import asyncio
from vzug import Dishwasher
import logconf
import locale
import sys

locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

# First parameter must be the device IP address
HOSTNAME_OR_IP = sys.argv[1]
USERNAME = ""
PASSWORD = ""


async def main():
    logconf.setup_logging()

    device = Dishwasher(HOSTNAME_OR_IP, USERNAME, PASSWORD)
    await device.load_device_information()
    await device.load_program_details()

    print("\n==== Device information")
    print("Type:", device.device_type)
    print("Model:", device.model_desc)
    print("Name:", device.device_name)
    print("Status:", device.status)
    print("Active:", device.is_active)

    print("\n==== Current Program")
    if device.is_active:
        print("Program name:", device.program_name)
        print("Program status:", device.program_status)

        if device.program_status == 'timed':
            print("Start time:", device.date_time_start)
            print("Seconds to start:", device.seconds_to_start)

        print("End time:", device.date_time_end)
        print("Seconds to end:", device.seconds_to_end)

        print("Energy saving:", device.is_energy_saving)
        print("Opti start:", device.is_opti_start)
        print("Partialload:", device.is_partialload)
        print("Rinse plus:", device.is_rinse_plus)
        print("Dry plus:", device.is_dry_plus)
    else:
        print("No program active")

if __name__ == '__main__':
    asyncio.run(main())
