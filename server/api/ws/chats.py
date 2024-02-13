# import ujson
# from sanic import Request, Websocket
#
# from utils.strs import StrUtils
#
# users = dict()
#
#
# async def chat_messages(request: Request, ws: Websocket):
#     while True:
#         data = ujson.loads(await ws.recv())
#         user_id = StrUtils.to_str(data.get('user_id'))
#         action = StrUtils.to_str(data.pop('action', None))
#
#         if action == 'open':
#             if user_id:
#                 users[user_id] = ws
#
#         elif action in ['close', 'error']:
#             if user_id:
#                 users.pop(user_id, None)
#
#         elif action == 'message':
#             data['is_me'] = False
#             recipient_id = StrUtils.to_str(data.get('recipient_id'))
#             if recipient_id and recipient_id in users:
#                 if not users[recipient_id] == ws:
#                     await users[recipient_id].send(ujson.dumps(data))
