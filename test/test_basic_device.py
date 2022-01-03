import pytest
from aiohttp import web
from aiohttp.test_utils import RawTestServer
from tenacity import wait_none
from vzug import const

from vzug import BasicDevice, DEVICE_TYPE_WASHING_MACHINE
from .util import get_test_response_from_file


# Disable retry wait time for better test performance
BasicDevice.make_vzug_device_call_json.retry.wait = wait_none()


async def device_status_ok_handler(request: web.BaseRequest):
    if const.COMMAND_GET_STATUS in request.path_qs:
        return get_test_response_from_file('device_status_ok_resp.json')
    elif const.COMMAND_GET_MODEL_DESC in request.path_qs:
        return web.Response(text='AdoraWash V4000')
    else:
        return 'WRONG REQUEST'


async def device_status_err_handler(request):
    return get_test_response_from_file('device_status_error_resp.json')


async def device_status_invalid_handler(request):
    return web.Response(text='no json response')


@pytest.fixture
async def server_ok(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(device_status_ok_handler, port=aiohttp_unused_port())


@pytest.fixture
async def server_err(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(device_status_err_handler, port=aiohttp_unused_port())


@pytest.fixture
async def server_invalid(aiohttp_raw_server, aiohttp_unused_port) -> BasicDevice:
    return await aiohttp_raw_server(device_status_invalid_handler, port=aiohttp_unused_port())


async def test_device_information_ok(server_ok: RawTestServer):
    device = BasicDevice(server_ok.host + ":" + str(server_ok.port))
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


async def test_device_all_information(server_ok: RawTestServer):
    device = BasicDevice(server_ok.host + ":" + str(server_ok.port))
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


async def test_device_information_error(server_err: RawTestServer):
    device = BasicDevice(server_err.host + ":" + str(server_err.port))
    loaded = await device.load_device_information()

    assert loaded is False
    assert device._error_code == "501"


async def test_device_information_invalid(server_invalid: RawTestServer):
    device = BasicDevice(server_invalid.host + ":" + str(server_invalid.port))
    loaded = await device.load_device_information()

    assert loaded is False
    assert device.error_code == "n/a"
    assert isinstance(device.error_exception is not None and device.error_exception.inner_exception, ValueError)


async def test_device_information_wrong_address():
    device = BasicDevice('localhost_wrong_host')
    loaded = await device.load_device_information()

    assert loaded is False
    assert device.error_code == "n/a"
    assert isinstance(device.error_exception.inner_exception, IOError)
