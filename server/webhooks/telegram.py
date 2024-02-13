from pprint import pprint

import ujson
from sanic import response
from sanic.views import HTTPMethodView

from clients.telegram import tgclient
from core.cache import cache
from core.db import db
from utils.dicts import DictUtils
from utils.ints import IntUtils
from utils.strs import StrUtils


class TelegramWebhookHandler(HTTPMethodView):
    async def get(self, request):
        return response.json({})

    async def post(self, request):
        data = request.json

        print(f'telegram_message: {data}')

        message = DictUtils.as_dict(data.get('message'))
        callback_query = DictUtils.as_dict(data.get('callback_query'))

        if message:
            chat_id = StrUtils.to_str(message.get('chat', {}).get('id'))
            sender = message.get('from', {})
            customer = await db.fetchrow(
                '''
                SELECT id, username
                FROM public.customers
                WHERE uid = $1
                ''',
                chat_id
            )
        elif callback_query:
            chat_id = StrUtils.to_str(callback_query.get('message', {}).get('chat', {}).get('id'))
            sender = callback_query.get('from', {})
            customer = await db.fetchrow(
                '''
                SELECT id, username
                FROM public.customers
                WHERE uid = $1
                ''',
                chat_id
            )
        else:
            return response.json({})

        if not customer:
            customer = await db.fetchrow(
                '''
                INSERT INTO public.customers(name, username, uid)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING
                RETURNING id, username
                ''',
                sender['first_name'],
                sender['username'],
                chat_id
            )

        if message and message.get('text') == '/start':
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': '''
                    Привет! Меня зовут [имя бота]. Я здесь, чтобы помочь тебе с помощью арт-терапии через музыку.
                    Как тебя зовут?
                    '''
                }
            )

            await cache.set(f'art:question:name:{customer["id"]}', '1')

            return response.json({})

        text = None
        success = False
        if message and message.get('text'):
            text = message['text']

        if callback_query and callback_query.get('data'):
            text = callback_query['data']

        if text:
            success = True
            position = IntUtils.to_int(await cache.get(f'art:question:position:{customer["id"]}')) or 1
            data = await cache.get(f'art:question:data:{customer["id"]}') or {}
            if data:
                data = ujson.loads(data)

            if await cache.get(f'art:question:name:{customer["id"]}'):
                await cache.delete(f'art:question:name:{customer["id"]}')

                await db.execute(
                    '''
                    UPDATE public.customers
                    SET name = $2
                    WHERE id = $1
                    ''',
                    customer['id'],
                    text
                )
            else:
                if str((position - 1)) in data:
                    data[str(position - 1)]['answer'] = text

            question = await db.fetchrow(
                '''
                SELECT *
                FROM public.questions
                WHERE position = $1
                ''',
                position
            ) or {}

            if not question:
                await tgclient.api_call(
                    payload={
                        'chat_id': chat_id,
                        'text': '''
                        Приятно было с вами общаться!
                        Спасибо за то, что воспользовались ботом!
                        '''
                    }
                )
                print('---> end')
                pprint(data)

                await cache.delete(f'art:question:position:{customer["id"]}')
                await cache.delete(f'art:question:data:{customer["id"]}')

                return response.json({})

            data[position] = {
                'question': question['text'],
                'answer': None
            }

            payload = {
                'chat_id': chat_id,
                'text': question['text']
            }

            if question['buttons']:
                payload.update({
                    'reply_markup': {
                        'keyboard': [
                            [{
                                'text': button['text'],
                                # 'callback_data': button['callback_data']
                            }] for button in question['buttons']
                        ],
                        'remove_keyboard': True
                    }
                })

            await tgclient.api_call(payload=payload)

            await cache.set(f'art:question:position:{customer["id"]}', position + 1)
            await cache.set(f'art:question:data:{customer["id"]}', ujson.dumps(data))

        if success is False:
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': 'В системе ничего не найдено',
                }
            )

        return response.json({})
