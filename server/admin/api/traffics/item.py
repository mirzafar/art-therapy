from sanic_openapi.openapi2 import doc

from core.db import db, mongo
from core.handlers import BaseAPIView
from models import TrafficsModels
from utils.ints import IntUtils
from utils.strs import StrUtils


class TrafficsItemView(BaseAPIView):

    async def get(self, request, user, traffic_id):
        traffic_id = IntUtils.to_int(traffic_id)
        if not traffic_id:
            return self.error(message='Отсуствует обязательный параметры "traffic_id: int"')

        traffic = await db.fetchrow(
            '''
            SELECT t.*,
                ( 
                    CASE WHEN tk.id IS NULL THEN NULL
                    ELSE jsonb_build_object(
                        'id', tk.id,
                        'title', tk.title
                    )
                    END
                ) AS track,
                ( 
                    CASE WHEN d.id IS NULL THEN NULL
                    ELSE jsonb_build_object(
                        'id', d.id,
                        'title', d.title
                    )
                    END
                ) AS district,
                ( 
                    CASE WHEN r.id IS NULL THEN NULL
                    ELSE jsonb_build_object(
                        'id', r.id,
                        'title', r.title,
                        'number', r.number
                    )
                    END
                ) AS region
            FROM public.traffics t
            LEFT JOIN public.tracks tk ON t.track_id = tk.id
            LEFT JOIN public.districts d ON tk.district_id = d.id
            LEFT JOIN public.regions r ON d.region_id = r.id
            WHERE t.id = $1
            ''',
            traffic_id
        ) or {}

        return self.success(request=request, user=user, data={
            'traffic': traffic
        })

    @doc.consumes(TrafficsModels, location='body', required=True)
    async def post(self, request, user, traffic_id):
        traffic = await db.fetchrow(
            '''
            INSERT INTO public.traffics(title, description, track_id, video_path, counters, state)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            ''',
            StrUtils.to_str(request.json.get('title')),
            StrUtils.to_str(request.json.get('description')),
            IntUtils.to_int(request.json.get('track_id')),
            StrUtils.to_str(request.json.get('video_path')),
            {
                'cars': 0,
                'trucks': 0,
                'buses': 0,
            },
            0 if request.json.get('video_path') else -2
        )

        if not traffic:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'traffic': dict(traffic)
        })

    @doc.consumes(TrafficsModels, location='body', required=True)
    async def put(self, request, user, traffic_id):
        traffic_id = IntUtils.to_int(traffic_id)
        if not traffic_id:
            return self.error(message='Отсуствует обязательный параметр "traffic_id: int"')

        traffic = await mongo.traffics.find_one({'id': traffic_id})
        if traffic and traffic.get('state') in [1, 2]:
            return self.error(message='Редактирование запрещено')

        traffic = await db.fetchrow(
            '''
            UPDATE public.traffics
            SET title = $2, description = $3, track_id = $4, video_path = $5, state = $6
            WHERE id = $1
            RETURNING *
            ''',
            traffic_id,
            StrUtils.to_str(request.json.get('title')),
            StrUtils.to_str(request.json.get('description')),
            IntUtils.to_int(request.json.get('track_id')),
            StrUtils.to_str(request.json.get('video_path')),
            0 if request.json.get('video_path') else -2
        )

        if not traffic:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'track': dict(traffic)
        })

    async def delete(self, request, user, traffic_id):
        traffic_id = IntUtils.to_int(traffic_id)
        if not traffic_id:
            return self.error(message='Отсуствует обязательный параметр "traffic_id: int"')

        traffic = await db.fetchrow(
            '''
            UPDATE public.traffics
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            traffic_id
        )

        if not traffic:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'traffic': dict(traffic)
        })
