from sanic import Blueprint

from admin.api.categories.item import CategoriesItemView
from admin.api.categories.list import CategoriesView

category_bp = Blueprint('category', url_prefix='/categories')

category_bp.add_route(CategoriesView.as_view(), '/', name='categories')
category_bp.add_route(CategoriesItemView.as_view(), '/<category_id>/', name='categories-item')
