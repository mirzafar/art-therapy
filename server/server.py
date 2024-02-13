import os

from sanic import Sanic
from sanic_openapi import openapi2_blueprint

from admin import LoginAdminView, LogoutAdminView
from admin.api import api_group
from api.core.upload import UploadView
from core.auth import auth
from core.cache import cache
from core.db import mongo, db
from core.session import session
from settings import settings
from webhooks import webhooks_bp

app = Sanic(name='demo')

app.config.AUTH_LOGIN_URL = '/api/login/'
app.config.ACCESS_LOG = False
app.config.DB_HOST = settings.get('db', {}).get('host', '127.0.0.1')
app.config.DB_DATABASE = settings.get('db', {}).get('database', 'maindb')
app.config.DB_PORT = settings.get('db', {}).get('port', 5432)
app.config.DB_USER = settings.get('db', {}).get('user', 'postgres')
app.config.DB_PASSWORD = settings.get('db', {}).get('password', '1234')
app.config.DB_POOL_MAX_SIZE = 25
app.config.RESPONSE_TIMEOUT = 600
app.config.FALLBACK_ERROR_FORMAT = 'html'
app.config.DEBUG = True
app.config['API_SCHEMES'] = ['https']
app.config['API_SECURITY'] = [{'ApiKeyAuth': []}]
app.config['API_SECURITY_DEFINITIONS'] = {
    'ApiKeyAuth': {'type': 'apiKey', 'in': 'header', 'name': 'X-API-Token'}
}


@app.listener('before_server_start')
async def initialize_modules(_app, _loop):
    await db.initialize(_app, _loop)
    mongo.initialize(_loop)
    await cache.initialize(_loop, maxsize=5)
    session.initialize(_app)
    auth.initialize(_app)


app.blueprint([
    api_group,
    webhooks_bp,
])

app.add_route(UploadView.as_view(), '/api/upload/')
app.add_route(LoginAdminView.as_view(), '/api/login/')
app.add_route(LogoutAdminView.as_view(), '/api/logout/')

app.static('/static', os.path.join(settings.get('file_path'), 'static'))

if __name__ == '__main__':
    try:
        app.run('127.0.0.1', port=8109, access_log=True)
    except Exception as e:
        print(e)
