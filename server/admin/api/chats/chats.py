from sanic import response

from core.db import mongo, db
from core.encoder import encoder
from core.handlers import BaseAPIView


class ChatsTemplateView(BaseAPIView):
    template_name = 'admin/chats.html'

    async def get(self, request, user):
        return self.render_template(request, user)


class ChatsAPIView(BaseAPIView):
    async def get(self, request, user):
        filter_obj = {
            '$and': [
                {
                    'user_ids': {
                        '$all': [user['id']]
                    }

                },
                {
                    'user_ids': {
                        '$ne': [user['id'], user['id']]
                    }
                },
            ]
        }

        chats = await mongo.chats.find(filter_obj, sort=[('updated_at', -1)]).to_list(length=None)

        data = []
        for chat in chats:
            user = await db.fetchrow(
                '''
                SELECT *
                FROM public.users
                WHERE id = $1
                ''',
                list(set(chat['user_ids']) - set([user['id']]))[0]
            )
            chat['chat_id'] = chat.pop('_id', None)
            chat.update(dict(user or {}))
            data.append(chat)

        return response.json({
            '_success': True,
            'chats': chats
        }, dumps=encoder.encode)
