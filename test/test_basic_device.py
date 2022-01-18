from tenacity import wait_none
from flask import Flask
from flask import request
from flask_testing import LiveServerTestCase
from unittest import IsolatedAsyncioTestCase
from vzug import const
from vzug import BasicDevice, DEVICE_TYPE_WASHING_MACHINE
from .util import get_test_response_from_file_raw

# Disable retry wait time for better test performance
BasicDevice.make_vzug_device_call_json.retry.wait = wait_none()


def server_ok_func():
    cmd = request.args.get('command')
    if cmd == const.COMMAND_GET_STATUS:
        return get_test_response_from_file_raw('device_status_ok_resp.json')
    elif cmd == const.COMMAND_GET_MODEL_DESC:
        return 'AdoraWash V4000'
    else:
        return 'WRONG REQUEST'


def create_app_with_func(func):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.route('/ai')(func)
    return app


class TestOkResponse(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(server_ok_func)

    async def test_device_information_ok(self):
        device = BasicDevice(self.get_server_url())
        loaded = await device.load_device_information()

        assert loaded is True
        assert device.device_name == "TestDevice"
        assert device.serial == "123"
        assert device.status == "Testing"
        assert device.program == "TestProgram"
        assert device.uuid == "test-uuid"
        assert device.model_desc == "AdoraWash V4000"
        assert device.is_active is True
        assert device.device_type is DEVICE_TYPE_WASHING_MACHINE

    async def test_device_all_information(self):
        device = BasicDevice(self.get_server_url())
        loaded = await device.load_all_information()

        assert loaded is True
        assert device.device_name == "TestDevice"
        assert device.serial == "123"
        assert device.status == "Testing"
        assert device.program == "TestProgram"
        assert device.uuid == "test-uuid"
        assert device.model_desc == "AdoraWash V4000"
        assert device.is_active is True
        assert device.device_type is DEVICE_TYPE_WASHING_MACHINE


class TestErrResponse(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(lambda: get_test_response_from_file_raw('device_status_error_resp.json'))

    async def test_device_information_error(self):
        device = BasicDevice(self.get_server_url())
        loaded = await device.load_device_information()

        assert loaded is False
        assert device._error_code == "501"

    async def test_device_information_wrong_address(self):
        device = BasicDevice('localhost_wrong_host')
        loaded = await device.load_device_information()

        assert loaded is False
        assert device.error_code == "n/a"
        assert isinstance(device.error_exception.inner_exception, IOError)


class TestInvalidResponse(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(lambda: 'no json response')

    async def test_device_information_invalid(self):
        device = BasicDevice(self.get_server_url())
        loaded = await device.load_device_information()

        assert loaded is False
        assert device.error_code == "n/a"
        assert isinstance(device.error_exception is not None and device.error_exception.inner_exception, ValueError)
