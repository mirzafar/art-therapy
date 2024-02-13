from sanic import response

from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils


class LessonsInfoTemplateView(BaseAPIView):
    template_name = 'admin/lesson-info.html'

    async def get(self, request, user, lesson_id):
        lesson_id = IntUtils.to_int(lesson_id)
        if not lesson_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): lesson_id'
            })

        lesson = await db.fetchrow(
            '''
            SELECT 
                l.*, 
                c.title AS category_title,
                (
                    SELECT array_agg(tags.title) 
                    FROM public.tags
                    WHERE id = ANY(l.tag_ids)
                ) AS tags,
                $2 = ANY (subscribers) AS is_subscribe
            FROM public.lessons l
            LEFT JOIN categories c on c.id = l.category_id
            WHERE l.id = $1
            ''',
            lesson_id,
            user['id'],
        )

        lesson = dict(lesson or {})

        if lesson.get('discount') and 1 < lesson['discount'] < 100 and lesson.get('price'):
            lesson['price'] = lesson['price'] * 100 / (100 - lesson['discount'])

        self.context = {
            'lesson': lesson
        }

        return self.render_template(
            request=request,
            user=user
        )
