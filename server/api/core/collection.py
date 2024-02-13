import string
import sys

from bson import ObjectId
from pydantic import ValidationError as valid_error
from sanic import response
from sanic.views import HTTPMethodView

from utils.strs import StrUtils
from api.core.models import *


def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)


class CollectionView(HTTPMethodView):
    async def get(self, request):
        return response.json({
            '_success': True
        })

    async def post(self, request, collection_name, action):
        collection_name = StrUtils.to_str(collection_name)
        action = StrUtils.to_str(action)
        payload = request.json

        if not payload:
            return response.json({
                '_success': False,
                'message': 'Missing options'
            })

        if action == 'new':
            invalid_fields = ['_id', 'status', 'undefined']

            item = {k: v for k, v in payload.items() if k and k not in invalid_fields}
            try:
                item = str_to_class(string.capwords(collection_name, sep=None))(**item)
                await mongo[collection_name].insert_one({
                    'status': 0,
                    'created_at': datetime.now(),
                    **item.dict()
                })

            except (valid_error,) as er:
                return response.json({
                    '_success': False,
                    'message': ', '.join([f'{[i for i in x.get("loc")]}: {x.get("msg")}' for x in er.errors()])
                })

            return response.json({
                '_success': True,
                'message': 'Added successfully'
            })

        _id = ObjectId(action)
        if not ObjectId.is_valid(_id):
            return response.json({
                '_success': False,
                'message': 'Invalid param(s): id'
            })

        if payload.get('status') == -1:
            await mongo[collection_name].update_one({'_id': _id}, {'$set': {
                'status': -1,
                'deleted_at': datetime.now()}
            })

            return response.json({
                '_success': True,
                'message': 'Deleted successfully'
            })

        for x in ['undefined', '_id']:
            if x in payload:
                del payload[x]

        try:
            item = str_to_class(string.capwords(collection_name, sep=None))(**payload)
            await mongo[collection_name].update_one({'_id': _id}, {'$set': {
                'updated_at': datetime.now(),
                **item.dict(exclude_none=True)
            }})
            return response.json({
                '_success': True,
                'message': 'Updated successfully'
            })

        except (valid_error,) as e:
            return response.json({
                '_success': False,
                'message': ', '.join([f'{[i for i in x.get("loc")]}: {x.get("msg")}' for x in e.errors()])
            })
