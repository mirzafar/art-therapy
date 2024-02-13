from sanic_openapi import doc

from core.db import db
from core.handlers import BaseAPIView
from models import DistrictsModels
from utils.ints import IntUtils
from utils.strs import StrUtils


class DistrictsItemView(BaseAPIView):

    async def get(self, request, user, district_id):
        district_id = IntUtils.to_int(district_id)
        if not district_id:
            return self.error(message='Отсуствует обязательный параметры "district_id: int"')

        district = await db.fetchrow(
            '''
            SELECT d.*,
                (
                    CASE WHEN r.id IS NULL THEN NULL
                    ELSE jsonb_build_object(
                        'id', r.id,
                        'title', r.title
                    )
                    END
                ) AS region
            FROM public.districts d
            LEFT JOIN public.regions r ON d.region_id = r.id
            WHERE d.id = $1
            ''',
            district_id
        ) or {}

        return self.success(request=request, user=user, data={
            'district': dict(district)
        })

    @doc.consumes(DistrictsModels, location='body', required=True)
    async def post(self, request, user, district_id):
        district = await db.fetchrow(
            '''
            INSERT INTO public.districts(title, region_id)
            VALUES ($1, $2)
            RETURNING *
            ''',
            StrUtils.to_str(request.json.get('title')),
            IntUtils.to_int(request.json.get('region_id'))
        )

        if not district:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'district': dict(district)
        })

    @doc.consumes(DistrictsModels, location='body', required=True)
    async def put(self, request, user, district_id):
        district_id = IntUtils.to_int(district_id)
        if not district_id:
            return self.error(message='Отсуствует обязательный параметр "district_id: int"')

        district = await db.fetchrow(
            '''
            UPDATE public.districts
            SET title = $2, region_id = $3
            WHERE id = $1
            RETURNING *
            ''',
            district_id,
            StrUtils.to_str(request.json.get('title')),
            IntUtils.to_int(request.json.get('region_id'))
        )

        if not district:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'district': dict(district)
        })

    async def delete(self, request, user, district_id):
        district_id = IntUtils.to_int(district_id)
        if not district_id:
            return self.error(message='Отсуствует обязательный параметр "district_id: int"')

        district = await db.fetchrow(
            '''
            UPDATE public.districts
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            district_id
        )

        if not district:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'district': dict(district)
        })
