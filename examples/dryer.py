import asyncio
from vzug import Dryer
import logconf
import locale

locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

HOSTNAME_OR_IP = "192.168.1.6"
USERNAME = ""
PASSWORD = ""


async def main():
    logconf.setup_logging()

    device = Dryer(HOSTNAME_OR_IP, USERNAME, PASSWORD)
    await device.load_device_information()
    await device.load_program_details()
    await device.load_consumption_data()

    print("\n==== Device information")
    print("Model:", device.model_desc)
    print("Name:", device.device_name)
    print("Status:", device.status)
    print("Active:", device.is_active)

    print("\n==== Current Program")
    if device.is_active:
        print("Program name:", device.program_name)
        print("Program status:", device.program_status)
        print("End time:", device.date_time_end)
        print("Seconds to end:", device.seconds_to_end)
    else:
        print("No program active")

    print("\n==== Power Consumption")

    print(f"Power consumption total: {device.power_consumption_kwh_total}, avg: {device.power_consumption_kwh_avg}")

if __name__ == '__main__':
    asyncio.run(main())
