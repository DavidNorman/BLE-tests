import asyncio
from bleak import BleakScanner, BleakClient
from contextlib import AsyncExitStack
from functools import partial

evt = asyncio.Event()
devices = {}

def detection_callback(device, advertisment_data):
  name = str(device.name)
  if name.startswith("Simon"):
    print(device)
    devices[name] = device
    if len(devices) == 1:
      evt.set()

async def main():
    async with BleakScanner(detection_callback):
      await evt.wait()

    async with AsyncExitStack() as stack:
      for d in devices:
        client = BleakClient(devices[d])
        await stack.enter_async_context(client)

        print("connected " + str(client.address) + " " + str(client.is_connected))

        for s in client.services:
          print("service: i" + str(s))

          for c in s.characteristics:
            print("  characteristic: " + str(c))


      await asyncio.sleep(10000)

asyncio.run(main())


