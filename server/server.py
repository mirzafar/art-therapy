from sanic import Sanic

from api.core.upload import UploadView
from core.cache import cache
from core.db import db
from settings import settings
from webhooks import webhooks_bp

app = Sanic(name='demo')

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


@app.listener('before_server_start')
async def initialize_modules(_app, _loop):
    await db.initialize(_app, _loop)
    await cache.initialize(_loop, maxsize=5)


app.blueprint([
    webhooks_bp,
])

app.add_route(UploadView.as_view(), '/api/upload/')

if __name__ == '__main__':
    try:
        app.run('127.0.0.1', port=8109, access_log=True)
    except Exception as e:
        print(e)
