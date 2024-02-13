from sanic import Blueprint

from admin.api.testings.responses.list import TestingsResponsesAPIView
from admin.api.testings.responses.template import TestingsResponsesTemplateView

responses_bp = Blueprint('responses', url_prefix='/responses')

responses_bp.add_route(TestingsResponsesTemplateView.as_view(), '/<result_id>/template/')
responses_bp.add_route(TestingsResponsesAPIView.as_view(), '/<result_id>/list/')
