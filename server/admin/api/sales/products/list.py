from datetime import datetime

from core.db import mongo
from core.handlers import BaseAPIView
from core.pager import Pager
from utils.ints import IntUtils
from utils.strs import StrUtils


class ProductsView(BaseAPIView):
    template_name = 'admin/sales-products.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 10))

        query = StrUtils.to_str(request.args.get('query'))
        status = IntUtils.to_int(request.args.get('status'))

        filters = {
            'status': 0
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        if status is not None:
            filters['status'] = status

        products = await mongo.products.find(filters) \
            .limit(pager.limit) \
            .skip(pager.offset) \
            .sort({'_id': -1}) \
            .to_list(length=None)

        pager.total = await mongo.products.count_documents(filters)

        return self.success(request=request, user=user, data={
            '_success': True,
            'products': products,
            'pager': pager.dict(),
        })
