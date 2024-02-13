import random
from datetime import datetime

import ujson
from sanic import response

from core.cache import cache
from core.db import db
from core.encoder import encoder
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class TestingsCompleteAPIView(BaseAPIView):
    async def get_question(self, question_id):
        return await db.fetchrow(
            '''
            SELECT *,
                   (SELECT array_agg(json_build_object('id', a.id, 'title', title, 'description', description)) AS answers
                    FROM testings.answers a
                    WHERE a.question_id = q.id)
            FROM testings.questions q
            WHERE q.id = $1
            ''',
            IntUtils.to_int(question_id)
        )

    async def end_testing(self, result_id):
        result = await db.fetchrow(
            '''
            WITH result AS (
                SELECT count(rs.is_currect) FILTER ( WHERE is_currect = 1 ) AS count
                FROM testings.response rs
                WHERE rs.result_id = $1
            )
            UPDATE testings.results rl
            SET currect  = result.count,
                wrong    = rl.total - result.count,
                status   = 2,
                ended_at = $2
            FROM result
            WHERE rl.id = $1
            RETURNING *
            ''',
            result_id,
            datetime.now()
        )

        if result:
            await cache.delete(f'testings:{result["user_id"]}:lobby:{result["lesson_id"]}')
            await cache.delete(f'testings:{result["user_id"]}:lobby:{result["lesson_id"]}:result_id')

        return result

    async def post(self, request, user, lesson_id):
        lesson_id = IntUtils.to_int(lesson_id)
        if not lesson_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): lesson_id'
            })

        action = StrUtils.to_str(request.json.get('action'), default='check_to_start')

        if action == 'check_to_start':
            lesson = await db.fetchrow(
                '''
                SELECT *
                FROM public.lessons
                WHERE id = $1
                ''',
                lesson_id
            )
            if not lesson:
                return response.json({
                    '_success': False,
                    'is_error': True,
                    'message': 'В системе урок не найдены'
                })

            if lesson.get('testing_state') not in [1]:
                return response.json({
                    '_success': False,
                    'is_error': True,
                    'message': 'Тестирование ещё не активирована'
                })

            question_ids = await db.fetchval(
                '''
                SELECT array_agg(DISTINCT id)
                FROM testings.questions
                WHERE status >= 0 AND lesson_id = $1
                ''',
                lesson_id,
            ) or []

            if not question_ids:
                return response.json({
                    '_success': False,
                    'is_error': True,
                    'message': 'В системе вопросы не найдены'
                })

            question_ids = await cache.get(f'testings:{user["id"]}:lobby:{lesson_id}')
            if question_ids:
                return response.json({
                    'continue': True,
                    '_success': True
                })
            else:
                count_result = await db.fetchval(
                    '''
                    SELECT count(id)
                    FROM testings.results
                    WHERE lesson_id = $1 AND user_id = $2 AND status >= 0
                    ''',
                    lesson_id,
                    user['id'],
                )

                if count_result and (lesson.get('testing_count') or 0) <= count_result:
                    return response.json({
                        '_success': False,
                        'is_info': True,
                        'message': 'Количества попыток ограничена'
                    })

                return response.json({
                    '_success': True
                })

        if action in ['start']:
            question_ids = await cache.get(f'testings:{user["id"]}:lobby:{lesson_id}')
            if question_ids:
                return response.json({
                    '_success': False,
                    'is_info': True,
                    'message': 'У вас есть активный сессия. Для продолжение нажмите на кнопку'
                })

            question_ids = await db.fetchval(
                '''
                SELECT array_agg(DISTINCT id)
                FROM testings.questions
                WHERE status >= 0 AND lesson_id = $1
                ''',
                lesson_id,
            ) or []

            question_ids = random.sample(question_ids, len(question_ids))
            await cache.set(f'testings:{user["id"]}:lobby:{lesson_id}', ujson.dumps(question_ids))

            result = await db.fetchrow(
                '''
                INSERT INTO testings.results(total, user_id, lesson_id)
                VALUES ($1, $2, $3)
                RETURNING *
                ''',
                len(question_ids),
                user['id'],
                lesson_id,
            )
            await cache.set(f'testings:{user["id"]}:lobby:{lesson_id}:result_id', result['id'])

            action = 'get_next'

        if action in ['continue', 'get_next']:
            question_ids = await cache.get(f'testings:{user["id"]}:lobby:{lesson_id}')
            if question_ids:
                question_ids = ujson.loads(question_ids)

            result_id = IntUtils.to_int(await cache.get(f'testings:{user["id"]}:lobby:{lesson_id}:result_id'))
            if question_ids:
                question = await self.get_question(question_ids[0])
                await cache.set(f'testings:{user["id"]}:lobby', ujson.dumps(question_ids))

                return response.json({
                    '_success': True,
                    'last': True if len(question_ids) == 1 else False,
                    'question': dict(question)
                }, dumps=encoder.encode)

            else:
                result = await self.end_testing(result_id)
                return response.json({
                    '_success': False,
                    'result': dict(result or {}),
                    'end': True
                }, dumps=encoder.encode)

        if action in ['end']:
            result_id = IntUtils.to_int(await cache.get(f'testings:{user["id"]}:lobby:{lesson_id}:result_id'))
            if result_id:
                await self.end_testing(result_id)

        if action in ['check_question']:
            question_id = IntUtils.to_int(request.json.get('question_id'))
            answer_id = IntUtils.to_int(request.json.get('answer_id'))

            if not question_id:
                return response.json({
                    '_success': False,
                    'is_error': True,
                    'message': 'Required param(s): question_id'
                })

            if not answer_id:
                return response.json({
                    '_success': False,
                    'is_error': True,
                    'message': 'Required param(s): answer_id'
                })

            flag = await db.fetchval(
                '''
                SELECT (CASE WHEN a.is_currect = 1 THEN TRUE ELSE FALSE END)
                FROM testings.answers a
                WHERE a.id = $1
                ''',
                answer_id
            )

            if flag is None:
                return response.json({
                    '_success': False,
                    'is_error': True,
                    'message': 'Operation failed'
                })

            question_ids = await cache.get(f'testings:{user["id"]}:lobby:{lesson_id}')
            result_id = IntUtils.to_int(await cache.get(f'testings:{user["id"]}:lobby:{lesson_id}:result_id'))
            if question_ids and result_id:
                question_ids = ujson.loads(question_ids)
                question_ids.remove(question_id) if question_id in question_ids else None

                await cache.set(f'testings:{user["id"]}:lobby:{lesson_id}', ujson.dumps(question_ids))

            else:
                return response.json({
                    '_success': False,
                    'is_error': True,
                    'message': 'Operation failed'
                })

            resp = await db.fetchrow(
                '''
                INSERT INTO testings.response(question_id, answer_id, is_currect, user_id, result_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                ''',
                question_id,
                answer_id,
                1 if flag else 0,
                user['id'],
                result_id
            )

            return response.json({
                '_success': True,
                'response': dict(resp)
            }, dumps=encoder.encode)

        return response.json({
            '_success': True,
        })
