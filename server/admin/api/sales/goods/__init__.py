from sanic import Blueprint

from admin.api.sales.goods.item import SalesGoodsItemView
from admin.api.sales.goods.list import SalesGoodsView

goods_bp = Blueprint('goods', url_prefix='/goods')

goods_bp.add_route(SalesGoodsView.as_view(), '/')
goods_bp.add_route(SalesGoodsItemView.as_view(), '/<item_id>/')
