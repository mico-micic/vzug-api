import json

from .basic_device import BasicDevice, DeviceError
from datetime import datetime, timedelta
from .const import ENDPOINT_HH, COMMAND_GET_PROGRAM


class WashingMachine(BasicDevice):
    """Class representing V-Zug washing machines"""

    def __init__(self, host: str):
        super().__init__(host)
        self._seconds_to_end = 0
        self._program_name = ""
        self._program_status = ""
        self._optidos_active = False
        self._optidos_config = ""
        self._optidos_a_status = ""
        self._optidos_b_status = ""

    def _reset_program_information(self) -> None:
        self._seconds_to_end = 0
        self._program_name = ""
        self._program_status = ""
        self._optidos_active = False
        self._optidos_config = ""
        self._optidos_a_status = ""
        self._optidos_b_status = ""

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
                              self.program_name, self.seconds_to_end/60, self.date_time_end)

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
