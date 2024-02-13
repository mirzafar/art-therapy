from sanic import Blueprint

from admin.api.sales.overheads.item import SalesOverheadsItemView
from admin.api.sales.overheads.list import SalesOverheadsView

overheads_bp = Blueprint('overheads', url_prefix='/overheads')

overheads_bp.add_route(SalesOverheadsView.as_view(), '/')
overheads_bp.add_route(SalesOverheadsItemView.as_view(), '/<item_id>/')
