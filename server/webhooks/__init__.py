from sanic import Blueprint

__all__ = ['webhooks_bp']

from webhooks.telegram import TelegramWebhookHandler

webhooks_bp = Blueprint('webhooks', url_prefix='/webhooks')

webhooks_bp.add_route(TelegramWebhookHandler.as_view(), '/telegram/')
