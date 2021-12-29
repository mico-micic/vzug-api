import pytest
from aiohttp import web
from aiohttp.test_utils import RawTestServer
from tenacity import wait_none
from vzug import BasicDevice, WashingMachine, const, DeviceError, DEVICE_TYPE_WASHING_MACHINE
from vzug.washing_machine import COMMAND_VALUE_ECOM_STAT_TOTAL, COMMAND_VALUE_ECOM_STAT_AVG
from .util import get_test_response_from_file


# Disable retry wait time for better test performance
BasicDevice.make_vzug_device_call_json.retry.wait = wait_none()


async def device_all_information_handler(request: web.BaseRequest):
    if const.COMMAND_GET_STATUS in request.path_qs:
        return get_test_response_from_file('device_status_ok_resp.json')
    elif const.COMMAND_GET_MODEL_DESC in request.path_qs:
        return web.Response(text='AdoraWash V4000')
    elif const.COMMAND_GET_PROGRAM in request.path_qs:
        return get_test_response_from_file('washing_machine_program_status_active.json')
    else:
        return await consumption_ok_handler(request)


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


async def consumption_ok_handler(request: web.BaseRequest):
    if const.COMMAND_GET_COMMAND in request.path_qs and COMMAND_VALUE_ECOM_STAT_AVG in request.path_qs:
        return get_test_response_from_file('washing_machine_consumption_avg.json')
    elif const.COMMAND_GET_COMMAND in request.path_qs and COMMAND_VALUE_ECOM_STAT_TOTAL in request.path_qs:
        return get_test_response_from_file('washing_machine_consumption_total.json')
    else:
        return 'WRONG REQUEST'


async def consumption_err_handler(request: web.BaseRequest):
    return get_test_response_from_file('washing_machine_consumption_err.json')


@pytest.fixture
async def server_prog_active(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(device_program_active_handler, port=aiohttp_unused_port())


@pytest.fixture
async def server_all_information(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(device_all_information_handler, port=aiohttp_unused_port())


@pytest.fixture
async def server_prog_idle(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(device_program_idle_handler, port=aiohttp_unused_port())


@pytest.fixture
async def server_consumption_ok(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(consumption_ok_handler, port=aiohttp_unused_port())


@pytest.fixture
async def server_consumption_err(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(consumption_err_handler, port=aiohttp_unused_port())


async def test_all_information(server_all_information: RawTestServer):
    device = WashingMachine(server_all_information.host + ":" + str(server_all_information.port))
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

    assert device.program_status == "active"
    assert device.program_name == "40°C Outdoor"
    assert device.optidos_active is True
    assert device.optidos_b_status == "ok"
    assert device.optidos_b_status == "ok"

    assert device.power_consumption_kwh_total == 29.0
    assert device.power_consumption_kwh_avg == 0.6
    assert device.water_consumption_l_total == 2119.0
    assert device.water_consumption_l_avg == 37.0


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


async def test_consumption_information(server_consumption_ok: RawTestServer):
    device = WashingMachine(server_consumption_ok.host + ":" + str(server_consumption_ok.port))
    loaded = await device.load_consumption_data()

    assert loaded is True
    assert device.power_consumption_kwh_total == 29.0
    assert device.power_consumption_kwh_avg == 0.6
    assert device.water_consumption_l_total == 2119.0
    assert device.water_consumption_l_avg == 37.0


async def test_consumption_wrong_data(server_consumption_err: RawTestServer):
    device = WashingMachine(server_consumption_err.host + ":" + str(server_consumption_err.port))
    loaded = await device.load_consumption_data()

    assert loaded is False
    assert device.error_code == "n/a"
    assert len(device.error_message) > 0
    assert isinstance(device.error_exception, DeviceError)
