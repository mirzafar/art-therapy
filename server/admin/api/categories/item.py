from sanic import response

from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class CategoriesItemView(BaseAPIView):
    template_name = 'admin/categories_item.html'

    async def get(self, request, user, category_id):
        return self.render_template(
            request=request,
            user=user
        )

    async def post(self, request, user, category_id):
        title = StrUtils.to_str(request.json.get('title'))
        description = StrUtils.to_str(request.json.get('description'))
        parent_id = IntUtils.to_int(request.json.get('parent_id'))

        if category_id == 'new':
            data = await db.fetchrow(
                '''
                INSERT INTO public.categories(title, description, parent_id)
                VALUES ($1, $2, $3)
                RETURNING *
                ''',
                title,
                description,
                parent_id
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

        category_id = IntUtils.to_int(category_id)
        if not category_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): category_id'
            })

        data = await db.fetchrow(
            '''
            UPDATE public.categories
            SET title = $2, description = $3, parent_id = $4
            WHERE id = $1
            RETURNING *
            ''',
            category_id,
            title,
            description,
            parent_id,
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

    async def delete(self, request, user, category_id):
        category_id = IntUtils.to_int(category_id)
        if not category_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): category_id'
            })

        data = await db.fetchrow(
            '''
            UPDATE public.categories
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            category_id,
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
