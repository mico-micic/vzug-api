import locale

from datetime import datetime, timedelta
from typing import Dict, Any
from .basic_device import BasicDevice, DeviceError, read_kwh_from_string, read_float_from_string
from .const import ENDPOINT_HH, COMMAND_GET_PROGRAM

locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

COMMAND_VALUE_ECOM_STAT_TOTAL = 'ecomXstatXtotal'
COMMAND_VALUE_ECOM_STAT_AVG = 'ecomXstatXavarage'

PROGRAM_NAME = 'name'
PROGRAM_DURATION = 'duration'
PROGRAM_DURATION_ACT = 'act'
PROGRAM_STATUS = 'status'
PROGRAM_STATUS_IDLE = 'idle'
PROGRAM_OPTIDOS = 'optiDos'
PROGRAM_OPTIDOS_SET = 'set'
PROGRAM_OPTIDOS_DETERGENT_A_B = 'detergentAandB'
PROGRAM_OPTIDOS_FILL_LEVEL_A = 'fillLevelA'
PROGRAM_OPTIDOS_FILL_LEVEL_B = 'fillLevelB'
PROGRAM_OPTIDOS_FILL_LEVEL_ACT = 'act'

CONSUMPTION_DETAILS_VALUE = 'value'

REGEX_MATCH_LITER = r"(\d+(?:[\,\.]\d+)?).?ℓ"


def read_liter_from_string(consumption_value: str) -> float:
    liter = read_float_from_string(consumption_value, REGEX_MATCH_LITER)
    if liter < 0:
        raise DeviceError('Cannot find liter value in string {0}'.format(consumption_value), 'n/a')

    return liter


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

    def _reset_active_program_information(self) -> None:
        self._seconds_to_end = 0
        self._program_name = ""
        self._program_status = ""
        self._optidos_active = False
        self._optidos_config = ""

    async def load_all_information(self) -> bool:
        """Load consumption data and if a program is active load also the program details"""
        loaded = await super().load_all_information()
        if loaded:
            loaded = await self.load_consumption_data()
            if loaded and self.is_active:
                loaded = await self.load_program_details()
            else:
                # If no program is active only load the optiDos data. (Use same function because the optiDos
                # information is returned on the active program endpoint)
                loaded = await self.load_program_details(True)

        return loaded

    async def load_program_details(self, opti_dos_only: bool = False) -> bool:
        """Load program details information by calling the corresponding API endpoint"""

        self._logger.info("Loading program information for %s", self._host)

        self._reset_active_program_information()

        try:
            program_json = (await self.make_vzug_device_call_json(
                self.get_command_url(ENDPOINT_HH, COMMAND_GET_PROGRAM)))[0]

            self._program_status = program_json[PROGRAM_STATUS]

            # Load optiDos detailed information if optiDos is available / active
            # (optiDos may be available even if no program is active...)
            self._read_optidos_details(program_json)

            # Skip if only die optiDos data should be loaded
            if opti_dos_only:
                return True

            if PROGRAM_STATUS_IDLE in self._program_status:
                self._logger.info("No program information available because no program is active")
                return False

            self._program_name = program_json[PROGRAM_NAME]
            self._seconds_to_end = program_json[PROGRAM_DURATION][PROGRAM_DURATION_ACT]

            self._logger.info("Go program information. Active program: %s, minutes to end: %.0f, end time: %s",
                              self.program_name, self.seconds_to_end / 60, self.date_time_end)

            return True

        except DeviceError as e:
            self._error_code = e.error_code
            self._error_message = e.message
            self._error_exception = e
            return False

    def _read_optidos_details(self, program_json: Dict[Any, Any]) -> None:
        """Read optiDos information from given program response"""

        self._optidos_a_status = ""
        self._optidos_b_status = ""

        if PROGRAM_OPTIDOS_FILL_LEVEL_A in program_json:
            self._optidos_a_status = program_json[PROGRAM_OPTIDOS_FILL_LEVEL_A][PROGRAM_OPTIDOS_FILL_LEVEL_ACT]

        if PROGRAM_OPTIDOS_FILL_LEVEL_B in program_json:
            self._optidos_b_status = program_json[PROGRAM_OPTIDOS_FILL_LEVEL_B][PROGRAM_OPTIDOS_FILL_LEVEL_ACT]

        self._optidos_active = False
        if PROGRAM_OPTIDOS in program_json:
            self._optidos_config = program_json[PROGRAM_OPTIDOS][PROGRAM_OPTIDOS_SET]

            # TODO: Add support for other optiDos configurations
            if self._optidos_config == PROGRAM_OPTIDOS_DETERGENT_A_B:
                self._optidos_active = True
            else:
                self._logger.info("Unknown optiDos configuration / status")
        else:
            self._logger.info("optiDos is not active / available")

        self._logger.info("optiDos information: %s optiDos A status: %s, optiDos B status: %s",
                          self._optidos_config, self.optidos_a_status, self.optidos_b_status)

    async def load_consumption_data(self) -> bool:
        """Load power and water consumption data by calling the corresponding API endpoint"""

        self._logger.info("Loading power and water consumption data for %s", self._host)
        try:
            consumption_total = await self.do_consumption_details_request(COMMAND_VALUE_ECOM_STAT_TOTAL)
            self._power_consumption_kwh_total = read_kwh_from_string(consumption_total)
            self._water_consumption_l_total = read_liter_from_string(consumption_total)

            consumption_avg = await self.do_consumption_details_request(COMMAND_VALUE_ECOM_STAT_AVG)
            self._power_consumption_kwh_avg = read_kwh_from_string(consumption_avg)
            self._water_consumption_l_avg = read_liter_from_string(consumption_avg)

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

    def get_date_time_end(self, tz=None) -> datetime:
        return datetime.now(tz) + timedelta(seconds=self.seconds_to_end)

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
