from datetime import datetime

from bson import ObjectId

from core.datetimes import DatetimeUtils
from core.db import mongo
from core.handlers import BaseAPIView
from utils.floats import FloatUtils
from utils.strs import StrUtils


class SalesGoodsItemView(BaseAPIView):
    template_name = 'admin/sales-goods-item.html'

    async def get(self, request, user, item_id):
        if not ObjectId.is_valid(item_id):
            return self.error(message='Required param(s): item_id')

        item = await mongo.goods.find_one({'_id': ObjectId(item_id)}) or {}

        return self.success(request=request, user=user, data={
            'item': item,
        })

    async def post(self, request, user, item_id):
        if item_id == 'create':
            pass
        else:
            if not ObjectId.is_valid(item_id):
                return self.error(message='Required param(s): item_id')
            item_id = ObjectId(item_id)

        title = StrUtils.to_str(request.json.get('title'))
        photo = StrUtils.to_str(request.json.get('photo'))
        started_at = DatetimeUtils.parse(request.json.get('started_at'))
        stopped_at = DatetimeUtils.parse(request.json.get('stopped_at'))
        cost = FloatUtils.to_float(request.json.get('cost')) or 0.0
        price = FloatUtils.to_float(request.json.get('price')) or 0.0
        discount = FloatUtils.to_float(request.json.get('discount')) or 0.0
        amount = FloatUtils.to_float(request.json.get('amount')) or 0.0
        product_id = StrUtils.to_str(request.json.get('product_id'))
        store_id = StrUtils.to_str(request.json.get('store_id'))
        overhead_id = StrUtils.to_str(request.json.get('overhead_id'))

        if not title:
            return self.error(message='Required param(s): title')

        if started_at and stopped_at:
            if stopped_at <= started_at:
                return self.error(message='started at more than stopped at')

        if (stopped_at and stopped_at < datetime.now()) or (started_at and started_at > datetime.now()):
            return self.error(message='stopped at or started at more than now')

        fields = {
            'title': title,
            'photo': photo,
            'started_at': started_at,
            'stopped_at': stopped_at,
            'discount': discount,
            'amount': amount,
            'store_id': store_id,
            'overhead_id': overhead_id,
            'product_id': product_id,
            'price': price,
            'cost': cost,
        }

        if item_id == 'create':
            fields.update({
                'status': 0,
                'created_at': datetime.now()
            })
            await mongo.goods.insert_one(fields)

        else:
            fields.update({
                'updated_at': datetime.now()
            })

            await mongo.goods.update_one(
                {'_id': item_id}, {'$set': fields}
            )

        return self.success()

    async def delete(self, request, user, item_id):
        if not ObjectId.is_valid(item_id):
            return self.error(message='Required param(s): item_id')

        await mongo.goods.update_one({'_id': ObjectId(item_id)}, {'$set': {
            'status': -1
        }})

        return self.success()
