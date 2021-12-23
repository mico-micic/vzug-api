import asyncio
from vzug import BasicDevice
import logconf

HOSTNAME_OR_IP = "192.168.0.202"
USERNAME = ""
PASSWORD = ""


async def main():

    logconf.setup_logging()

    device = BasicDevice(HOSTNAME_OR_IP, USERNAME, PASSWORD)
    await device.load_device_information()

    print("\n==== Device information")
    print("Model:", device.model_desc)
    print("Name:", device.device_name)
    print("Status:", device.status)
    print("Active:", device.is_active)

if __name__ == '__main__':
    asyncio.run(main())
