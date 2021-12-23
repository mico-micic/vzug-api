import asyncio
from vzug import BasicDevice, WashingMachine
import logconf


async def main():
    logconf.setup_logging()


   # device = BasicDevice("192.168.0.202")
   # await device.load_device_information()

    device = WashingMachine("192.168.0.202")
    await device.load_program_details()

    device = WashingMachine("192.168.0.202")
    await device.load_consumption_data()

if __name__ == '__main__':
    asyncio.run(main())
