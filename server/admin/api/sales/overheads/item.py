from datetime import datetime

from bson import ObjectId

from core.datetimes import DatetimeUtils
from core.db import mongo
from core.handlers import BaseAPIView
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.strs import StrUtils


class SalesOverheadsItemView(BaseAPIView):
    template_name = 'admin/sales-overheads-item.html'

    async def get(self, request, user, item_id):
        if not ObjectId.is_valid(item_id):
            return self.error(message='Required param(s): item_id')

        item = await mongo.overheads.find_one({'_id': ObjectId(item_id)}) or {}

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
        description = StrUtils.to_str(request.json.get('description'))
        paid_summ = FloatUtils.to_float(request.json.get('paid_summ')) or 0.0
        summa = FloatUtils.to_float(request.json.get('summ')) or 0.0
        whole = FloatUtils.to_float(request.json.get('whole')) or 0.0
        amount_goods = IntUtils.to_int(request.json.get('amount_goods')) or 0
        organization_id = IntUtils.to_int(request.json.get('organization_id'))
        photo = StrUtils.to_str(request.json.get('photo'))
        document_number = StrUtils.to_str(request.json.get('document_number'))
        compiled_at = DatetimeUtils.parse(request.json.get('compiled_at'))

        if not title:
            return self.error(message='Required param(s): title')

        fields = {
            'title': title,
            'description': description,
            'photo': photo,
            'paid_summ': paid_summ,
            'summa': summa,
            'amount_goods': amount_goods,
            'whole': whole,
            'organization_id': organization_id,
            'document_number': document_number,
            'compiled_at': compiled_at
        }

        if item_id == 'create':
            fields.update({
                'status': 0,
                'created_at': datetime.now()
            })
            await mongo.overheads.insert_one(fields)

        else:
            await mongo.overheads.update_one(
                {'_id': item_id}, {'$set': fields}
            )

        return self.success()

    async def delete(self, request, user, item_id):
        if not ObjectId.is_valid(item_id):
            return self.error(message='Required param(s): item_id')

        await mongo.overheads.update_one({'_id': ObjectId(item_id)}, {'$set': {
            'status': -1
        }})

        return self.success()
