import asyncio
import pygame
from bleak import BleakScanner, BleakClient
from contextlib import AsyncExitStack
from functools import partial

HR_NOTIFY_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

evt = asyncio.Event()
hr_devices = {}

pygame.init()
screen = pygame.display.set_mode((800, 600))
GAME_FONT = pygame.freetype.SysFont("Courier", 48)
running =  True

heart_rates = {}

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

clock=pygame.time.Clock()

def detection_callback(device, advertisment_data):
  name = str(device.name)
  if name.startswith("RHYTHM"):
    print("Found heart monitor " + name)
    hr_devices[name] = device
    if len(hr_devices) == 2:
      evt.set()

def notify_callback(device, sender, data):
    hr = data[1]
    if hr != 0:
      heart_rates[device] = hr

async def run_buetooth():
    print("Starting bluetooth, looking for devices")
    async with BleakScanner(detection_callback):
      await evt.wait()

    evt.clear()

    async with AsyncExitStack() as stack:
      for d in hr_devices:
        client = BleakClient(hr_devices[d])
        await stack.enter_async_context(client)

        print("Device connected " + str(client.address))
        await client.start_notify(HR_NOTIFY_UUID, partial(notify_callback, hr_devices[d]))

      await evt.wait()

def display_string(n):
    return "Heart rate: " + str(n)

loop.create_task(run_buetooth())

while running:
  clock.tick(30)

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False

  # Draw the screen
  screen.fill((255,255,255))
  y = 100
  for hr in heart_rates:
    GAME_FONT.render_to(screen, (100, y), display_string(heart_rates[hr]), (0, 0, 0))
    y = y + 50
  pygame.display.flip()

  # Run the async eveny loop once
  loop.call_soon(loop.stop)
  loop.run_forever()

# Run all tasks until they exit
evt.set()
while len(asyncio.all_tasks(loop)):
  loop.call_soon(loop.stop)
  loop.run_forever()

# Shut down the async loop
loop.run_until_complete(loop.shutdown_asyncgens())
loop.close()

pygame.quit()


