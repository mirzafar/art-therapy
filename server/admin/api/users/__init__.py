from sanic import Blueprint

from .item import UsersItemView
from .list import UsersListView

__all__ = ['users_bp']

users_bp = Blueprint('users', url_prefix='/users')

users_bp.add_route(UsersListView.as_view(), '/')
users_bp.add_route(UsersItemView.as_view(), '/<user_id>/')
