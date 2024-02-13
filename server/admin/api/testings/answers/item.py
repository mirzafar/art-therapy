from sanic import response

from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class TestingsAnswersItemAPIView(BaseAPIView):
    async def post(self, request, user, answer_id):
        answer_id = IntUtils.to_int(answer_id)
        if not answer_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): answer_id'
            })

        access = await db.fetchval(
            '''
            SELECT l.testing_state 
            FROM testings.questions q
            LEFT JOIN public.lessons l ON q.lesson_id = l.id
            LEFT JOIN testings.answers a ON q.id = a.question_id
            WHERE a.id = $1
            ''',
            answer_id
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
        if not title:
            return response.json({
                '_success': False,
                'message': 'Required param(s): title'
            })

        answer = await db.fetchrow(
            '''
            UPDATE testings.answers
            SET title = $2, is_currect = $3
            WHERE id = $1
            RETURNING *
            ''',
            answer_id,
            title,
            IntUtils.to_int(request.json.get('is_currect')) or 0
        )

        if not answer:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        if answer['is_currect']:
            await db.fetchrow(
                '''
                UPDATE testings.answers
                SET is_currect = 0
                WHERE id <> $1 AND question_id = $2
                RETURNING *
                ''',
                answer['id'],
                answer['question_id']
            )

        return response.json({
            '_success': True,
            'answer': dict(answer)
        })

    async def delete(self, request, user, answer_id):
        answer_id = IntUtils.to_int(answer_id)
        if not answer_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): answer_id'
            })

        answer = await db.fetchrow(
            '''
            UPDATE testings.answers
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            answer_id,
        )

        if not answer:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        return response.json({
            '_success': True,
            'answer': dict(answer)
        })
