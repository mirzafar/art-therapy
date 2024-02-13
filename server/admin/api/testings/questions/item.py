from sanic import response

from core.db import db
from core.encoder import encoder
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class TestingsQuestionsItemAPIView(BaseAPIView):
    async def get(self, request, user, question_id):
        question_id = IntUtils.to_int(question_id)
        if not question_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): question_id'
            })

        question = await db.fetchrow(
            '''
            SELECT
                q.*,
                (
                    SELECT array_agg(
                        json_build_object(
                            'id', a.id,
                            'title', a.title,
                            'is_currect', a.is_currect
                        )
                    )
                    FROM testings.answers a
                    WHERE a.question_id = q.id
                ) AS answers
            FROM testings.questions q
            WHERE q.id = $1
            ''',
            question_id
        )

        return response.json({
            '_success': True,
            'question': dict(question)
        }, dumps=encoder.encode)

    async def post(self, request, user, question_id):
        question_id = IntUtils.to_int(question_id)
        if not question_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): question_id'
            })

        access = await db.fetchval(
            '''
            SELECT l.testing_state 
            FROM testings.questions q
            LEFT JOIN public.lessons l ON q.lesson_id = l.id
            WHERE q.id = $1
            ''',
            question_id
        )
        if access is None:
            return response.json({
                '_success': False,
                'message': 'Урок не найден'
            })

        if access == 1:
            return response.json({
                '_success': False,
                'message': 'Доступ отказан. Урок уже активирован'
            })

        title = StrUtils.to_str(request.json.get('title'))
        description = StrUtils.to_str(request.json.get('description'))
        photo = StrUtils.to_str(request.json.get('photo'))
        audio = StrUtils.to_str(request.json.get('audio'))
        video_link = StrUtils.to_str(request.json.get('video_link'))
        current_answer_id = IntUtils.to_int(request.json.get('current_answer_id'))

        if not title:
            return response.json({
                '_success': False,
                'message': 'Required param(s): title'
            })

        question = await db.fetchrow(
            '''
            UPDATE testings.questions
            SET title = $2, description = $3, video_link = $4, audio = $5, photo = $6, current_answer_id = $7
            WHERE id = $1
            RETURNING *
            ''',
            question_id,
            title,
            description,
            video_link,
            audio,
            photo,
            current_answer_id,
        )

        if not question:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        return response.json({
            '_success': True,
            'question': dict(question)
        }, dumps=encoder.encode)

    async def delete(self, request, user, question_id):
        question_id = IntUtils.to_int(question_id)
        if not question_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): question_id'
            })

        question = await db.fetchrow(
            '''
            UPDATE testings.questions
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            question_id
        )

        if not question:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        return response.json({
            '_success': True,
            'question': dict(question)
        }, dumps=encoder.encode)
