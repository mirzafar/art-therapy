from sanic import Blueprint

from admin.api.testings.questions.list import TestingsQuestionsAPIView
from admin.api.testings.questions.item import TestingsQuestionsItemAPIView
from admin.api.testings.questions.template import TestingsQuestionsTemplatesView

question_bp = Blueprint('questions', url_prefix='/questions')

question_bp.add_route(TestingsQuestionsAPIView.as_view(), '/<lesson_id>/list/')
question_bp.add_route(TestingsQuestionsTemplatesView.as_view(), '/<lesson_id>/template/')
question_bp.add_route(TestingsQuestionsItemAPIView.as_view(), '/<question_id>/')
