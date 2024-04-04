import asyncio
import random

from bleak import BleakScanner, BleakClient
from contextlib import AsyncExitStack
from functools import partial

evt = asyncio.Event()
devices = {}

#LVS_CTRL_UUID = "5A300002-0023-4BD4-BBD5-A6920E4C5653"
LVS_CTRL_UUID = "53300002-0023-4BD4-BBD5-A6920E4C5653"

DEV_COUNT = 1

tune = [
  [16, 2],
  [16, 2],
  [18, 2],
  [14, 3],
  [15, 1],
  [18, 2],

  [20, 2],
  [20, 2],
  [28, 2],
  [20, 3],
  [18, 1],
  [16, 2],

  [18, 2],
  [16, 2],
  [15, 2],
  [16, 3]
]


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
      for d in devices:
        client = BleakClient(devices[d])
        await stack.enter_async_context(client)

        print("connected " + str(client.address) + " " + str(client.is_connected))

        for note in tune:
          #level = random.randint(1,32)
          level = note[0]
          print("Setting level " + str(level))
          command = "Vibrate:" + str(level)
          command = bytes(command, 'utf-8')
          await client.write_gatt_char(LVS_CTRL_UUID, command, False)
          await asyncio.sleep(note[1] / 4)

          await client.write_gatt_char(LVS_CTRL_UUID, b'Vibrate:0', False)
          await asyncio.sleep(0.2)

        await client.write_gatt_char(LVS_CTRL_UUID, b'Vibrate:0', False)
        print("Stopped")

asyncio.run(main())


