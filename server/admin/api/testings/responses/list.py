from sanic import response

from core.db import db
from core.encoder import encoder
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils


class TestingsResponsesAPIView(BaseAPIView):

    async def get(self, request, user, result_id):
        result_id = IntUtils.to_int(result_id)
        if not result_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): result_id'
            })

        data = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM testings.response r
            WHERE r.result_id = $1
            ''',
            result_id
        ))
        return response.json({
            '_success': True,
            'data': data
        }, dumps=encoder.encode)
