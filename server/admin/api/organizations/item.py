from core.db import db
from core.handlers import BaseAPIView
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils


class OrganizationsItemView(BaseAPIView):
    template_name = 'admin/organizations-item.html'

    async def get(self, request, user, item_id):
        organization, organization_items = {}, []
        if item_id == 'create':
            organization_items = ListUtils.to_list_of_dicts(await db.fetch(
                '''
                SELECT id, title
                FROM public.organization_fields
                WHERE status >= 0
                '''
            ))
        elif IntUtils.to_int(item_id):
            organization_items = ListUtils.to_list_of_dicts(await db.fetch(
                '''
                SELECT of.id, of.title, coalesce(oi.value, '') AS value
                FROM public.organization_fields of
                LEFT JOIN public.organization_items oi ON oi.field_id = of.id AND oi.organization_id = $1
                WHERE of.status >= 0
                ''',
                IntUtils.to_int(item_id)
            ))

            organization = await db.fetchrow(
                '''
                SELECT *
                FROM public.organization
                WHERE id = $1
                ''',
                IntUtils.to_int(item_id)
            )

        return self.success(request, user, data={
            'organization': organization,
            'organization_items': organization_items,
        })

    async def post(self, request, user, item_id):
        title = request.json.get('title')
        photo = request.json.get('photo', '')
        fields = request.json.get('fields') or {}

        if item_id == 'create':
            if not title:
                return self.error(message='Required param: title')

            organization = await db.fetchrow(
                '''
                INSERT INTO public.organization(title, photo)
                VALUES ($1, $2)
                RETURNING *
                ''',
                title,
                photo
            )

            if not organization:
                return self.error(message='Operation failed')

            if fields:
                cond_vars, setters = [], []
                for k, v in fields.items():
                    k = IntUtils.to_int(k)
                    if k:
                        setters.append('({}, {}, {})')
                        cond_vars.extend([organization['id'], k, v])

                if cond_vars:
                    status_counters, _ = set_counters(', '.join(setters))
                    organization_items = await db.fetch(
                        '''
                        INSERT INTO public.organization_items(organization_id, field_id, value)
                        VALUES %s
                        RETURNING *
                        ''' % status_counters,
                        *cond_vars
                    )

                    if not organization_items:
                        return self.error(message='Operation failed')

            return self.success()

        item_id = IntUtils.to_int(item_id)
        if not item_id:
            return self.error(message='Required param: item_id')

        organization = await db.fetchrow(
            '''
            UPDATE public.organization
            SET title = $2, photo = $3
            WHERE id = $1
            RETURNING *
            ''',
            item_id,
            title,
            photo,
        )

        if not organization:
            return self.error(message='Operation failed')

        if fields:
            cond_vars, setters = [], []
            for k, v in fields.items():
                k = IntUtils.to_int(k)
                if k:
                    setters.append('({}, {}, {})')
                    cond_vars.extend([organization['id'], k, v])
                    update = await db.fetchrow(
                        '''
                        UPDATE public.organization_items
                        SET value = $3
                        WHERE organization_id = $1 AND field_id = $2
                        RETURNING *
                        ''',
                        item_id,
                        k,
                        v
                    )

                    if not update:
                        await db.execute(
                            '''
                            INSERT INTO public.organization_items(organization_id, field_id, value)
                            VALUES ($1, $2, $3)
                            RETURNING *
                            ''',
                            item_id,
                            k,
                            v
                        )

        return self.success()

    async def delete(self, request, user, item_id):
        item_id = IntUtils.to_int(item_id)
        if not item_id:
            return self.error(message='Required param: item_id')

        organization = await db.fetchrow(
            '''
            UPDATE public.organization
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            item_id,
        )

        if not organization:
            return self.error(message='Operation failed')

        return self.success()
