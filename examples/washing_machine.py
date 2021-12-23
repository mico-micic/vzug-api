import asyncio
from vzug import WashingMachine
import logconf
import locale

locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

HOSTNAME_OR_IP = "192.168.0.202"
USERNAME = ""
PASSWORD = ""


async def main():
    logconf.setup_logging()

    device = WashingMachine(HOSTNAME_OR_IP, USERNAME, PASSWORD)
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
        print("End time:", device.date_time_end)
        print("Seconds to end:", device.seconds_to_end)

        if device.optidos_active:
            print("optiDos: active")
    else:
        print("No program active")

    print("\n==== optiDos Status")
    print("optiDos A status:", device.optidos_a_status)
    print("optiDos B status:", device.optidos_b_status)

    print("\n==== Power / Water Consumption")

    power_total = locale.format_string('%.0f', device.power_consumption_kwh_total, True)
    print(f"Power consumption total: {power_total} kWh, avg: {device.power_consumption_kwh_avg:.1f} kWh")

    water_total = locale.format_string('%.0f', device.water_consumption_l_total, True)
    print(f"Water consumption total: {water_total} l, avg: {device.water_consumption_l_avg:.0f} l")

if __name__ == '__main__':
    asyncio.run(main())
