from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class OrganizationsFieldsView(BaseAPIView):
    template_name = 'admin/organizations-fields.html'

    async def get(self, request, user):

        fields = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.organization_fields
            WHERE status >= 0
            ORDER BY id DESC
            '''
        ))

        return self.success(request, user, data={
            'fields': fields
        })

    async def post(self, request, user):
        field_id = StrUtils.to_str(request.json.get('field_id'))
        title = StrUtils.to_str(request.json.get('title'))

        if field_id == 'create':
            insert = await db.fetchrow(
                '''
                INSERT INTO public.organization_fields(title)
                VALUES ($1)
                RETURNING *
                ''',
                title,
            )
            if not insert:
                return self.error(message='Operation failed')

            return self.success()

        field_id = IntUtils.to_int(field_id)
        if not field_id:
            return self.error(message='Required param: field_id')

        update = await db.fetchrow(
            '''
            UPDATE public.organization_fields
            SET title = $2
            WHERE id = $1
            RETURNING *
            ''',
            field_id,
            title,
        )

        if not update:
            return self.error(message='Operation failed')

        return self.success()

    async def delete(self, request, user):
        field_id = IntUtils.to_int(request.json.get('field_id'))
        if not field_id:
            return self.error(message='Required param: field_id')

        update = await db.fetchrow(
            '''
            UPDATE public.organization_fields
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            field_id,
        )

        if not update:
            return self.error(message='Operation failed')

        return self.success()
