from sanic_openapi import doc

from core.datetimes import DatetimeUtils
from core.db import db
from core.handlers import BaseAPIView
from core.hasher import password_to_hash
from models import UsersModels
from utils.ints import IntUtils
from utils.strs import StrUtils


class UsersItemView(BaseAPIView):
    template_name = 'admin/users-item.html'

    async def get(self, request, user, user_id):
        user_id = IntUtils.to_int(user_id)
        if not user_id:
            return self.error(message='Required param(s): user_id')

        customer = await db.fetchrow(
            '''
            SELECT *
            FROM public.users
            WHERE id = $1
            ''',
            user_id
        )

        if not customer:
            return self.error(message='Пользователь не найден(-o, -а) в системе')

        return self.success(request=request, user=user, data={
            'customer': dict(customer)
        })

    @doc.consumes(UsersModels, location='body')
    async def post(self, request, user, user_id):
        first_name = StrUtils.to_str(request.json.get('first_name'))
        last_name = StrUtils.to_str(request.json.get('last_name'))
        middle_name = StrUtils.to_str(request.json.get('middle_name'))
        birthday = DatetimeUtils.parse(request.json.get('birthday'))
        username = StrUtils.to_str(request.json.get('username'))
        password = StrUtils.to_str(request.json.get('password'))
        photo = StrUtils.to_str(request.json.get('photo'))

        if not first_name or not last_name:
            return self.error(message='Отсуствует обязательный параметры "first_name: str, last_name: str"')

        if username:
            duplicate = await db.fetchrow(
                '''
                SELECT *
                FROM public.users
                WHERE username = $1
                ''',
                username
            )
            if duplicate:
                return self.error(
                    message='Пользователь с этими значениями уже существует. Дубликат не может быть создан'
                )

        else:
            return self.error(message='Отсуствует обязательный параметр "username: str"')

        if not password:
            return self.error(message='Отсуствует обязательный параметр "password: str"')

        user = await db.fetchrow(
            '''
            INSERT INTO public.users
            (last_name, first_name, middle_name, password, username, photo, birthday)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            ''',
            last_name,
            first_name,
            middle_name,
            password_to_hash(password),
            username,
            photo,
            birthday,
        )

        if not user:
            return self.error(message='Операция не выполнена')

        return self.success(
            data={
                'user': dict(user)
            }
        )

    @doc.consumes(UsersModels, location='body', required=True)
    @doc.consumes(doc.String(description='main, reset_password'), required=True)
    async def put(self, request, user, user_id):
        user_id = IntUtils.to_int(user_id)
        if not user_id:
            return self.error(message='Отсуствует обязательный параметр "user_id: int"')

        action = StrUtils.to_str(request.args.get('action'))
        if action == 'main':
            first_name = StrUtils.to_str(request.json.get('first_name'))
            last_name = StrUtils.to_str(request.json.get('last_name'))
            middle_name = StrUtils.to_str(request.json.get('middle_name'))
            birthday = DatetimeUtils.parse(request.json.get('birthday'))
            username = StrUtils.to_str(request.json.get('username'))
            photo = StrUtils.to_str(request.json.get('photo'))
            status = IntUtils.to_int(request.json.get('status')) or 0

            if not first_name or not last_name:
                return self.error(message='Отсуствует обязательный параметры "first_name: str, last_name: str"')

            if username:
                duplicate = await db.fetchrow(
                    '''
                    SELECT *
                    FROM public.users
                    WHERE id <> $1 AND username = $2
                    ''',
                    user_id,
                    username
                )
                if duplicate:
                    return self.error(
                        message='Пользователь с этими значениями уже существует. Дубликат не может быть создан'
                    )

            else:
                return self.error(message='Отсуствует обязательный параметр "username: str"')

            user = await db.fetchrow(
                '''
                UPDATE public.users
                SET 
                    last_name = $2,
                    first_name = $3, 
                    middle_name = $4, 
                    username = $5, 
                    photo = $6, 
                    birthday = $7,
                    status = $8
                WHERE id = $1
                RETURNING *
                ''',
                user_id,
                last_name,
                first_name,
                middle_name,
                username,
                photo,
                birthday,
                status
            )

            if not user:
                return self.error(message='Операция не выполнена')

            return self.success(data={
                'user': dict(user)
            })

        elif action == 'reset_password':
            password = StrUtils.to_str(request.json.get('password'))
            if not password:
                return self.error(message='Отсуствует обязательный параметр "password: str"')

            user = await db.fetchrow(
                '''
                UPDATE public.users
                SET password = $2
                WHERE id = $1
                RETURNING *
                ''',
                user_id,
                password_to_hash(password)
            )
            if not user:
                return self.error(message='Операция не выполнена')

            return self.success(data={
                'user': dict(user)
            })

        return self.success()

    async def delete(self, request, user, user_id):
        user_id = IntUtils.to_int(user_id)
        if not user_id:
            return self.error(message='Отсуствует обязательный параметр "user_id: int"')

        user = await db.fetchrow(
            '''
            UPDATE public.users
            SET status = -2
            WHERE id = $1
            RETURNING *
            ''',
            user_id
        )

        if not user:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'user': dict(user)
        })
