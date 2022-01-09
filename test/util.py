import pathlib


def get_test_response_from_file_raw(filename: str) -> str:
    path = pathlib.Path(__file__).parent.resolve().joinpath('resources').joinpath(filename)
    with open(path, 'r') as file:
        return file.read().rstrip()
