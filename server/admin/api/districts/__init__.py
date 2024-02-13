from sanic import Blueprint

from .item import DistrictsItemView
from .list import DistrictsView

__all__ = ['districts_bp']

districts_bp = Blueprint('districts', url_prefix='/districts')

districts_bp.add_route(DistrictsView.as_view(), '/')
districts_bp.add_route(DistrictsItemView.as_view(), '/<district_id>/')
