from flask import Flask
from flask import request
from flask_httpauth import HTTPDigestAuth
from flask_testing import LiveServerTestCase
from unittest import IsolatedAsyncioTestCase
from vzug import BasicDevice
from vzug import const
from .util import get_test_response_from_file_raw

auth = HTTPDigestAuth()

USER_PW = {
    "admin": "test-password"
}


@auth.get_password
def pw_func(user):
    return USER_PW.get(user)


@auth.login_required
def status_func():
    return get_test_response_from_file_raw('device_status_ok_resp.json')


@auth.login_required
def machine_type_func():
    cmd = request.args.get('command')
    if cmd == const.COMMAND_GET_MACHINE_TYPE:
        return const.DEVICE_TYPE_SHORT_WASHING_MACHINE
    else:
        return 'WRONG REQUEST'


class TestAuth(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'secret key here'
        app.route(f"/{const.ENDPOINT_AI}")(status_func)
        app.route(f"/{const.ENDPOINT_HH}")(machine_type_func)
        return app

    async def test_no_auth(self):
        device = BasicDevice(self.get_server_url())
        loaded = await device.load_device_information()

        assert loaded is False
        assert device.error_exception.is_auth_problem is True

    async def test_invalid_auth(self):
        device = BasicDevice(self.get_server_url(), "admin", "wrong-pw")
        loaded = await device.load_device_information()

        assert loaded is False
        assert device.error_exception.is_auth_problem is True

    async def test_valid_auth(self):
        device = BasicDevice(self.get_server_url(), "admin", "test-password")
        loaded = await device.load_device_information()

        assert loaded is True
        assert device.error_exception is None
        assert device.device_name == "TestDevice"
        assert device.device_type == const.DEVICE_TYPE_WASHING_MACHINE
