from jinja2 import Environment, select_autoescape, FileSystemLoader
from sanic import response

from settings import settings

root_dir = settings.get('root_dir')
TEMPLATE_DIR = '/'.join(root_dir.split('/')[:-1])

env = Environment(
    loader=FileSystemLoader(f'{TEMPLATE_DIR}/templates'),
    autoescape=select_autoescape()
)


def not_found(request, exception):
    template = env.get_template('errors/404.html')
    rendered = template.render(
        request=request,
        app=request.app,
        url_for=request.app.url_for
    )
    return response.HTTPResponse(rendered, content_type='text/html')
