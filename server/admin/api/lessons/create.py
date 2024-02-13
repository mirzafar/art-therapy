from core.db import db
from core.handlers import BaseAPIView
from utils.lists import ListUtils


class LessonsCreateView(BaseAPIView):
    template_name = 'admin/lessons-create.html'

    async def get(self, request, user):
        categories = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.categories
            WHERE status >= 0
            '''
        ))

        tags = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.tags
            WHERE status >= 0
            '''
        ))

        self.context = {
            'categories': categories,
            'tags': tags,
        }

        return self.render_template(
            request=request,
            user=user
        )
