from sanic import Blueprint

from admin.api.testings.answers.item import TestingsAnswersItemAPIView
from admin.api.testings.answers.list import TestingsAnswersAPIView
from admin.api.testings.answers.template import TestingsAnswersTemplatesView

answer_bp = Blueprint('answers', url_prefix='/answers')

answer_bp.add_route(TestingsAnswersAPIView.as_view(), '/<question_id>/list/')
answer_bp.add_route(TestingsAnswersTemplatesView.as_view(), '/<question_id>/')
answer_bp.add_route(TestingsAnswersItemAPIView.as_view(), '/<answer_id>/')
