import asyncio
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
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils

RISK_WORDS = [
    ['суицид'], ['самоубийства'], ['жизненный', 'ситуация'], ['плохой', 'аппетит'], ['плохо'], ['болеть'], ['уставать'],
    ['уставать'], ['ничто', 'не', 'хотеть'], ['плохо', 'спать'], ['бояться'], ['ужасно'], ['никто', 'не', 'любить'],
    ['тревога'], ['беспокойство'], ['депрессия'], ['апатия'], ['ничто', 'не', 'любить'],
    ['никто', 'не', 'хотеть', 'видеть'], ['грустно'], ['грусть'], ['тоска'], ['гнев'], ['вино'], ['одиноко'],
    ['страдать'], ['бояться'], ['ненавидеть'], ['бесполезео'], ['страх'], ['печаль'], ['безнадежность'],
    ['нет', 'смысл'], ['нет', 'цель'], ['мучиться'], ['недостойный'], ['виноватый'], ['тяжело'], ['невыносимый']
]

LOCALE_TUNES = [
    {'text': 'Классика', 'callback_data': 'classic'}, {'text': 'Джаз', 'callback_data': 'djazz'},
    {'text': 'Электронная музыка', 'callback_data': 'electronic'},
    {'text': 'Музыка для медитации', 'callback_data': 'meditation'},
    {'text': 'Звуки природы', 'callback_data': 'nature'}
]

m = Mystem()

HOME_BUTTON = [{
    'text': '🏠 Вернуться в меню',
}]  # Кнопка назад

MENU_BUTTONS = [
    [{
        'text': 'ℹ️ О боте',
    }],
    [{
        'text': '📃️ Справка',
    }],
    [{
        'text': '🎼 Генерация музыки',
    }],
    [{
        'text': '💬 Пообщаемся?',
    }],
    [{
        'text': '📁 Плейлист',
    }],
]  # Список меню


class TelegramWebhookHandler(HTTPMethodView):

    @classmethod
    async def send_rating(cls, customer_id, chat_id, text):
        success, genre = False, None
        for x in LOCALE_TUNES:
            if x.get('text') == text:
                success = True
                genre = x['callback_data']

        if not success:
            await cls.send_locale_tune(customer_id, chat_id)
            return

        await cache.setex(f'art:telegram:questions:rating:{customer_id}', 600, '1')
        wait_payloads = [{
            'method_name': 'sendMessage',
            'payload': {
                'chat_id': chat_id,
                'text': 'Вот несколько вариантов музыки, которая может тебе помочь расслабиться:',
            }
        }]

        tune = await db.fetchrow(
            '''
            SELECT *
            FROM public.tunes
            WHERE genre = $1
            ORDER BY random()
            ''',
            genre
        )

        if tune:
            wait_payloads.append({
                'method_name': 'sendAudio',
                'payload': {
                    'chat_id': chat_id,
                    'title': tune['title'],
                    'audio': settings['base_url'] + '/static/uploads/' + tune['path'],
                }
            })
            wait_payloads.append({
                'method_name': 'sendMessage',
                'payload': {
                    'chat_id': chat_id,
                    'text': 'Как вам эта музыка?',
                    'reply_markup': {
                        'keyboard': [[{'text': '🔎 Генерировать трек'}], HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            })

        for x in wait_payloads:
            await tgclient.api_call(method_name=x['method_name'], payload=x['payload'])

        return cls.finalize(customer_id)

    @classmethod
    async def send_locale_tune(cls, customer_id, chat_id):
        await tgclient.api_call(
            payload={
                'chat_id': chat_id,
                'text': 'Вот несколько вариантов музыки, которая может тебе помочь расслабиться:',
                'reply_markup': {
                    'keyboard': [[x] for x in LOCALE_TUNES + HOME_BUTTON],
                    'one_time_keyboard': True,
                    'resize_keyboard': True
                }
            }
        )

        return await cache.setex(f'art:telegram:locale_tune:{customer_id}', 600, 1)

    @classmethod
    async def generate_questions(cls, customer_id, _type):  # Генерация вопросов для общения и создания треков
        items = await db.fetch(
            '''
            SELECT c.id, count(*) AS count_questions, array_agg(q.id) AS question_ids, c.attempt
            FROM public.questions q
            LEFT JOIN public.categories c on c.id = q.category_id
            WHERE c.type = $1
            GROUP BY c.id
            ''',
            _type
        )
        question_ids = []
        for item in items:
            if item.get('count_questions') > item.get('attempt'):
                question_ids.extend(random.sample(item['question_ids'], item.get('attempt')) or [])
            else:
                question_ids.extend(item['question_ids'])

        questions = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.questions
            WHERE id = ANY($1)
            ORDER BY position, random()
            ''',
            question_ids
        )) or []

        await cache.setex(f'art:telegram:questions:{customer_id}', 600, ujson.dumps(questions))

        return questions

    @classmethod
    async def finalize(cls, customer_id):  # Завершить диалог
        keys = [
            f'art:telegram:questions:{customer_id}',
            f'art:question:name:{customer_id}',
            f'art:telegram:prev_question:{customer_id}',
            f'art:telegram:words:{customer_id}',
            f'art:telegram:audio:name:{customer_id}',
            f'art:telegram:questions:rating:{customer_id}',
            f'art:telegram:risk:{customer_id}',
            f'art:telegram:locale_tune:{customer_id}'
        ]
        return await cache.delete(*keys)

    @classmethod
    async def generate_turn(cls, customer_id, chat_id):  # Генерация треков
        words = await cache.lrange(f'art:telegram:words:{customer_id}', 0, -1)
        if words:
            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': '⏱️ идет генерация трека ...'
                }
            )

            await db.fetchrow(
                '''
                INSERT INTO public.playlist(customer_id, words)
                VALUES ($1, $2)
                RETURNING *
                ''',
                customer_id,
                list(set(words))
            )

            await asyncio.sleep(5)

        else:
            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите',
                    'reply_markup': {
                        'keyboard': [[{'text': '🛠️ Выбор параметров'}], HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }

                }
            )

        return

    @classmethod
    async def get_playlist(cls, chat_id, _id):  # Отправка трека из списка плейлист
        playlist = await db.fetchrow(
            '''
            SELECT *
            FROM public.playlist
            WHERE id = $1
            ''',
            int(_id)
        )
        await tgclient.api_call(
            method_name='sendAudio',
            payload={
                'chat_id': chat_id,
                'audio': playlist['url'],
                'reply_markup': {
                    'keyboard': [HOME_BUTTON],
                    'one_time_keyboard': True,
                    'resize_keyboard': True
                }
            }
        )

    @classmethod
    async def playlists(cls, customer_id, chat_id, page=1):  # Список плейлист с пагинацией
        page = int(page)
        limit = 5
        offset = (page - 1) * limit

        buttons = []

        playlists = await db.fetch(
            '''
            SELECT *
            FROM public.playlist
            WHERE customer_id = $1 AND status = 3 AND url IS NOT NULL
            ORDER BY id desc
            LIMIT $2 OFFSET $3
            ''',
            customer_id,
            limit,
            offset
        ) or []

        for x in playlists:
            buttons.append([
                {
                    'text': f'🎵 {x["title"] or "Без название"}',
                    'callback_data': f'playlist:id:{x["id"]}'
                }
            ])

        total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.playlist
            WHERE customer_id = $1 AND status = 3 AND url IS NOT NULL
            ''',
            customer_id
        ) or 0

        next_page = total > (limit * page)
        prev_page = page > 1

        if next_page or prev_page:
            a = []
            if prev_page:
                a.append({
                    'text': f'⏮️',
                    'callback_data': f'playlist:page:{page - 1}'
                })
            if next_page:
                a.append({
                    'text': f'⏭️',
                    'callback_data': f'playlist:page:{page + 1}'
                })

            buttons.append(a)

        if buttons:
            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите',
                    'reply_markup': {
                        'inline_keyboard': buttons,
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

    async def get(self, request):
        return response.json({})

    async def post(self, request):
        data = request.json

        print(f'[post] data: {data}')

        message = DictUtils.as_dict(data.get('message'))
        callback_query = DictUtils.as_dict(data.get('callback_query'))

        if message:
            chat_id = StrUtils.to_str(message.get('chat', {}).get('id'))  # чат id пользователя
            sender = message.get('from', {})  # информация о пользователе
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
                method_name='sendPhoto',
                payload={
                    'chat_id': chat_id,
                    'caption': '*Что умеет этот бот?*\n\n'
                               'Подбор музыки, соответствующей текущему эмоциональному состоянию пользователя '
                               'Генерация мелодии на основе заданного настроения и предпочтений пользователя',
                    'photo': 'https://art.ttshop.kz/static/uploads/78/cf/78cf9c70-7622-4800-b97d-f6b52de3a176.jpeg',
                    'parse_mode': 'Markdown',
                    'reply_markup': {
                        'keyboard': MENU_BUTTONS,
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': 'Привет! Меня зовут TulparIfy. '
                            'Я здесь, чтобы помочь тебе с помощью арт-терапии через музыку.'
                            'Как тебя зовут?',
                    'reply_markup': {
                        'keyboard': [HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )
            await cache.setex(f'art:question:name:{customer["id"]}', 600, '1')

            return response.json({})

        text = None
        success = False
        questions = None

        if message and message.get('text'):
            text = message['text']

        if callback_query and callback_query.get('data'):
            text = callback_query['data']
            if text:
                if text.startswith('playlist'):
                    _, r, _id = text.split(':')
                    if r == 'id':
                        await self.get_playlist(chat_id, _id)
                        return response.json({})
                    elif r == 'page':
                        await self.playlists(customer['id'], chat_id, _id)
                        return response.json({})

        if text and text.startswith('🏠'):
            await self.finalize(customer['id'])
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите',
                    'reply_markup': {
                        'keyboard': MENU_BUTTONS,
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            return response.json({})

        elif text and text.startswith('🎼'):
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите',
                    'reply_markup': {
                        'keyboard': [[{'text': '🛠️ Выбор параметров'}], [{'text': '🔎 Генерация трека'}], HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            return response.json({})

        elif text and text.startswith('🛠'):
            await self.finalize(customer['id'])
            questions = await self.generate_questions(customer['id'], 'ai')

        elif text and text.startswith('💬'):
            await self.finalize(customer['id'])
            questions = await self.generate_questions(customer['id'], 'search')

        elif text and text.startswith('📁'):
            await self.playlists(customer['id'], chat_id)
            return response.json({})

        elif text and text.startswith('\u2069'):
            await cache.setex(f'art:telegram:audio:name:{customer["id"]}', 600, '1')
            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': 'Напишите название трека',
                    'reply_markup': {
                        'keyboard': [HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )
            return response.json({})

        elif await cache.get(f'art:telegram:audio:name:{customer["id"]}'):
            playlist_id = IntUtils.to_int(await cache.get(f'art:telegram:audio:{customer["id"]}'))
            if playlist_id:
                t = 'Сохранено'
                await db.fetchrow(
                    '''
                    UPDATE public.playlist
                    SET status = 3, title = $2
                    WHERE id = $1
                    ''',
                    playlist_id,
                    text
                )
            else:
                t = 'Ничего не найден'

            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': t,
                    'reply_markup': {
                        'keyboard': [HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            await cache.delete(f'art:telegram:audio:name:{customer["id"]}', f'art:telegram:audio:{customer["id"]}')

            return response.json({})

        elif text and text.startswith('🔎'):
            await self.generate_turn(customer['id'], chat_id)
            await self.finalize(customer['id'])

            return response.json({})

        elif await cache.get(f'art:telegram:questions:rating:{customer["id"]}'):
            lemmas = m.lemmatize(text)
            success = True
            for x in RISK_WORDS:
                if len(list(set(x) & set(lemmas))) == len(x):
                    if await cache.get(f'art:telegram:risk:{customer["id"]}'):
                        await tgclient.api_call(
                            payload={
                                'chat_id': chat_id,
                                'text': 'Рекомендую обратиться к профессиональному психологу или психотерапевту,'
                                        ' если это беспокоит длительное время. Арт-терапия может быть эффективным '
                                        'дополнением к другим методам лечения депрессии, таким как медикаментозная '
                                        'терапия и психотерапия',
                                'reply_markup': {
                                    'keyboard': [HOME_BUTTON],
                                    'one_time_keyboard': True,
                                    'resize_keyboard': True
                                }
                            }
                        )
                        success = False
                    break

            if success:
                await tgclient.api_call(
                    method_name='sendMessage',
                    payload={
                        'chat_id': chat_id,
                        'text': 'Спасибо за вашу обратную связь!',
                        'reply_markup': {
                            'keyboard': MENU_BUTTONS,
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )
            await self.finalize(customer['id'])
            return response.json({})

        elif await cache.get(f'art:telegram:locale_tune:{customer["id"]}'):
            await self.send_rating(customer['id'], chat_id, text)
            return response.json({})

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

            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите',
                    'reply_markup': {
                        'keyboard': MENU_BUTTONS,
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            return response.json({})

        if not questions:
            questions = await cache.get(f'art:telegram:questions:{customer["id"]}')
            if questions:
                questions = ujson.loads(questions)

        if text:
            success, method = True, 'sendMessage'
            while success:
                prev_question = await cache.get(f'art:telegram:prev_question:{customer["id"]}')

                if questions:
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
                                await cache.lpush(f'art:telegram:words:{customer["id"]}', genre)

                    lemmas = m.lemmatize(text)  # поиск основы слов

                    for x in RISK_WORDS:
                        if len(list(set(x) & set(lemmas))) == len(x):
                            await cache.setex(f'art:telegram:risk:{customer["id"]}', 600, 1)
                            await self.send_locale_tune(customer['id'], chat_id)

                            return response.json({})

                if not question:
                    question = questions.pop(0) if questions else {}

                payload, end = {'chat_id': chat_id}, False

                if question:
                    await cache.setex(f'art:telegram:prev_question:{customer["id"]}', 600, ujson.dumps(question))
                    await cache.setex(f'art:telegram:questions:{customer["id"]}', 600, ujson.dumps(questions))
                    payload['text'] = question['text']

                else:
                    end = True

                if end:
                    if prev_question and prev_question.get('is_last'):
                        await self.send_locale_tune(customer['id'], chat_id)
                        return response.json({})
                    else:
                        payload.update({
                            'text': 'Выберите',
                            'reply_markup': {
                                'keyboard': [[{'text': '🔎 Генерировать трек'}], HOME_BUTTON],
                                'one_time_keyboard': True,
                                'resize_keyboard': True
                            }
                        })

                elif question and question['buttons']:
                    payload.update({
                        'reply_markup': {
                            'keyboard': [
                                [{
                                    'text': button['text'],
                                }] for button in question['buttons'] + HOME_BUTTON
                            ],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    })
                else:
                    payload.update({
                        'reply_markup': {
                            'keyboard': [HOME_BUTTON],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    })

                await tgclient.api_call(method_name=method, payload=payload)
                break

        if success is False:
            if text and text.startswith('📃️'):
                buttons = await db.fetchval(
                    '''
                    WITH a AS (SELECT title
                               FROM public.kbase
                               WHERE type = 'reference'
                               ORDER BY id)
                    SELECT array_agg(title)
                    FROM a
                    '''
                )
                await tgclient.api_call(
                    payload={
                        'chat_id': chat_id,
                        'text': 'Выберите',
                        'reply_markup': {
                            'keyboard': [[{'text': x}] for x in buttons] + [HOME_BUTTON],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )

                return response.json({})

            elif text and text.startswith('ℹ️'):
                await tgclient.api_call(
                    method_name='sendPhoto',
                    payload={
                        'chat_id': chat_id,
                        'caption': '*Что умеет этот бот?*\n\n'
                                   'Подбор музыки, соответствующей текущему эмоциональному состоянию пользователя '
                                   'Генерация мелодии на основе заданного настроения и предпочтений пользователя',
                        'photo': 'https://art.ttshop.kz/static/uploads/78/cf/78cf9c70-7622-4800-b97d-f6b52de3a176.jpeg',
                        'parse_mode': 'Markdown',
                        'reply_markup': {
                            'keyboard': MENU_BUTTONS,
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )

                return response.json({})

            kbase = await db.fetchrow(
                '''
                SELECT *
                FROM public.kbase
                WHERE title = $1
                ''',
                text
            )
            if kbase:
                await tgclient.api_call(
                    payload={
                        'chat_id': chat_id,
                        'text': kbase['response'],
                        'parse_mode': 'Markdown',
                        'reply_markup': {
                            'keyboard': MENU_BUTTONS,
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )

            else:
                await tgclient.api_call(
                    payload={
                        'chat_id': chat_id,
                        'text': 'В системе ничего не найдено',
                        'reply_markup': {
                            'keyboard': MENU_BUTTONS,
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )

        return response.json({})
