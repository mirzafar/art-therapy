from sanic.views import HTTPMethodView
from sanic import response

from core.db import db


class OrdersView(HTTPMethodView):

    async def get(self, request):
        action = request.args.get('action')
        order = {}
        if action and action == 'get_orders':
            order = await db.fetchrow(
                '''
                SELECT *
                FROM public.orders
                WHERE status = 0
                '''
            ) or {}

            if order:
                await db.fetchrow(
                    '''
                    UPDATE public.orders
                    SET status = 1
                    WHERE id = $1
                    ''',
                    order['id']
                )

        return response.json({
            '_success': True,
            'order': dict(order)
        })
