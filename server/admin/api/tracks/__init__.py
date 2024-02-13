from sanic import Blueprint

from .item import TracksItemView
from .list import TracksView

__all__ = ['tracks_bp']

tracks_bp = Blueprint('tracks', url_prefix='/tracks')

tracks_bp.add_route(TracksView.as_view(), '/')
tracks_bp.add_route(TracksItemView.as_view(), '/<track_id>/')
