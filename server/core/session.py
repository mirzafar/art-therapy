import uuid

import ujson

from core.cache import cache
from core.db import mongo


class Session:
    app = None

    def initialize(self, app):
        self.app = app

        app.router.reset()
        app.register_middleware(self._process_request, 'request')
        app.register_middleware(self._process_response, 'response')
        app.finalize()

    @classmethod
    def is_protected_path(cls, path) -> bool:
        if path.startswith('/api/login') or path.startswith('/api/logout'):
            return True
        return False

    async def _process_request(self, request):
        session_id = request.headers.get('X-API-Token') or request.args.get('token') or request.cookies.get('sid')

        request.ctx.session = {}

        if session_id:
            session_data = await cache.get(f'session:{session_id}')
            if session_data:
                request.ctx.session = ujson.loads(session_data)

    async def _process_response(self, request, response):
        if not self.is_protected_path(request.path):
            return

        session_id = request.headers.get('X-API-Token') or request.args.get('token') or request.cookies.get('sid')

        if not session_id:
            if hasattr(request.ctx, 'session_id'):
                session_id = request.ctx.session_id
                response.cookies['sid'] = session_id
                response.cookies['sid']['max-age'] = 60 * 60 * 24 * 365 * 10

        if not session_id:
            session_id = uuid.uuid4().hex
            response.cookies['sid'] = session_id
            response.cookies['sid']['max-age'] = 60 * 60 * 24 * 365 * 10

        if hasattr(request.ctx, 'session'):
            if request.ctx.session.get('_delete'):
                del response.cookies['sid']
                await cache.delete(f'session:{session_id}')
                await mongo.users.delete_one({'token': session_id})
            else:
                await cache.setex(f'session:{session_id}', 60 * 60 * 1, ujson.dumps(request.ctx.session))

    @classmethod
    async def create_session(cls, request, user_id):
        session_id = request.cookies.get('sid')
        if not session_id:
            session_id = uuid.uuid4().hex

        request.ctx.session_id = session_id

        await cache.setex(f'session:{session_id}', 60 * 60 * 1, ujson.dumps({'user_id': user_id}))

        return session_id


session = Session()
