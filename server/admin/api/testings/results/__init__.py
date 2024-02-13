from sanic import Blueprint

from admin.api.testings.results.item import TestingsResultsItemTemplateView, TestingsResultslistTemplateView
from admin.api.testings.results.list import TestingsResultsAPIView
from admin.api.testings.results.template import TestingsResultsTemplateView

results_bp = Blueprint('results', url_prefix='/results')

results_bp.add_route(TestingsResultsAPIView.as_view(), '/<lesson_id>/list/')
results_bp.add_route(TestingsResultsTemplateView.as_view(), '/<lesson_id>/template/')
results_bp.add_route(TestingsResultsItemTemplateView.as_view(), '/<result_id>/indicators/template/')
results_bp.add_route(TestingsResultslistTemplateView.as_view(), '/<result_id>/indicators/list/')
