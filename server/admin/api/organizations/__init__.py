from sanic import Blueprint

from admin.api.organizations.fields import OrganizationsFieldsView
from admin.api.organizations.item import OrganizationsItemView
from admin.api.organizations.list import OrganizationsView

__all__ = ['organizations_bp']

organizations_bp = Blueprint('organizations', url_prefix='/organizations')

organizations_bp.add_route(OrganizationsView.as_view(), '/')
organizations_bp.add_route(OrganizationsItemView.as_view(), '/<item_id>/')
organizations_bp.add_route(OrganizationsFieldsView.as_view(), '/fields/')
