import asyncio
import os
import uuid

import scipy
from transformers import AutoProcessor, MusicgenForConditionalGeneration

from clients.telegram import tgclient
from server.core.db import mongo
from settings import settings

processor = AutoProcessor.from_pretrained('facebook/musicgen-small')
model = MusicgenForConditionalGeneration.from_pretrained('facebook/musicgen-small')


async def generate(order):
    inputs = processor(
        text=[' '.join(order['words'])],
        padding=True,
        return_tensors='pt',
    )

    uid = str(uuid.uuid4())
    root_dir = settings['root_dir'] + '/static/uploads/' + f'{uid[:2]}/{uid[2:4]}'
    if not os.path.isdir(root_dir):
        os.makedirs(root_dir)

    audio_values = model.generate(**inputs, max_new_tokens=1024)
    sampling_rate = model.config.audio_encoder.sampling_rate
    scipy.io.wavfile.write(f'{root_dir}/{uid}.mp3', rate=sampling_rate, data=audio_values[0, 0].numpy())

    await tgclient.api_call(
        method_name='sendPhoto',
        payload={
            'chat_id': order['chat_id'],
            'photo': f'{settings["base_url"]}/static/uploads/{uid[:2]}/{uid[2:4]}/{uid}.mp3'
        }
    )

    await mongo.orders.update_one({'_id': order['_id']}, {'$set': {
        'status': 1
    }})


async def main():
    mongo.initialize(loop=loop)
    while True:
        order = await mongo.orders.find_one({'status': 0})
        if not order:
            await asyncio.sleep(2)
            continue

        loop.create_task(generate(order))
        await asyncio.sleep(2)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
