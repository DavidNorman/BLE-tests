import asyncio
from bleak import BleakScanner

evt = asyncio.Event()
devices = {}

def detection_callback(device, advertisment_data):
  name = str(device.name)
  print(device)
  devices[name] = device

async def main():
    async with BleakScanner(detection_callback):
      await asyncio.sleep(30)

asyncio.run(main())

