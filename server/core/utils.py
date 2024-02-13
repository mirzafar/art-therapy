from core.db import mongo


async def mongo_generate_id(collection):
    ret = await mongo.command(
        'findAndModify',
        'counters',
        query={'_id': collection},
        update={'$inc': {'seq': 1}},
        new=True,
        upsert=True
    )
    return ret['value']['seq']
