from sanic import response

from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class TestingsAnswersAPIView(BaseAPIView):
    async def get(self, request, user, question_id):
        question_id = IntUtils.to_int(question_id)
        if not question_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): question_id'
            })

        lesson_id = await db.fetchval(
            '''
            SELECT l.id
            FROM testings.questions q
            LEFT JOIN public.lessons l ON q.lesson_id = l.id
            WHERE q.id = $1
            ''',
            question_id
        )

        answers = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT a.*
            FROM testings.answers a
            WHERE a.status >= 0 AND question_id = $1
            ORDER BY a.id DESC 
            ''',
            question_id
        ))

        return response.json({
            '_success': True,
            'answers': answers,
            'lesson_id': lesson_id,
        })

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
        if not title:
            return response.json({
                '_success': False,
                'message': 'Required param(s): title'
            })

        answer = await db.fetchrow(
            '''
            INSERT INTO testings.answers(title, question_id, is_currect)
            VALUES ($1, $2, $3)
            RETURNING *
            ''',
            title,
            question_id,
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
                question_id
            )

        return response.json({
            '_success': True,
            'answer': dict(answer)
        })
