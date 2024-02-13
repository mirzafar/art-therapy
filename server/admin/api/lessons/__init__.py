from sanic import Blueprint

from .create import LessonsCreateView
from .info import LessonsInfoTemplateView
from .item import LessonsItemView
from .list import LessonsView

__all__ = ['lessons_bp']

from .me import LessonsMeTemplateView

from .tags import LessonsTagsView, LessonsTagsItemView
from .template import LessonsTemplateView

lessons_bp = Blueprint('lessons', url_prefix='/lessons')

# Lessons
lessons_bp.add_route(LessonsCreateView.as_view(), '/create/')
lessons_bp.add_route(LessonsView.as_view(), '/')
lessons_bp.add_route(LessonsTemplateView.as_view(), '/template/')
lessons_bp.add_route(LessonsItemView.as_view(), '/<lesson_id>/')
lessons_bp.add_route(LessonsMeTemplateView.as_view(), '/me/template/')
lessons_bp.add_route(LessonsInfoTemplateView.as_view(), '/info/<lesson_id>/template/')

# Tags
lessons_bp.add_route(LessonsTagsView.as_view(), '/tags/')
lessons_bp.add_route(LessonsTagsItemView.as_view(), '/tags/<tag_id>/')
