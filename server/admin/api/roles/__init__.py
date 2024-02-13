from sanic import Blueprint

from admin.api.roles.item import RolesItemView
from admin.api.roles.list import RolesView

role_bp = Blueprint('roles', url_prefix='/roles')

role_bp.add_route(RolesView.as_view(), '/', name='categories')
role_bp.add_route(RolesItemView.as_view(), '/<role_id>', name='categories-item')
