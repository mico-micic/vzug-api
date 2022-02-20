from __future__ import annotations

import re
import json
import aiohttp
import aiohttp.web
import logging

from distutils.util import strtobool
from typing import Optional, Any, Dict
from yarl import URL
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_log
from .const import (QUERY_PARAM_COMMAND, QUERY_PARAM_VALUE, COMMAND_GET_STATUS, COMMAND_GET_MODEL_DESC,
                    COMMAND_GET_MACHINE_TYPE, ENDPOINT_AI, VERSION, DEVICE_TYPE_UNKNOWN, DEVICE_TYPE_MAPPING,
                    ENDPOINT_HH, COMMAND_GET_COMMAND)
from .digest_auth import DigestAuth

REQUEST_HEADERS = {
    f"User-Agent": f"vzug-lib/{VERSION}",
    "Accept": f"application/json, text/plain, */*",
}

CONSUMPTION_DETAILS_VALUE = 'value'
REGEX_MATCH_KWH = r"(\d+(?:[\,\.]\d+)?).?kWh"


def read_kwh_from_string(value_str: str) -> float:
    kwh = read_float_from_string(value_str, REGEX_MATCH_KWH)
    if kwh < 0:
        raise DeviceError('Cannot find kWh value in string {0}'.format(value_str), 'n/a')

    return kwh


def read_float_from_string(value_str: str, regex: str) -> float:
    match = re.search(regex, value_str)
    if match:
        return float(match.group(1).replace(',', '.'))

    return -1


class DeviceAuthError(Exception):
    """Exception thrown if there is an authentication problem."""


class DeviceError(Exception):
    def __init__(self, message, err_code: str, inner_exception: Exception = None):
        super().__init__(message)
        self._device_err_code = err_code
        self._message = message
        self._inner_exception = inner_exception

    @property
    def error_code(self) -> str:
        return self._device_err_code

    @property
    def message(self) -> str:
        return self._message

    @property
    def inner_exception(self) -> Exception | None:
        return self._inner_exception

    @property
    def is_auth_problem(self) -> bool:
        return isinstance(self.inner_exception, DeviceAuthError)


class BasicDevice:
    """Class containing basic functions valid to any V-ZUG device"""

    def __init__(self, host: str, username: str = "", password: str = "") -> None:
        self._host = host
        self._username = username
        self._password = password
        self._serial = ""
        self._model_desc = ""
        self._device_name = ""
        self._status = ""
        self._status_json: Dict[Any, Any] = {}
        self._program = ""
        self._error_code = ""
        self._error_message = ""
        self._error_exception: Optional[DeviceError] = None
        self._uuid = ""
        self._active = False
        self._device_information_loaded = False
        self._device_type_short = ""
        self._device_type: Optional[str] = DEVICE_TYPE_UNKNOWN
        self._logger = logging.getLogger(__name__)
        self._auth_previous: Dict[str, str] = {}

    def get_base_url(self) -> URL:
        return URL.build(scheme='http', host=self._host.replace("http://", ""))

    def get_command_url(self, endpoint: str, command: str) -> URL:
        return self.get_base_url().join(URL(endpoint)).update_query({QUERY_PARAM_COMMAND: command})

    async def make_vzug_device_call_raw(self, url: URL) -> str:
        """
        Make raw service call to any V-Zug device and return the response as text
        """

        async with aiohttp.ClientSession() as session:
            try:
                self._logger.debug("Raw service call URL: %s", str(url))

                auth = DigestAuth(self._username, self._password, session, self._auth_previous)
                resp = await auth.request('GET', url=url, headers=REQUEST_HEADERS)
                self._auth_previous = {
                    'nonce_count': auth.nonce_count,
                    'last_nonce': auth.last_nonce,
                    'challenge': auth.challenge,
                }

                if aiohttp.web.HTTPUnauthorized.status_code == resp.status:
                    err_msg = "Authentication problem occurred while calling device API"
                    self._logger.error(err_msg)
                    raise DeviceError(err_msg, "n/a", DeviceAuthError())

                txt_resp = await resp.read()
                self._logger.debug("Raw response from %s: status %s, text: %s", self._host, resp.status, txt_resp)
                return txt_resp.decode("utf-8")

            except IOError as e:
                err_msg = "IOError while calling device API"
                self._logger.error("%s: %s", err_msg, str(e))
                raise DeviceError(err_msg, "n/a", e)

    @retry(stop=stop_after_attempt(3),
           wait=wait_fixed(2),
           retry=retry_if_exception_type(DeviceError),
           before=before_log(logging.getLogger(__name__), logging.DEBUG),
           reraise=True)
    async def make_vzug_device_call_json(self, url: URL) -> Dict:
        """
        Make service call for any V-Zug device and check if there is an error code in json response.
        Sometimes the devices returns an internal error (like 503). In this case DeviceError exception
        is raised after 3 retries.
        """

        try:
            text_resp = str(await self.make_vzug_device_call_raw(url))

            json_resp = json.loads(text_resp)
            if "error" in json_resp:
                err_code = json_resp['error']['code']
                self._logger.error("Device returned error code: %s", err_code)
                raise DeviceError("Device returned error code", err_code)
            return json_resp

        except ValueError as e:
            err_msg = "Got invalid response from device"
            self._logger.error("%s: %s", err_msg, str(e))
            raise DeviceError(err_msg, "n/a", e)

    async def load_all_information(self) -> bool:
        """
        For the basic device forward the call to load_device_information().
        Method can be overridden by subclasses to load device specific
        information.
        """
        return await self.load_device_information()

    async def load_device_information(self) -> bool:
        """Load device status information by calling the corresponding API endpoint"""

        try:
            self._logger.info("Loading device information for %s", self._host)
            self._status_json = await self.make_vzug_device_call_json(
                self.get_command_url(ENDPOINT_AI, COMMAND_GET_STATUS))

            self._error_code = ""
            self._serial = self._status_json['Serial']
            self._device_name = self._status_json['DeviceName']
            self._status = self._status_json['Status']
            self._uuid = self._status_json['deviceUuid']
            self._program = self._status_json['Program']
            self._active = not strtobool(self._status_json['Inactive'])

            # Load model description in separate call
            self._model_desc = await self.make_vzug_device_call_raw(
                self.get_command_url(ENDPOINT_AI, COMMAND_GET_MODEL_DESC))

            # Load short device type in separate call
            self._device_type_short = await self.make_vzug_device_call_raw(
                self.get_command_url(ENDPOINT_HH, COMMAND_GET_MACHINE_TYPE))

            self._set_device_type()
            self._device_information_loaded = True

            self._logger.info("Got device information. Type: %s, model: %s, serial: %s, uuid: %s, name: %s, status: %s",
                              self.device_type, self.model_desc, self.serial, self.uuid, self.device_name, self.status)
            return True

        except DeviceError as e:
            self._error_code = e.error_code
            self._error_message = e.message
            self._error_exception = e
            return False

    def _set_device_type(self) -> None:
        if self._device_type_short in DEVICE_TYPE_MAPPING:
            self._device_type = DEVICE_TYPE_MAPPING.get(self._device_type_short)
        else:
            self._device_type = DEVICE_TYPE_UNKNOWN

    async def do_consumption_details_request(self, command: str) -> str:

        url = self.get_command_url(ENDPOINT_HH, COMMAND_GET_COMMAND).update_query({QUERY_PARAM_VALUE: command})
        eco_json = await self.make_vzug_device_call_json(url)

        if CONSUMPTION_DETAILS_VALUE in eco_json:
            return eco_json[CONSUMPTION_DETAILS_VALUE]
        else:
            self._logger.error('Error reading consumption data, no \'value\' entry found in response.')
            raise DeviceError('Got invalid response while reading consumption data.', 'n/a')

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def device_name(self) -> str:
        return self._device_name

    @property
    def model_desc(self) -> str:
        return self._model_desc

    @property
    def status(self) -> str:
        return self._status

    @property
    def status_json(self) -> Any:
        return self._status_json

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def program(self) -> str:
        return self._program

    @property
    def error_code(self) -> str:
        return self._error_code

    @property
    def error_message(self) -> str:
        return self._error_message

    @property
    def error_exception(self) -> Optional[DeviceError]:
        return self._error_exception

    @property
    def device_information_loaded(self) -> bool:
        return self._device_information_loaded

    @property
    def device_type(self) -> Optional[str]:
        return self._device_type

    @property
    def uuid(self) -> str:
        return self._uuid
