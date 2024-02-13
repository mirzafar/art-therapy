from datetime import datetime

from core.datetimes import DatetimeUtils
from core.db import mongo
from core.handlers import BaseAPIView
from core.pager import Pager
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.strs import StrUtils


class SalesOverheadsView(BaseAPIView):
    template_name = 'admin/sales-overheads.html'

    async def get(self, request, user):
        response_type = request.args.get('response_type', 'html')
        if response_type == 'html':
            return self.success(request=request, user=user)

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 10))

        query = StrUtils.to_str(request.args.get('query'))
        document_number = StrUtils.to_str(request.args.get('document-number'))
        status = IntUtils.to_int(request.args.get('status'))

        filters = {
            'status': 0
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        if document_number:
            filters['document_number'] = {'$regex': document_number, '$options': 'i'}

        if status is not None:
            filters['status'] = status

        overheads = await mongo.overheads.find(filters) \
            .limit(pager.limit) \
            .skip(pager.offset) \
            .sort({'_id': -1}) \
            .to_list(length=None)

        pager.total = await mongo.overheads.count_documents(filters)

        return self.success(request=request, user=user, data={
            '_success': True,
            'items': overheads,
            'pager': pager.dict(),
        })
