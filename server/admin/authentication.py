from sanic import response
from sanic_openapi import doc

from core.db import db
from core.handlers import TemplateHTTPView, auth, BaseAPIView
from core.hasher import password_to_hash
from core.session import session
from models import UsersLoginModels
from utils.strs import StrUtils


class LoginAdminView(TemplateHTTPView):
    template_name = 'auth/login.html'

    async def get(self, request):
        await auth.logout(request)
        return self.success(request=request)

    @doc.consumes(UsersLoginModels, location='body')
    async def post(self, request):
        if not request.json:
            return response.json({
                '_success': False,
                'message': 'Отсуствует обязательный параметр(ы)'
            })

        username = StrUtils.to_str(request.json.get('username'))
        password = StrUtils.to_str(request.json.get('password'))

        if not username:
            return response.json({
                '_success': False,
                'message': 'Отсуствует обязательный параметр "username: str"'
            })

        if not password:
            return response.json({
                '_success': False,
                'message': 'Отсуствует обязательный параметр "password: str"'
            })

        user = await db.fetchrow(
            '''
            SELECT *
            FROM public.users u
            WHERE u.username = $1 AND u.password = $2
            ''',
            username,
            password_to_hash(password=password)
        )

        if user:
            user = dict(user)
        else:
            return response.json({
                '_success': False,
                'message': 'Пользователь не найден(-o, -а) в системе'
            })

        if user['status'] == -1:
            return response.json({
                '_success': False,
                'message': 'Пользователь заблокирован(-о, -а) в системе'
            })

        elif user['status'] == -2:
            return response.json({
                '_success': False,
                'message': 'Пользователь удален(-о, -а) из системы'
            })

        token = await session.create_session(request, user['id'])
        await auth.login(request, user, token)

        return response.json({
            '_success': True,
            'url': '/api/',
            'token': token,
            'user_id': user['id'],
        })


class LogoutAdminView(BaseAPIView):
    async def get(self, request, user):
        await auth.logout(request)
        return response.redirect('/')
