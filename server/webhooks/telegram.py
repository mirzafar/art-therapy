import random

import ujson
from pymystem3 import Mystem
from sanic import response
from sanic.views import HTTPMethodView

from clients.telegram import tgclient
from core.cache import cache
from core.db import db
from settings import settings
from utils.dicts import DictUtils
from utils.lists import ListUtils
from utils.strs import StrUtils

RISK_WORDS = [
    ['суицид'], ['самоубийства'], ['жизненный', 'ситуация'], ['плохой', 'аппетит']
]

m = Mystem()


class TelegramWebhookHandler(HTTPMethodView):
    @classmethod
    async def generate_questions(cls, customer_id):
        items = await db.fetch(
            '''
            SELECT c.id, count(*) AS count_questions, array_agg(q.id) AS question_ids, c.attempt
            FROM public.questions q
            LEFT JOIN public.categories c on c.id = q.category_id
            GROUP BY c.id
            '''
        )
        question_ids = []
        for item in items:
            if item.get('count_questions') > item.get('attempt'):
                question_ids.extend(random.sample(item['question_ids'], item.get('attempt')) or [])

        questions = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.questions
            WHERE id = ANY($1)
            ORDER BY position
            ''',
            question_ids
        )) or []

        await cache.set(f'art:telegram:questions:{customer_id}', ujson.dumps(questions))

        return questions

    @classmethod
    async def finalize(cls, customer_id):
        await cache.delete(f'art:question:name:{customer_id}')
        await cache.delete(f'art:telegram:items:{customer_id}')
        await cache.delete(f'art:telegram:prev_question:{customer_id}')

    async def get(self, request):
        return response.json({})

    async def post(self, request):
        data = request.json

        print(f'[post] data: {data}')

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
                sender.get('first_name'),
                sender.get('username'),
                chat_id
            )

        if message and message.get('text') == '/start':
            await self.finalize(customer['id'])
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': 'Привет! Меня зовут TulparIfy. '
                            'Я здесь, чтобы помочь тебе с помощью арт-терапии через музыку.\n'
                            'Как тебя зовут?'
                }
            )

            await cache.set(f'art:question:name:{customer["id"]}', '1')

            return response.json({})

        text = None
        success = False
        questions = None
        if message and message.get('text'):
            text = message['text']

        if callback_query and callback_query.get('data'):
            text = callback_query['data']

        if text and text.startswith('🔄'):
            await self.finalize(customer['id'])
            questions = await self.generate_questions(customer['id'])

        if await cache.get(f'art:question:name:{customer["id"]}'):
            await cache.delete(f'art:question:name:{customer["id"]}')
            questions = await self.generate_questions(customer['id'])

            await db.execute(
                '''
                UPDATE public.customers
                SET name = $2
                WHERE id = $1
                ''',
                customer['id'],
                text
            )

        if not questions:
            questions = await cache.get(f'art:telegram:questions:{customer["id"]}')
            if questions:
                questions = ujson.loads(questions)

        if text:
            success, method = True, 'sendMessage'
            while success:
                prev_question = await cache.get(f'art:telegram:prev_question:{customer["id"]}')

                if not questions:
                    success = False
                    continue
                elif questions:
                    pass
                elif not prev_question:
                    success = False
                    continue

                question, genre = None, None
                if prev_question:
                    prev_question = ujson.loads(prev_question)
                    if prev_question['buttons']:
                        question = prev_question
                        for x in prev_question['buttons']:
                            if text == x['text']:
                                question = None
                                genre = x['callback_data']

                    lemmas = m.lemmatize(text)
                    risk_words = RISK_WORDS + (prev_question.get('details') or {}).get('risk_words', [])

                    for x in risk_words:
                        if len(list(set(x) & set(lemmas))) == len(x):
                            await tgclient.api_call(
                                payload={
                                    'chat_id': chat_id,
                                    'text': 'Рекомендую обратиться к профессиональному психологу или психотерапевту,'
                                            ' если это беспокоит длительное время. Арт-терапия может быть эффективным '
                                            'дополнением к другим методам лечения депрессии, таким как медикаментозная '
                                            'терапия и психотерапия',
                                    'reply_markup': {
                                        'keyboard': [
                                            [{
                                                'text': '🔄 Пройти заново',
                                            }]
                                        ],
                                        'one_time_keyboard': True,
                                        'resize_keyboard': True
                                    }
                                }
                            )

                if not question:
                    question = questions.pop(0) if questions else {}

                payload = {'chat_id': chat_id}

                if question:
                    if question.get('media'):
                        payload['audio'] = question['media']['url']
                        payload['caption'] = question['text']
                        method = 'sendAudio'

                    elif question.get('details') and question['details'].get('action') == 'get_tunes':
                        tunes = await db.fetch(
                            '''
                            SELECT *
                            FROM public.tunes
                            WHERE genre = $1
                            ''',
                            genre
                        )
                        if tunes:
                            for tune in tunes:
                                await tgclient.api_call(
                                    method_name='sendAudio',
                                    payload={
                                        'chat_id': chat_id,
                                        'title': tune['title'],
                                        'audio': settings['base_url'] + '/static/uploads/' + tune['path'],
                                    }
                                )
                        payload['text'] = question['text']
                    else:
                        payload['text'] = question['text']

                else:
                    payload['text'] = 'Приятно было с вами общаться!\nСпасибо за то, что воспользовались ботом!'
                    await self.finalize(customer['id'])

                if question and question['buttons']:
                    payload.update({
                        'reply_markup': {
                            'keyboard': [
                                [{
                                    'text': button['text'],
                                    # 'callback_data': button['callback_data']
                                }] for button in question['buttons']
                            ],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    })
                else:
                    payload.update({
                        'reply_markup': {
                            'keyboard': [
                                [{
                                    'text': '🔄 Пройти заново',
                                }]
                            ],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    })

                await cache.set(f'art:telegram:prev_question:{customer["id"]}', ujson.dumps(question))
                await cache.set(f'art:telegram:questions:{customer["id"]}', ujson.dumps(questions))
                await tgclient.api_call(method_name=method, payload=payload)
                break

        if success is False:
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': 'В системе ничего не найдено',
                }
            )

        return response.json({})
