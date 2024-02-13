from datetime import datetime

from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.strs import StrUtils


class ProductsItemView(BaseAPIView):
    template_name = 'admin/sales-products-item.html'

    async def get(self, request, user, item_id):
        if not ObjectId.is_valid(item_id):
            return self.error(message='Required param(s): item_id')

        item = await mongo.products.find_one({'_id': ObjectId(item_id)}) or {}

        return self.success(request=request, user=user, data={
            'product': item,
        })

    async def post(self, request, user, item_id):
        print(';dasda')
        if item_id == 'create':
            pass
        else:
            if not ObjectId.is_valid(item_id):
                return self.error(message='Required param(s): item_id')
            item_id = ObjectId(item_id)

        title = StrUtils.to_str(request.json.get('title'))
        photo = StrUtils.to_str(request.json.get('photo'))

        if not title:
            return self.error(message='Required param(s): title')

        fields = {
            'title': title,
            'photo': photo,
        }

        if item_id == 'create':
            fields.update({
                'status': 0,
                'created_at': datetime.now()
            })
            await mongo.products.insert_one(fields)

        else:
            await mongo.products.update_one({'_id': ObjectId(item_id)}, {'$set': fields})

        return self.success()

    async def delete(self, request, user, item_id):
        if not ObjectId.is_valid(item_id):
            return self.error(message='Required param(s): item_id')

        await mongo.products.update_one({'_id': ObjectId(item_id)}, {'$set': {
            'status': -1
        }})

        return self.success()
