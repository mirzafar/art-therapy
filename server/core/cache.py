import functools
from typing import Union

import aio_pika
import aioredis

from settings import settings


class Cache:

    def __init__(self):
        self.pool = None
        self.loop = None
        self.extra_pool = None

        self.channel = None

    async def initialize(self, loop, db=1, maxsize=10):
        self.loop = loop

        self.pool = await aioredis.create_redis_pool(
            settings['redis'],
            db=db,
            loop=loop,
            maxsize=maxsize,
            encoding='utf-8'
        )

        self.extra_pool = await aioredis.create_redis_pool(
            settings['redis'],
            db=3,
            loop=loop,
            maxsize=2,
            encoding='utf-8'
        )

        # self.subscriber = await aioredis.create_redis_pool(settings['redis'], loop=loop)

        # connection = await aio_pika.connect_robust(
        #     settings['mq'], loop=loop
        # )
        #
        # self.channel = await connection.channel()  # type: aio_pika.Channel

    def __getattr__(self, attr):
        return functools.partial(getattr(self.pool, attr))

    def multi_exec(self):
        return self.pool.multi_exec()


cache = Cache()  # type: Union[aioredis.Redis, Cache]
