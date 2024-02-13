from core import httpclient
from settings import settings


class TelegramClient:
    TOKEN = settings.get('tg', {}).get('token')

    async def api_call(
        self,
        http_method: str = 'post',
        method_name: str = 'sendMessage',
        payload=None
    ) -> dict:

        if http_method.strip().lower() == 'post':
            if not method_name:
                return {}

            success, result = await httpclient.request(
                method='post',
                url=f'https://api.telegram.org/bot{self.TOKEN}/{method_name}',
                json=payload,
            )

            if success and result:
                return result

            return {}


tgclient = TelegramClient()
