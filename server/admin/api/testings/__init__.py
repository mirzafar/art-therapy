from sanic import Blueprint

from admin.api.sales import sales_bp
from admin.api.testings.answers import answer_bp
from admin.api.testings.complete import complete_bp
from admin.api.testings.questions import question_bp
from admin.api.testings.responses import responses_bp
from admin.api.testings.results import results_bp

testing_bp = Blueprint.group(
    answer_bp,
    question_bp,
    complete_bp,
    results_bp,
    responses_bp,
    url_prefix='/testings'
)
