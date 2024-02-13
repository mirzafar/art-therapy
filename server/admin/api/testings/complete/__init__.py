from sanic import Blueprint

from admin.api.testings.complete.list import TestingsCompleteAPIView
from admin.api.testings.complete.template import TestingsCompleteTemplatesView

complete_bp = Blueprint('complete', url_prefix='/complete')

complete_bp.add_route(TestingsCompleteTemplatesView.as_view(), '/<lesson_id>/template/')
complete_bp.add_route(TestingsCompleteAPIView.as_view(), '/<lesson_id>/')
