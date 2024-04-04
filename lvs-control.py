import asyncio
import random

from bleak import BleakScanner, BleakClient
from contextlib import AsyncExitStack
from functools import partial

evt = asyncio.Event()
devices = {}

LVS_HUSH_CTRL_UUID = "5A300002-0023-4BD4-BBD5-A6920E4C5653"
LVS_LUSH_CTRL_UUID = "53300002-0023-4BD4-BBD5-A6920E4C5653"
LVS_DOLCE_CTRL_UUID = "4A300002-0023-4BD4-BBD5-A6920E4C5653"

DEV_COUNT = 1

def detection_callback(device, advertisment_data):
  name = str(device.name)
  if name.startswith("LVS"):
    print(device)
    devices[name] = device
    if len(devices) == DEV_COUNT:
      evt.set()

async def main():
    print("Waiting for devices")
    async with BleakScanner(detection_callback):
      await evt.wait()

    print("Got all devices")
    async with AsyncExitStack() as stack:
      clients = []

      for d in devices:
        client = BleakClient(devices[d])
        await stack.enter_async_context(client)
        clients.append(client)

        print("connected " + str(client.address) + " " + str(client.is_connected))

      for _ in range(30):
        for c in clients:
          level = random.randint(1,32)
          print("Setting level on " + str(c) + " to " + str(level))
          command = "Vibrate:" + str(level)
          command = bytes(command, 'utf-8')
          await c.write_gatt_char(LVS_DOLCE_CTRL_UUID, command, False)
        await asyncio.sleep(0.5)

      for c in clients:
        await c.write_gatt_char(LVS_CTRL_UUID, b'Vibrate:0', False)
      print("Stopped")

asyncio.run(main())


