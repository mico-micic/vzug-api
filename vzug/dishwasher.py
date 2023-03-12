import locale

from datetime import datetime, timedelta
from .basic_device import BasicDevice, DeviceError, read_kwh_from_string
from .const import ENDPOINT_HH, COMMAND_GET_PROGRAM

locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

PROGRAM_NAME = 'name'
PROGRAM_DURATION = 'duration'
PROGRAM_ENERGY_SAVING = 'energySaving'
PROGRAM_OPTI_START = 'optiStart'
PROGRAM_PARTIALLOAD = 'partialload' 
PROGRAM_RINSE_PLUS = 'rinsePlus'
PROGRAM_DRY_PLUS = 'dryPlus'
PROGRAM_DURATION_ACT = 'act'
PROGRAM_DURATION_SET = 'set'
PROGRAM_STATUS = 'status'
PROGRAM_STATUS_IDLE = 'idle'
PROGRAM_STATUS_TIMED = 'timed'
PROGRAM_INFORMATION_SET = 'set'
PROGRAM_STARTTIME = 'starttime'
PROGRAM_STARTTIME_SET = 'set'

REGEX_MATCH_LITER = r"(\d+(?:[\,\.]\d+)?).?ℓ"
REGEX_MATCH_KWH = r"(\d+(?:[\,\.]\d+)?).?kWh"


class Dishwasher(BasicDevice):
    """Class representing V-Zug dishwashers"""

    def __init__(self, host: str, username: str = "", password: str = ""):
        super().__init__(host, username, password)
        self._seconds_to_end = 0
        self._seconds_to_start = 0
        self._program_duration = 0
        self._program_name = ""
        self._program_status = ""
        self._is_energy_saving = False
        self._is_opti_start = False
        self._is_partialload = False
        self._is_rinse_plus = False
        self._is_dry_plus = False

    def _reset_active_program_information(self) -> None:
        self._seconds_to_end = 0
        self._seconds_to_start = 0
        self._program_duration = 0
        self._program_name = ""
        self._program_status = ""
        self._is_energy_saving = False
        self._is_opti_start = False
        self._is_partialload = False
        self._is_rinse_plus = False
        self._is_dry_plus = False
        
    async def load_all_information(self) -> bool:
        """Load consumption data and if a program is active load also the program details"""
        loaded = await super().load_all_information()
        if loaded:
            
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

            if PROGRAM_STATUS_TIMED in self._program_status:
                self._program_duration = program_json[PROGRAM_DURATION][PROGRAM_DURATION_SET]
                self._seconds_to_start = program_json[PROGRAM_STARTTIME][PROGRAM_STARTTIME_SET]
                self._seconds_to_end = self._seconds_to_start + self._program_duration
            else:
                self._seconds_to_end = program_json[PROGRAM_DURATION][PROGRAM_DURATION_ACT]

            self._program_name = program_json[PROGRAM_NAME]
            self._is_energy_saving = program_json[PROGRAM_ENERGY_SAVING][PROGRAM_INFORMATION_SET]
            self._is_opti_start = program_json[PROGRAM_OPTI_START][PROGRAM_INFORMATION_SET]
            self._is_partialload = program_json[PROGRAM_PARTIALLOAD][PROGRAM_INFORMATION_SET]
            self._is_rinse_plus = program_json[PROGRAM_RINSE_PLUS][PROGRAM_INFORMATION_SET]
            self._is_dry_plus = program_json[PROGRAM_DRY_PLUS][PROGRAM_INFORMATION_SET]

            self._logger.info("Go program information. Active program: %s, minutes to end: %.0f, end time: %s",
                              self.program_name, self.seconds_to_end / 60, self.date_time_end)

            return True

        except DeviceError as e:
            self._error_code = e.error_code
            self._error_message = e.message
            self._error_exception = e
            return False

    @property
    def program_status(self) -> str:
        return self._program_status

    @property
    def program_name(self) -> str:
        return self._program_name

    @property
    def is_energy_saving(self) -> bool:
        return self._is_energy_saving

    @property
    def is_opti_start(self) -> bool:
        return self._is_opti_start

    @property
    def is_partialload(self) -> bool:
        return self._is_partialload

    @property
    def is_rinse_plus(self) -> bool:
        return self._is_rinse_plus

    @property
    def is_dry_plus(self) -> bool:
        return self._is_dry_plus

    @property
    def seconds_to_end(self) -> int:
        return self._seconds_to_end

    @property
    def seconds_to_start(self) -> int:
        return self._seconds_to_start

    @property
    def program_duration(self) -> int:
        return self._program_duration

    @property
    def date_time_end(self) -> datetime:
        return datetime.now() + timedelta(seconds=self.seconds_to_end)

    @property
    def date_time_start(self) -> datetime:
        return datetime.now() + timedelta(seconds=self.seconds_to_start)

    def get_date_time_end(self, tz=None) -> datetime:
        return datetime.now(tz) + timedelta(seconds=self.seconds_to_end)

    def get_date_time_start(self, tz=None) -> datetime:
        return datetime.now(tz) + timedelta(seconds=self.seconds_to_start)
