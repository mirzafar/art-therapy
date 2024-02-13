from sanic import response

from core.db import db
from core.encoder import encoder
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils


class TestingsResultsItemTemplateView(BaseAPIView):
    template_name = 'admin/results-item.html'

    async def get(self, request, user, result_id):
        return self.render_template(request, user)


class TestingsResultslistTemplateView(BaseAPIView):

    async def get(self, request, user, result_id):
        result_id = IntUtils.to_int(result_id)
        if not result_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): result_id'
            })

        data = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                *,
                (
                    SELECT 
                        array_agg(
                            json_build_object(
                            'title', q.title,
                            'description', q.description,
                            'photo', q.photo,
                            'audio', q.audio,
                            'video_link', q.video_link,
                            'current_answer_id', q.current_answer_id,
                            'answers', (
                                SELECT array_agg(
                                    json_build_object(
                                        'title', a.title,
                                        'description', a.description,
                                        'is_currect', a.is_currect
                                        )
                                    )
                                FROM testings.answers a
                                WHERE a.question_id = q.id
                                )
                            )
                        )
                    FROM testings.questions q
                    WHERE q.id = r.question_id
                ) AS questions
            FROM testings.response r
            WHERE r.result_id = $1
            ''',
            result_id
        ))
        return response.json({
            '_success': True,
            'data': data
        }, dumps=encoder.encode)
