from sanic import response

from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class RolesItemView(BaseAPIView):
    template_name = 'adminn/category_item.html'

    async def get(self, request, user, category_id):
        self.context['data'] = dict(await db.fetchrow(
            '''
            SELECT *
            FROM public.categories
            WHERE id = $1
            ''',
            category_id
        ) or {})

        return self.render_template(
            request=request,
            user=user
        )

    async def post(self, request, user, role_id):
        title = StrUtils.to_str(request.json.get('title'))
        description = StrUtils.to_str(request.json.get('description'))
        permissions = ListUtils.to_list_of_strs(request.json.get('permissions'))

        if role_id == 'new':
            data = await db.fetchrow(
                '''
                INSERT INTO public.roles(title, description, permissions)
                VALUES ($1, $2, $3)
                RETURNING *
                ''',
                title,
                description,
                permissions,
            )

            if data:
                return response.json({
                    '_success': True,
                    'data': dict(data)
                })

            else:
                return response.json({
                    '_success': False,
                    'message': 'Operation failed'
                })

        role_id = IntUtils.to_int(role_id)
        if not role_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): category_id'
            })

        data = await db.fetchrow(
            '''
            UPDATE public.roles
            SET title = $2, description = $3, permissions = $4
            WHERE id = $1
            RETURNING *
            ''',
            role_id,
            title,
            description,
            permissions,
        )

        if not data:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        return response.json({
            '_success': True,
            'data': dict(data)
        })

    async def delete(self, request, user, role_id):
        role_id = IntUtils.to_int(role_id)
        if not role_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): category_id'
            })

        data = await db.fetchrow(
            '''
            UPDATE public.roles
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            role_id,
        )

        if not data:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        return response.json({
            '_success': True,
            'data': dict(data)
        })
