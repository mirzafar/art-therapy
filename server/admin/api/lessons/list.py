from sanic import response

from core.db import db
from core.encoder import encoder
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.bools import BoolUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class LessonsView(BaseAPIView):

    async def get(self, request, user):
        page = request.args.get('page', 1)
        limit = request.args.get('limit', 10)

        pager = Pager()
        pager.set_page(page)
        pager.set_limit(limit)

        query = StrUtils.to_str(request.args.get('query'))
        is_me = BoolUtils.to_bool(request.args.get('is_me'), default=False)

        cond, cond_vars = ['l.status >= {}'], [0]

        if query:
            cond.append('l.title ILIKE {}')
            cond_vars.append(f'%{query}%')

        if is_me:
            cond.append('$1 = ANY (l.subscribers)')

        cond, _ = set_counters(' AND '.join(cond), counter=2)

        lessons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT
                l.*,
                c.title AS category_title,
                $1 = ANY (l.subscribers) AS is_subscribe
            FROM public.lessons l
            LEFT JOIN categories c ON l.category_id = c.id
            WHERE %s
            ORDER BY l.id DESC
            %s
            ''' % (cond, pager.as_query()),
            user['id'],
            *cond_vars
        ))

        pager.total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.lessons l
            WHERE l.status >= $1 %s
            ''' % (' AND ' + cond) if cond else '',
            0,
            *cond_vars
        ) or 0

        self.context = {
            '_success': True,
            'lessons': lessons,
            'pager': pager.dict(),
            'user': dict(user)
        }

        return response.json(self.context, dumps=encoder.encode)
