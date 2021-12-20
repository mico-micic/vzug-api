from aiohttp import web


def get_test_response_from_file(filename: str) -> web.Response:
    with open('resources/' + filename, 'r') as file:
        return web.Response(text=file.read().rstrip())
