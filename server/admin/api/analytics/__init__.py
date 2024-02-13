from sanic import Blueprint

from admin.api.analytics.power_bi import AnalyticsLessonsTemplateView
from admin.api.analytics.template import AnalyticsTemplateView

__all__ = ['power_bi_bp']

power_bi_bp = Blueprint('analytics', url_prefix='/analytics')

power_bi_bp.add_route(AnalyticsTemplateView.as_view(), '/template/')
power_bi_bp.add_route(AnalyticsLessonsTemplateView.as_view(), '/lessons/')
