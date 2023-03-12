from tenacity import wait_none
from flask import Flask
from flask import request
from flask_testing import LiveServerTestCase
from unittest import IsolatedAsyncioTestCase
from datetime import datetime
from vzug import BasicDevice, Dishwasher, DeviceError
from vzug import const
from .util import get_test_response_from_file_raw

# Disable retry wait time for better test performance
BasicDevice.make_vzug_device_call_json.retry.wait = wait_none()


def server_ai_status_ok_func():
    cmd = request.args.get('command')
    if cmd == const.COMMAND_GET_STATUS:
        return get_test_response_from_file_raw('device_status_ok_resp.json')
    elif cmd == const.COMMAND_GET_MODEL_DESC:
        return 'AdoraDish V4000'
    else:
        return 'WRONG REQUEST'

def server_ai_status_timed_func():
    cmd = request.args.get('command')
    if cmd == const.COMMAND_GET_STATUS:
        return get_test_response_from_file_raw('dishwasher_status_timed_resp.json')
    elif cmd == const.COMMAND_GET_MODEL_DESC:
        return 'AdoraDish V4000'
    else:
        return 'WRONG REQUEST'


def server_hh_program_active_func():
    if request.args.get('command') == const.COMMAND_GET_PROGRAM:
        return get_test_response_from_file_raw('dishwasher_program_status_active.json')
    else:
        return server_hh_default_func()

def server_hh_program_idle_func():
    if request.args.get('command') == const.COMMAND_GET_PROGRAM:
        return get_test_response_from_file_raw('dishwasher_program_status_idle.json')
    else:
        return server_hh_default_func()


def server_hh_program_timed_func():
    if request.args.get('command') == const.COMMAND_GET_PROGRAM:
        return get_test_response_from_file_raw('dishwasher_program_status_timed.json')
    else:
        return server_hh_default_func()


def server_hh_default_func():
    cmd = request.args.get('command')
    value = request.args.get('value')

    if cmd == const.COMMAND_GET_MACHINE_TYPE:
        return const.DEVICE_TYPE_SHORT_DISHWASHER
    else:
        return 'WRONG REQUEST'


def create_app_with_func(ai_func, hh_func):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.route(f"/{const.ENDPOINT_AI}")(ai_func)
    app.route(f"/{const.ENDPOINT_HH}")(hh_func)
    return app


class TestOkAndActiveProgramInformation(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(server_ai_status_ok_func, server_hh_program_active_func)

    async def test_all_information(self):
        device = Dishwasher(self.get_server_url())
        loaded = await device.load_all_information()

        assert loaded is True
        assert device.device_name == "TestDevice"
        assert device.serial == "123"
        assert device.status == "Testing"
        assert device.program == "TestProgram"
        assert device.uuid == "test-uuid"
        assert device.model_desc == "AdoraDish V4000"
        assert device.is_active is True
        assert device.device_type is const.DEVICE_TYPE_DISHWASHER

        assert device.program_status == "active"
        assert device.program_name == "Éco"

    async def test_program_information_active(self):
        device = Dishwasher(self.get_server_url())
        active = await device.load_program_details()

        assert active is True
        assert device.program_status == "active"
        assert device.program_name == "Éco"
        assert device.seconds_to_end == 21024

        assert device.is_energy_saving is True
        assert device.is_opti_start is True
        assert device.is_partialload is True
        assert device.is_rinse_plus is True
        assert device.is_dry_plus is True

        end = device.get_date_time_end().replace(microsecond=0)
        assert (end-datetime.now().replace(microsecond=0)).total_seconds() == 21024

    async def test_program_information_wrong_address(self):
        device = Dishwasher('localhost_wrong_host')
        active = await device.load_program_details()

        assert active is False
        assert device.error_code == "n/a"
        assert isinstance(device.error_exception.inner_exception, IOError)


class TestIdleProgramInformation(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(server_ai_status_ok_func, server_hh_program_idle_func)

    async def test_program_information_idle(self):
        device = Dishwasher(self.get_server_url())
        active = await device.load_program_details()

        assert active is False
        assert device.program_status == "idle"
        assert device.program_name == ""

class TestTimedProgramInformation(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(server_ai_status_timed_func, server_hh_program_timed_func)

    async def test_program_information_timed(self):
        device = Dishwasher(self.get_server_url())
        loaded = await device.load_all_information()

        assert loaded is True
        assert device._active is True
        assert device.program_status == "timed"
        assert device.program_name == "Éco"
        assert device.status == "Démarrage dans 1h52"
        assert device.program_duration == 22200
        assert device.seconds_to_end == 28996

        start = device.get_date_time_start().replace(microsecond=0)
        assert (start-datetime.now().replace(microsecond=0)).total_seconds() == 6796

        end = device.get_date_time_end().replace(microsecond=0)
        assert (end-datetime.now().replace(microsecond=0)).total_seconds() == 28996

class TestConsumptionErrorInformation(LiveServerTestCase, IsolatedAsyncioTestCase):

    def create_app(self):
        return create_app_with_func(server_ai_status_ok_func,
                                    lambda: "wrong data")

    async def test_consumption_wrong_data(self):
        device = Dishwasher(self.get_server_url())
        loaded = await device.load_all_information()

        assert loaded is False
        assert device.error_code == "n/a"
        assert len(device.error_message) > 0
        assert isinstance(device.error_exception, DeviceError)