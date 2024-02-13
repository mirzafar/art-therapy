import aiohttp


async def request(
    method,
    url,
    **kwargs
):
    session_params, request_params = {
        'timeout': aiohttp.ClientTimeout(connect=5, total=10)
    }, {}
    try:
        async with aiohttp.ClientSession(**session_params) as session:
            if method == 'get':
                handler = session.get
            elif method == 'post':
                handler = session.post
            else:
                handler = getattr(session, method)
            try:
                async with handler(url, **kwargs) as response:
                    try:
                        data = await response.json()
                        return True, data
                    except Exception as e:
                        print(e)
                        return False, None
            except Exception as e:
                print(e)
                return False, None
    except Exception as e:
        print(e)
        return False, None
