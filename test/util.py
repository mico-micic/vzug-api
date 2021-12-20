import pathlib

from aiohttp import web


def get_test_response_from_file(filename: str) -> web.Response:
    path = pathlib.Path(__file__).parent.resolve().joinpath('resources').joinpath(filename)
    with open(path, 'r') as file:
        return web.Response(text=file.read().rstrip())
