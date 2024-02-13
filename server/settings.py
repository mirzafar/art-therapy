settings = {}

SECRET = 'justword'

try:
    from local_settings import settings as ls

    settings.update(ls)
except Exception as e:
    print(e)
