import os
import uuid

import aiofiles
from sanic import response
from sanic.views import HTTPMethodView

from settings import settings


class UploadView(HTTPMethodView):
    async def post(self, request):
        file_path = settings.get('file_path', '') + '/static/uploads'
        file = request.files and request.files['file']
        if file:
            file = file[0]
            uid = str(uuid.uuid4())

            ext = file.name.split('.')[len(file.name.split('.')) - 1]  # [::-1][0]
            file_name = f'{file_path}/{uid[:2]}/{uid[2:4]}/{uid}.{ext}'
            os.makedirs(f'{file_path}/{uid[:2]}/{uid[2:4]}', 0o755, True)

            async with aiofiles.open(file_name, 'wb') as f:
                await f.write(file.body)

            return response.json({
                '_success': True,
                'file_name': f'{uid[:2]}/{uid[2:4]}/{uid}.{ext}'
            })

        return response.json({
            '_success': False,
            'message': 'File not found'
        }, status=405)
