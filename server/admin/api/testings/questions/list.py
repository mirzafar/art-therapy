from sanic import response

from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class TestingsQuestionsAPIView(BaseAPIView):
    async def get(self, request, user, lesson_id):
        lesson_id = IntUtils.to_int(lesson_id)
        if not lesson_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): lesson_id'
            })

        page = request.args.get('page', 1)
        limit = request.args.get('limit', 10)

        pager = Pager()
        pager.set_page(page)
        pager.set_limit(limit)

        questions = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM testings.questions
            WHERE status >= 0 AND lesson_id = $1
            ORDER BY id DESC
            %s
            ''' % pager.as_query(),
            lesson_id,
        ))

        pager.total = await db.fetchval(
            '''
            SELECT count(*)
            FROM testings.questions
            WHERE status >= 0 AND lesson_id = $1
            ''',
            lesson_id,
        ) or 0

        return response.json({
            '_success': True,
            'questions': questions,
            'pager': pager.dict(),
        })

    async def post(self, request, user, lesson_id):
        lesson_id = IntUtils.to_int(lesson_id)
        if not lesson_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): lesson_id'
            })

        access = await db.fetchval('SELECT testing_state FROM public.lessons WHERE id = $1', lesson_id)
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

        if not title:
            return response.json({
                '_success': False,
                'message': 'Required param(s): title'
            })

        question = await db.fetchrow(
            '''
            INSERT INTO testings.questions(title, lesson_id, description, photo, audio, video_link)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            ''',
            title,
            lesson_id,
            description,
            photo,
            audio,
            video_link
        )

        if not question:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        return response.json({
            '_success': True,
            'questions': dict(question)
        })
