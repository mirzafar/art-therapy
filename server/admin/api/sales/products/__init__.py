from sanic import Blueprint

from admin.api.sales.products.item import ProductsItemView
from admin.api.sales.products.list import ProductsView

products_bp = Blueprint('products', url_prefix='/products')

products_bp.add_route(ProductsView.as_view(), '/')
products_bp.add_route(ProductsItemView.as_view(), '/<item_id>/')

