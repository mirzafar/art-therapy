from sanic import response

from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class LessonsTagsView(BaseAPIView):
    template_name = 'admin/lessons-tags.html'

    async def get(self, request, user):
        categories = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT c.*, p.title parent_title
            FROM public.categories c
            LEFT JOIN public.categories p ON c.parent_id = p.id 
            WHERE c.status >= 0
            ORDER BY id DESC
            '''
        ))

        tags = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT t.*, c.title AS category_title
            FROM public.tags t
            LEFT JOIN public.categories c ON t.category_id = c.id
            WHERE t.status >= 0
            ORDER BY t.id DESC
            '''
        ))

        total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.tags
            WHERE status >= 0
            '''
        ) or 0

        self.context = {
            'tags': tags,
            'categories': categories,
            'total': total
        }

        return self.render_template(request, user)


class LessonsTagsItemView(BaseAPIView):

    async def post(self, request, user, tag_id):
        title = StrUtils.to_str(request.json.get('title'))
        description = StrUtils.to_str(request.json.get('description'))
        category_id = IntUtils.to_int(request.json.get('category_id'))

        if tag_id == 'new':
            data = await db.fetchrow(
                '''
                INSERT INTO public.tags(title, description, category_id)
                VALUES ($1, $2, $3)
                RETURNING *
                ''',
                title,
                description,
                category_id
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

        tag_id = IntUtils.to_int(tag_id)
        if not tag_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): tag_id'
            })

        data = await db.fetchrow(
            '''
            UPDATE public.tags
            SET title = $2, description = $3, category_id = $4
            WHERE id = $1
            RETURNING *
            ''',
            tag_id,
            title,
            description,
            category_id
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

    async def delete(self, request, user, tag_id):
        tag_id = IntUtils.to_int(tag_id)
        if not tag_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): tag_id'
            })

        data = await db.fetchrow(
            '''
            UPDATE public.tags
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            tag_id,
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
