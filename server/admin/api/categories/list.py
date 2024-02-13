from core.db import db
from core.handlers import BaseAPIView
from utils.lists import ListUtils


class CategoriesView(BaseAPIView):
    template_name = 'admin/categories.html'

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

        total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.categories c
            LEFT JOIN public.categories p ON c.parent_id = p.id 
            WHERE c.status >= 0
            '''
        ) or 0

        self.context['data'] = {
            'categories': categories,
            'total': total
        }

        return self.render_template(
            request=request,
            user=user
        )
