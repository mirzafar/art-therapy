from sanic import Blueprint

from admin.api.chats.chats import ChatsTemplateView
from admin.api.chats.messages import ChatsMessagesAPIView
from admin.api.chats.chats import ChatsAPIView

chats_bp = Blueprint('chats', url_prefix='/chats')

chats_bp.add_route(ChatsTemplateView.as_view(), '/template/')
chats_bp.add_route(ChatsAPIView.as_view(), '/')
chats_bp.add_route(ChatsMessagesAPIView.as_view(), '/messages/')
