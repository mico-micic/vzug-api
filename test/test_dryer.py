from tenacity import wait_none
from flask import Flask
from flask import request
from flask_testing import LiveServerTestCase
from unittest import IsolatedAsyncioTestCase
from datetime import datetime
from vzug import BasicDevice, Dryer, DeviceError, DEVICE_TYPE_DRYER
from vzug.const import COMMAND_GET_COMMAND, COMMAND_GET_PROGRAM, COMMAND_GET_STATUS, COMMAND_GET_MODEL_DESC
from vzug.dryer import CMD_VALUE_CONSUMP_DRYER_TOTAL, CMD_VALUE_CONSUMP_DRYER_AVG
from .util import get_test_response_from_file_raw

# Disable retry wait time for better test performance
BasicDevice.make_vzug_device_call_json.retry.wait = wait_none()


def server_status_ok_func():
    cmd = request.args.get('command')
    if cmd == COMMAND_GET_STATUS:
        return get_test_response_from_file_raw('device_status_ok_resp.json')
    elif cmd == COMMAND_GET_MODEL_DESC:
        return 'AdoraDry V4000'
    else:
        return 'WRONG REQUEST'


def server_program_active_func():
    if request.args.get('command') == COMMAND_GET_PROGRAM:
        return get_test_response_from_file_raw('dryer_program_status_active.json')
    else:
        return consumption_ok_handler_func()


def server_program_idle_func():
    if request.args.get('command') == COMMAND_GET_PROGRAM:
        return get_test_response_from_file_raw('dryer_program_status_idle.json')
    else:
        return 'WRONG REQUEST'


def consumption_ok_handler_func():
    cmd = request.args.get('command')
    value = request.args.get('value')
    if cmd == COMMAND_GET_COMMAND and value == CMD_VALUE_CONSUMP_DRYER_AVG:
        return get_test_response_from_file_raw('dryer_consumption_avg.json')
    elif cmd == COMMAND_GET_COMMAND and value == CMD_VALUE_CONSUMP_DRYER_TOTAL:
        return get_test_response_from_file_raw('dryer_consumption_total.json')
    else:
        return 'WRONG REQUEST'


def create_app_with_func(func1, func2):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.route('/ai')(func1)
    app.route('/hh')(func2)
    return app


class TestOkAndActiveProgramInformation(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(server_status_ok_func, server_program_active_func)

    async def test_all_information(self):
        device = Dryer(self.get_server_url())
        loaded = await device.load_all_information()

        assert loaded is True
        assert device.device_name == "TestDevice"
        assert device.serial == "123"
        assert device.status == "Testing"
        assert device.program == "TestProgram"
        assert device.uuid == "test-uuid"
        assert device.model_desc == "AdoraDry V4000"
        assert device.is_active is True
        assert device.device_type is DEVICE_TYPE_DRYER

        assert device.program_status == "active"
        assert device.program_name == "Extra dry"

        assert device.power_consumption_kwh_total == 119.0
        assert device.power_consumption_kwh_avg == 0.7

    async def test_program_information_active(self):
        device = Dryer(self.get_server_url())
        active = await device.load_program_details()

        assert active is True
        assert device.program_status == "active"
        assert device.program_name == "Extra dry"
        assert device.seconds_to_end == 3660

        end = device.get_date_time_end().replace(microsecond=0)
        assert (end-datetime.now().replace(microsecond=0)).total_seconds() == 3660

    async def test_program_information_wrong_address(self):
        device = Dryer('localhost_wrong_host')
        active = await device.load_program_details()

        assert active is False
        assert device.error_code == "n/a"
        assert isinstance(device.error_exception.inner_exception, IOError)


class TestIdleProgramInformation(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(server_status_ok_func, server_program_idle_func)

    async def test_program_information_idle(self):
        device = Dryer(self.get_server_url())
        active = await device.load_program_details()

        assert active is False
        assert device.program_status == "idle"
        assert device.program_name == ""


class TestConsumptionInformation(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(server_status_ok_func, consumption_ok_handler_func)

    async def test_consumption_information(self):
        device = Dryer(self.get_server_url())
        loaded = await device.load_consumption_data()

        assert loaded is True
        assert device.power_consumption_kwh_total == 119.0
        assert device.power_consumption_kwh_avg == 0.7
        

class TestConsumptionErrorInformation(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(server_status_ok_func,
                                    lambda: "wrong data")

    async def test_consumption_wrong_data(self):
        device = Dryer(self.get_server_url())
        loaded = await device.load_consumption_data()

        assert loaded is False
        assert device.error_code == "n/a"
        assert len(device.error_message) > 0
        assert isinstance(device.error_exception, DeviceError)
