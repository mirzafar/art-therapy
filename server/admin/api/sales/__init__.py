from sanic import Blueprint

from admin.api.sales.goods import goods_bp
from admin.api.sales.overheads import overheads_bp
from admin.api.sales.products import products_bp

sales_bp = Blueprint.group(
    products_bp,
    goods_bp,
    overheads_bp,
    url_prefix='/sales'
)
