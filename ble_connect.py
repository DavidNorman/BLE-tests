import asyncio
from bleak import BleakScanner, BleakClient
from contextlib import AsyncExitStack
from functools import partial

evt = asyncio.Event()
devices = {}

def detection_callback(device, advertisment_data):
  name = str(device.name)
  if name.startswith("RHYTHM"):
    print(device)
    devices[name] = device
    if len(devices) == 2:
      evt.set()

def notify_callback(device, sender, data):
    hr = data[1]
    print(f"{device}: {sender}: {data[0]}, {hr}")

async def main():
    async with BleakScanner(detection_callback):
      await evt.wait()

    async with AsyncExitStack() as stack:
      for d in devices:
        client = BleakClient(devices[d])
        await stack.enter_async_context(client)

        print("connected " + str(client.address) + " " + str(client.is_connected))
        await client.start_notify("00002a37-0000-1000-8000-00805f9b34fb", partial(notify_callback, devices[d]))

      await asyncio.sleep(10000)

asyncio.run(main())


