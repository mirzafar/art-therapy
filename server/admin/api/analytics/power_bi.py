from sanic import response

from core.db import db
from core.encoder import encoder
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.strs import StrUtils


class AnalyticsLessonsTemplateView(BaseAPIView):

    async def get(self, request, user):
        page = request.args.get('page', 1)
        limit = request.args.get('limit', 10)

        pager = Pager()
        pager.set_page(page)
        pager.set_limit(limit)

        query = StrUtils.to_str(request.args.get('query'))

        cond, cond_vars = ['l.status >= {}'], [0]

        if query:
            cond.append('l.title ILIKE {}')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))

        data = await db.fetch(
            '''
            SELECT
                l.id,
                l.title,
                count(DISTINCT r.id) AS count_result,
                sum(r.total) AS sum_total,
                sum(r.currect) AS sum_currect,
                sum(r.wrong) AS sum_wrong
            FROM testings.results r
            LEFT JOIN public.lessons l ON r.lesson_id = l.id
            WHERE %s
            GROUP BY l.id
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        )

        lessons = []
        for x in data:
            x = dict(x)
            x['sum_currect_percent'] = round(((x['sum_currect'] or 0) * 100 / x['sum_total']), 2) or 0
            x['sum_wrong_percent'] = 100 - x['sum_currect_percent']
            lessons.append(x)

        pager.total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.lessons l
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0

        self.context = {
            '_success': True,
            'lessons': lessons,
            'pager': pager.dict(),
            'user': dict(user)
        }

        return response.json(self.context, dumps=encoder.encode)
