import hashlib
from datetime import datetime
from functools import partial, wraps
from inspect import isawaitable
from typing import Optional

import ujson
from pymongo import ReturnDocument
from sanic import response

from core.cache import cache
from core.db import db, mongo
from utils.strs import StrUtils

__all__ = ['auth']


class Auth:
    app = None
    login_endpoint = None
    login_url = None

    def initialize(self, app):
        if self.app is not None:
            raise RuntimeError('already initialized with an application')
        self.app = app
        self.login_endpoint = app.config.get('AUTH_LOGIN_ENDPOINT', None)
        self.login_url = app.config.get('AUTH_LOGIN_URL', None)

    @classmethod
    def generate_token(cls, user_id) -> Optional[str]:
        if user_id:
            token = hashlib.md5()
            token.update(bytes(str(user_id), encoding='utf-8'))
            return token.hexdigest()
        else:
            return None

    @classmethod
    async def login(cls, request, user, token):
        request.ctx.session['token'] = token

        return await mongo.users.update_one({'user_id': user['id'], 'token': token}, {'$set': {
            'logged_at': datetime.now(),
            'device': request.headers.get('user-agent', None)
        }}, upsert=True)

    @classmethod
    async def logout(cls, request):
        request.ctx.session['_delete'] = True

    @classmethod
    async def current_user(cls, request):
        token = StrUtils.to_str(request.headers.get('X-API-Token') or request.args.get('token'))

        if not token:
            token = request.ctx.session.get('token')

            if not token:
                return

        if not await cache.get(f'session:{token}'):
            return

        user = await mongo.users.find_one_and_update({'token': token}, {'$set': {
            'viewed_at': datetime.now()
        }}, return_document=ReturnDocument.AFTER)

        if not user:
            return

        await cache.setex(f'session:{token}', 60 * 60 * 1, ujson.dumps(request.ctx.session))

        return await db.fetchrow(
            '''
            SELECT 
                u.id, 
                u.last_name,
                u.first_name,
                u.middle_name,
                u.status,
                u.password,
                u.username,
                u.photo
            FROM public.users u
            WHERE u.id = $1
            ''',
            user['user_id']
        )

    def login_required(
        self,
        route=None,
        *,
        user_keyword='user',
        handle_no_auth=None
    ):
        if route is None:
            return partial(
                self.login_required,
                user_keyword=user_keyword,
                handle_no_auth=handle_no_auth
            )

        if handle_no_auth is not None:
            assert callable(handle_no_auth), 'handle_no_auth must be callable'

        @wraps(route)
        async def privileged(request, *args, **kwargs):
            user = await self.current_user(request)
            if isawaitable(user):
                user = user

            if user:
                if user_keyword is not None:
                    if user_keyword in kwargs:
                        raise RuntimeError(
                            'override user keyword %r in route' % user_keyword
                        )

                    kwargs[user_keyword] = dict(user)

                resp = route(request, *args, **kwargs)
            else:
                if handle_no_auth:
                    resp = handle_no_auth(request)
                else:
                    resp = self.handle_no_auth(request)

            if isawaitable(resp):
                resp = await resp

            return resp

        return privileged

    @classmethod
    def get_session(cls, request):
        return request.ctx.session

    def handle_no_auth(self, request):
        u = self.login_url or request.app.url_for(self.login_endpoint)
        return response.redirect(u)


auth = Auth()
