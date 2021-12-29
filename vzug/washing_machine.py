import json

import re
from .basic_device import BasicDevice, DeviceError
from datetime import datetime, timedelta
from .const import ENDPOINT_HH, COMMAND_GET_PROGRAM, COMMAND_GET_COMMAND
import locale

locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

COMMAND_VALUE_ECOM_STAT_TOTAL = 'ecomXstatXtotal'
COMMAND_VALUE_ECOM_STAT_AVG = 'ecomXstatXavarage'

REGEX_MATCH_LITER = r"(\d+(?:[\,\.]\d+)?).?ℓ"
REGEX_MATCH_KWH = r"(\d+(?:[\,\.]\d+)?).?kWh"


class WashingMachine(BasicDevice):
    """Class representing V-Zug washing machines"""

    def __init__(self, host: str, username: str = "", password: str = ""):
        super().__init__(host, username, password)
        self._seconds_to_end = 0
        self._program_name = ""
        self._program_status = ""
        self._optidos_active = False
        self._optidos_config = ""
        self._optidos_a_status = ""
        self._optidos_b_status = ""
        self._power_consumption_kwh_total = 0.0
        self._water_consumption_l_total = 0.0
        self._power_consumption_kwh_avg = 0.0
        self._water_consumption_l_avg = 0.0

    def _reset_program_information(self) -> None:
        self._seconds_to_end = 0
        self._program_name = ""
        self._program_status = ""
        self._optidos_active = False
        self._optidos_config = ""
        self._optidos_a_status = ""
        self._optidos_b_status = ""

    async def load_all_information(self) -> bool:
        """Load consumption data and if a program is active load also the program details"""
        loaded = await super().load_all_information()
        if loaded:
            loaded = await self.load_consumption_data()
            if loaded and self.is_active:
                loaded = await self.load_program_details()

        return loaded

    async def load_program_details(self) -> bool:
        """Load program details information by calling the corresponding API endpoint"""

        self._logger.info("Loading program information for %s", self._host)

        self._reset_program_information()
        try:
            program_json = (await self.make_vzug_device_call_json(
                self.get_command_url(ENDPOINT_HH, COMMAND_GET_PROGRAM)))[0]

            self._program_status = program_json['status']

            # Load optiDos detailed information if optiDos is available / active
            # (optiDos may be available even if no program is active...)
            self._read_optidos_details(program_json)

            if 'active' not in self._program_status:
                self._logger.info("No program information available because no program is active")
                return False

            self._program_name = program_json['name']
            self._seconds_to_end = program_json['duration']['act']

            self._logger.info("Go program information. Active program: %s, minutes to end: %.0f, end time: %s",
                              self.program_name, self.seconds_to_end / 60, self.date_time_end)

            return True

        except DeviceError as e:
            self._error_code = e.error_code
            self._error_message = e.message
            self._error_exception = e
            return False

    def _read_optidos_details(self, program_json: json) -> None:
        """Read optiDos information from given program response"""

        if 'fillLevelA' in program_json:
            self._optidos_a_status = program_json['fillLevelA']['act']

        if 'fillLevelB' in program_json:
            self._optidos_b_status = program_json['fillLevelB']['act']

        self._optidos_active = False
        if 'optiDos' in program_json:
            self._optidos_config = program_json['optiDos']['set']

            # TODO: Add support for other optiDos configurations
            if self._optidos_config == "detergentAandB":
                self._optidos_active = True
            else:
                self._logger.info("Unknown optiDos configuration / status")
        else:
            self._logger.info("optiDos is not active / available")

        self._logger.info("optiDos information: %s optiDos A status: %s, optiDos B status: %s",
                          self._optidos_config, self.optidos_a_status, self.optidos_b_status)

    async def _do_consumption_details_request(self, command: str) -> str:

        url = self.get_command_url(ENDPOINT_HH, COMMAND_GET_COMMAND).update_query({'value': command})
        eco_json = await self.make_vzug_device_call_json(url)

        if 'value' in eco_json:
            return eco_json['value']
        else:
            self._logger.error('Error reading power and water consumption, no \'value\' entry found in response.')
            raise DeviceError('Got invalid response while reading power and water consumption data.', 'n/a')

    async def load_consumption_data(self) -> bool:
        """Load power and water consumption data by calling the corresponding API endpoint"""

        self._logger.info("Loading power and water consumption data for %s", self._host)
        try:
            consumption_total = await self._do_consumption_details_request(COMMAND_VALUE_ECOM_STAT_TOTAL)
            self._power_consumption_kwh_total = self._read_kwh_from_string(consumption_total)
            self._water_consumption_l_total = self._read_liter_from_string(consumption_total)

            consumption_avg = await self._do_consumption_details_request(COMMAND_VALUE_ECOM_STAT_AVG)
            self._power_consumption_kwh_avg = self._read_kwh_from_string(consumption_avg)
            self._water_consumption_l_avg = self._read_liter_from_string(consumption_avg)

            self._logger.info("Power consumption total: %s kWh, avg: %.1f kWh",
                              locale.format_string('%.0f', self._power_consumption_kwh_total, True),
                              self._power_consumption_kwh_avg)

            self._logger.info("Water consumption total: %s l, avg: %.0f l",
                              locale.format_string('%.0f', self._water_consumption_l_total, True),
                              self._water_consumption_l_avg)

        except DeviceError as e:
            self._error_code = e.error_code
            self._error_message = e.message
            self._error_exception = e
            return False

        return True

    @staticmethod
    def _read_float_from_string(consumption_value: str, regex: str) -> float:
        match = re.search(regex, consumption_value)
        if match:
            return float(match.group(1).replace(',', '.'))

        return -1

    def _read_liter_from_string(self, consumption_value: str) -> float:
        liter = self._read_float_from_string(consumption_value, REGEX_MATCH_LITER)
        if liter < 0:
            raise DeviceError('Cannot find liter value in string %s'.format(consumption_value), 'n/a')

        return liter

    def _read_kwh_from_string(self, consumption_value: str) -> float:
        kwh = self._read_float_from_string(consumption_value, REGEX_MATCH_KWH)
        if kwh < 0:
            raise DeviceError('Cannot find kWh value in string %s'.format(consumption_value), 'n/a')

        return kwh

    @property
    def program_status(self) -> str:
        return self._program_status

    @property
    def program_name(self) -> str:
        return self._program_name

    @property
    def optidos_active(self) -> bool:
        return self._optidos_active

    @property
    def optidos_a_status(self) -> str:
        return self._optidos_a_status

    @property
    def optidos_b_status(self) -> str:
        return self._optidos_b_status

    @property
    def seconds_to_end(self) -> int:
        return self._seconds_to_end

    @property
    def date_time_end(self) -> datetime:
        return datetime.now() + timedelta(seconds=self.seconds_to_end)

    @property
    def power_consumption_kwh_total(self) -> float:
        return self._power_consumption_kwh_total

    @property
    def power_consumption_kwh_avg(self) -> float:
        return self._power_consumption_kwh_avg

    @property
    def water_consumption_l_total(self) -> float:
        return self._water_consumption_l_total

    @property
    def water_consumption_l_avg(self) -> float:
        return self._water_consumption_l_avg
