from sanic import Blueprint

from .item import RegionsItemView
from .list import RegionsView

__all__ = ['regions_bp']

regions_bp = Blueprint('regions', url_prefix='/regions')

regions_bp.add_route(RegionsView.as_view(), '/')
regions_bp.add_route(RegionsItemView.as_view(), '/<region_id>/')
