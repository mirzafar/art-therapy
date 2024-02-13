from sanic import Blueprint

from .item import TrafficsItemView
from .list import TrafficsView

__all__ = ['traffics_bp']

traffics_bp = Blueprint('traffics', url_prefix='/traffics')

traffics_bp.add_route(TrafficsView.as_view(), '/')
traffics_bp.add_route(TrafficsItemView.as_view(), '/<traffic_id>/')
