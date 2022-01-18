import locale

from datetime import datetime, timedelta
from .basic_device import BasicDevice, DeviceError, read_kwh_from_string
from .const import ENDPOINT_HH, COMMAND_GET_PROGRAM

locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

CMD_VALUE_CONSUMP_DRYER_TOTAL = 'TotalXconsumptionXdrumDry'
CMD_VALUE_CONSUMP_DRYER_AVG = 'AverageXperXcycleXdrumDry'

PROGRAM_NAME = 'name'
PROGRAM_DURATION = 'duration'
PROGRAM_DURATION_ACT = 'act'
PROGRAM_STATUS = 'status'
PROGRAM_STATUS_IDLE = 'idle'

REGEX_MATCH_LITER = r"(\d+(?:[\,\.]\d+)?).?ℓ"
REGEX_MATCH_KWH = r"(\d+(?:[\,\.]\d+)?).?kWh"


class Dryer(BasicDevice):
    """Class representing V-Zug dryers"""

    def __init__(self, host: str, username: str = "", password: str = ""):
        super().__init__(host, username, password)
        self._seconds_to_end = 0
        self._program_name = ""
        self._program_status = ""
        self._power_consumption_kwh_total = 0.0
        self._power_consumption_kwh_avg = 0.0

    def _reset_active_program_information(self) -> None:
        self._seconds_to_end = 0
        self._program_name = ""
        self._program_status = ""
        
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

        self._reset_active_program_information()

        try:
            program_json = (await self.make_vzug_device_call_json(
                self.get_command_url(ENDPOINT_HH, COMMAND_GET_PROGRAM)))[0]

            self._program_status = program_json[PROGRAM_STATUS]
            
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

    async def load_consumption_data(self) -> bool:
        """Load power consumption data by calling the corresponding API endpoint"""

        self._logger.info("Loading power consumption data for %s", self._host)
        try:
            consumption_total = await self.do_consumption_details_request(CMD_VALUE_CONSUMP_DRYER_TOTAL)
            self._power_consumption_kwh_total = read_kwh_from_string(consumption_total)

            consumption_avg = await self.do_consumption_details_request(CMD_VALUE_CONSUMP_DRYER_AVG)
            self._power_consumption_kwh_avg = read_kwh_from_string(consumption_avg)
            
            self._logger.info("Power consumption total: %s kWh, avg: %.1f kWh",
                              locale.format_string('%.0f', self._power_consumption_kwh_total, True),
                              self._power_consumption_kwh_avg)

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
