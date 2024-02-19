import asyncio

from replicate import Client

from clients.telegram import tgclient
from core.db import db
from settings import settings


class App:
    class Config:
        ACCESS_LOG = False
        DB_HOST = settings.get('db', {}).get('host', '127.0.0.1')
        DB_DATABASE = settings.get('db', {}).get('database', 'kenes')
        DB_PORT = settings.get('db', {}).get('port', 5432)
        DB_USER = settings.get('db', {}).get('user', 'root')
        DB_PASSWORD = settings.get('db', {}).get('password', 'X$@ABN^')
        DB_USE_CONNECTION_FOR_REQUEST = False
        DB_POOL_MAX_SIZE = 25

    def __init__(self):
        self.config = App.Config()


async def main():
    await db.initialize(App(), loop)
    client = Client(api_token='r8_agYdIyP42udjzCiMulRpAEdB4jLPrvw2DbB8v')

    while True:
        order = await db.fetchrow(
            '''
            SELECT *
            FROM public.orders
            WHERE status = 0
            '''
        )

        if order:
            loop.create_task(generate(order, client))

        await asyncio.sleep(5)


async def generate(order, client):
    output = await client.async_run(
        'meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38',
        input={
            'top_k': 250,
            'top_p': 0,
            'prompt': "piano classic",
            'duration': 10,
            'temperature': 1,
            'continuation': False,
            'model_version': "stereo-large",
            'output_format': "mp3",
            'continuation_start': 0,
            'multi_band_diffusion': False,
            'normalization_strategy': "peak",
            'classifier_free_guidance': 3
        }
    )

    await db.fetchrow(
        '''
        UPDATE public.orders
        SET status = 1, url = $2
        WHERE id = $1
        ''',
        order['id'],
        str(output)
    )

    await tgclient.api_call(
        method_name='sendAudio',
        payload={
            'chat_id': order['chat_id'],
            'audio': str(output)
        }
    )


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
