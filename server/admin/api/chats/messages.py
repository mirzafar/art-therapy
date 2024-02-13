from datetime import datetime

from bson import ObjectId
from sanic import response

from core.db import mongo
from core.encoder import encoder
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class ChatsMessagesAPIView(BaseAPIView):

    async def get(self, request, user):
        chat_id = StrUtils.to_str(request.args.get('chat_id'))
        recipient_id = IntUtils.to_int(request.args.get('recipient_id'))
        if chat_id:
            filter_obj = {
                'chat_id': chat_id
            }

        elif recipient_id:
            chat = await mongo.chats.find_one({
                '$or': [
                    {
                        'user_ids': [recipient_id, user['id']]
                    },
                    {
                        'user_ids': [user['id'], recipient_id]
                    }
                ]

            })
            if chat:
                filter_obj = {
                    'chat_id': str(chat['_id'])
                }
            else:
                chat = await mongo.chats.insert_one({'user_ids': [recipient_id, user['id']]})

                filter_obj = {
                    'chat_id': str(chat.inserted_id)
                }

        else:
            return response.json({
                '_success': False,
                'message': 'Required param(s): chat_id'
            })

        messages = []
        if filter_obj:
            pipeline = [
                {
                    '$addFields': {
                        'is_me': {
                            '$cond': {
                                'if': {'$eq': ['$user_id', user['id']]},
                                'then': True,
                                'else': False
                            }
                        }
                    }
                },
                {
                    '$match': filter_obj
                }
            ]

            messages = await mongo.messages.aggregate(pipeline).to_list(length=None) or []

        return response.json({
            '_success': True,
            'messages': messages,
            'user': dict(user),
        }, dumps=encoder.encode)

    async def save_message(self, chat_id, body, user_id):
        if not chat_id or not body:
            return {
                '_success': False
            }

        data = {
            'chat_id': str(chat_id),
            'body': body,
            'user_id': user_id,
            'created_at': datetime.now()
        }
        await mongo.messages.insert_one(data)

        data['_success'] = True
        data['is_me'] = True

        return data

    async def post(self, request, user):
        action = StrUtils.to_str(request.json.get('action'))
        body = StrUtils.to_str(request.json.get('body'))
        if not body:
            return response.json({
                '_success': False,
                'message': 'Required param(s): body'
            })

        if action == 'create_chat_and_send':
            recipient_id = IntUtils.to_int(request.json.get('recipient_id'))

            if not recipient_id:
                return response.json({
                    '_success': False,
                    'message': 'Required param(s): recipient_id'
                })

            chat = await mongo.chats.find_one_and_update(
                {'$or': [
                    {
                        'user_ids': [user['id'], recipient_id]
                    },
                    {
                        'user_ids': [recipient_id, user['id']]
                    }
                ]},
                {'$set': {
                    'user_ids': [user['id'], recipient_id],
                    'updated_at': datetime.now(),
                    'last_message': body
                }}, upsert=True, return_document=True)

            return response.json(await self.save_message(chat['_id'], body, user['id']), dumps=encoder.encode)

        elif action == 'send_message':
            chat_id = StrUtils.to_str(request.json.get('chat_id'))

            if not chat_id:
                return response.json({
                    '_success': False,
                    'message': 'Required param(s): chat_id'
                })

            await mongo.chats.find_one_and_update({'_id': ObjectId(chat_id)}, {'$set': {
                'updated_at': datetime.now(),
                'last_message': body
            }}, upsert=True)

            return response.json(await self.save_message(chat_id, user['id'], body), dumps=encoder.encode)

        return response.json({})
