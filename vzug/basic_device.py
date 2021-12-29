from distutils.util import strtobool
import json

import aiohttp
import logging
from .const import (COMMAND_GET_STATUS, COMMAND_GET_MODEL_DESC, ENDPOINT_AI, VERSION)
from yarl import URL
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_log

from .digest_auth import DigestAuth

REQUEST_HEADERS = {
    f"User-Agent": f"vzug-lib/{VERSION}",
    "Accept": f"application/json, text/plain, */*",
}


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
    def inner_exception(self) -> Exception:
        return self._inner_exception


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
        self._status_json = json
        self._program = ""
        self._error_code = ""
        self._error_message = ""
        self._error_exception = None
        self._uuid = ""
        self._active = False
        self._device_information_loaded = False
        self._logger = logging.getLogger(__name__)

    def get_base_url(self) -> URL:
        return URL.build(scheme='http', host=self._host)

    def get_command_url(self, endpoint: str, command: str) -> URL:
        return self.get_base_url().join(URL(endpoint)).update_query({'command': command})

    async def make_vzug_device_call_raw(self, url: URL) -> str:
        """
        Make raw service call to any V-Zug device and return the response as text
        """

        async with aiohttp.ClientSession() as session:
            try:
                self._logger.debug("Raw service call URL: %s", str(url))

                auth = DigestAuth(self._username, self._password, session)
                resp = await auth.request('GET', url=url, headers=REQUEST_HEADERS)

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
    async def make_vzug_device_call_json(self, url: URL) -> json:
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

            self._device_information_loaded = True

            self._logger.info("Go device information. Model: %s, Serial: %s, Uuid: %s, name: %s, Status text: %s",
                              self._model_desc, self._serial, self._uuid, self._device_name, self._status)
            return True

        except DeviceError as e:
            self._error_code = e.error_code
            self._error_message = e.message
            self._error_exception = e
            return False

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
    def status_json(self) -> json:
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
    def error_exception(self) -> DeviceError:
        return self._error_exception

    @property
    def device_information_loaded(self) -> bool:
        return self._device_information_loaded

    @property
    def uuid(self) -> str:
        return self._uuid
