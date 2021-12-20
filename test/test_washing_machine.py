import pytest
from aiohttp import web
from aiohttp.test_utils import RawTestServer
from tenacity import wait_none
from vzug import BasicDevice, WashingMachine, const
from .util import get_test_response_from_file

import logconf

logconf.setup_logging()

# Disable retry wait time for better test performance
BasicDevice.make_vzug_device_call_json.retry.wait = wait_none()


async def device_program_active_handler(request: web.BaseRequest):
    if const.COMMAND_GET_PROGRAM in request.path_qs:
        return get_test_response_from_file('washing_machine_program_status_active.json')
    else:
        return 'WRONG REQUEST'


async def device_program_idle_handler(request: web.BaseRequest):
    if const.COMMAND_GET_PROGRAM in request.path_qs:
        return get_test_response_from_file('washing_machine_program_status_idle.json')
    else:
        return 'WRONG REQUEST'


@pytest.fixture
async def server_prog_active(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(device_program_active_handler, port=aiohttp_unused_port())


@pytest.fixture
async def server_prog_idle(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(device_program_idle_handler, port=aiohttp_unused_port())


async def test_program_information_active(server_prog_active: RawTestServer):
    device = WashingMachine(server_prog_active.host + ":" + str(server_prog_active.port))
    active = await device.load_program_details()

    assert active is True
    assert device.program_status == "active"
    assert device.program_name == "40°C Outdoor"
    assert device.optidos_active is True
    assert device.optidos_b_status == "ok"
    assert device.optidos_b_status == "ok"


async def test_program_information_idle(server_prog_idle: RawTestServer):
    device = WashingMachine(server_prog_idle.host + ":" + str(server_prog_idle.port))
    active = await device.load_program_details()

    assert active is False
    assert device.program_status == "idle"
    assert device.program_name == ""
    assert device.optidos_active is False
    assert device.optidos_b_status == "ok"
    assert device.optidos_b_status == "ok"


async def test_program_information_wrong_address():
    device = WashingMachine('localhost_wrong_host')
    active = await device.load_program_details()

    assert active is False
    assert device.error_code == "n/a"
    assert isinstance(device.error_exception.inner_exception, IOError)
