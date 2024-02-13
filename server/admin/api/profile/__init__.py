from sanic import Blueprint

from admin.api.profile.item import ProfileView

__all__ = ['profile_bp']

profile_bp = Blueprint('profile', url_prefix='/profile')

profile_bp.add_route(ProfileView.as_view(), '/')
