import asyncio
import pygame
from bleak import BleakScanner, BleakClient
from contextlib import AsyncExitStack
from functools import partial

HR_NOTIFY_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
#LVS_HUSH_CTRL_UUID = "5A300002-0023-4BD4-BBD5-A6920E4C5653"
LVS_LUSH_CTRL_UUID = "53300002-0023-4BD4-BBD5-A6920E4C5653"

evt = asyncio.Event()
hr_devices = []
vibe_devices = []
vibe_level = []
heart_rates = []
vibe_clients = []
delay_counters = []

PLAYER_COUNT = 2
HEART_THESHOLD = 120
RED_THRESHOLLD = 110

pygame.init()
screen = pygame.display.set_mode((600, 600))
SMALL_GAME_FONT = pygame.freetype.SysFont("Courier", 48)
BIG_GAME_FONT = pygame.freetype.SysFont("Courier", 128)
running =  True

pygame.mixer.init()
sound = pygame.mixer.Sound('alarm.wav')

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

clock=pygame.time.Clock()

def hr_to_vibe(hr):
  if hr < 60:
    return 1
  elif hr < HEART_THRESHOLD:
    return (hr-60) / 3 + 1
  else:
    return 0

async def game_logic(player, opponent, now):
  new_level = 0
  if delay_counters[player] > now:
    new_level = hr_to_vibe(heart_rates[player])

  if vibe_level[player] > 0 and new_level == 0:
    delay_counters[player] = now + 10.0

  if new_level != vibe_level[player]:
    vibe_level[player] = new_level
    command = "Vibrate:" + str(new_level)
    command = bytes(command, 'utf-8')
    await vibe_clients[opponent].write_gatt_char(LVS_LUSH_CTRL_UUID, command, False)

def detection_callback(device, advertisment_data):
  name = str(device.name)
  if name.startswith("RHYTHM") and device not in hr_devices:
    print("Found heart monitor " + name)
    hr_devices.append(device)
  if name.startswith("LVS") and device not in vibe_devices:
    print("Found vibrator " + name)
    vibe_devices.append(device)

  if not running or len(hr_devices) == PLAYER_COUNT and len(vibe_devices) == PLAYER_COUNT:
    evt.set()

def hr_notify_callback(device, sender, data):
    hr = data[1]
    if hr != 0:
      heart_rates[device] = hr

async def run_buetooth():
    print("Starting bluetooth, looking for devices")
    async with BleakScanner(detection_callback):
      await evt.wait()

    evt.clear()

    if not running:
      return

    print("Devices found")

    async with AsyncExitStack() as stack:
      for n,d in enumerate(hr_devices):
        client = BleakClient(d)
        await stack.enter_async_context(client)

        print("Heart rate device connected " + str(client.address))
        await client.start_notify(HR_NOTIFY_UUID, partial(hr_notify_callback, n))

      for d in vibe_devices:
        client = BleakClient(d)
        await stack.enter_async_context(client)
        vibe_clients.append(client)
        vibe_level.append(-1)

        print("Vibrator connected " + str(client.address) + " " + str(client.is_connected))

      # This is the core game logic
      while running:
          now = time.time()

          game_logic(0, 1, now)
          game_logic(1, 0, now)

          await asyncio.sleep(0)
          
      for c in vibe_clients:
        await c.write_gatt_char(LVS_LUSH_CTRL_UUID, b'Vibrate:0', False)

# Initialise game state
for _ in range(PLAYER_COUNT):
  heart_rates.append(-1)
  delay_counters.append(0)

loop.create_task(run_buetooth())

while running:
  clock.tick(30)

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False

  # Draw the screen
  screen.fill((255,255,255))

  if len(vibe_devices) == 0 and len(hr_devices) == 0:
    SMALL_GAME_FONT.render_to(screen, (5, 100), "Turn on vibe 1", (0, 0, 0))

  elif len(vibe_devices) == 1 and len(hr_devices) == 0:
    SMALL_GAME_FONT.render_to(screen, (5, 100), "Turn on HR monitor 1", (0, 0, 0))

  elif len(vibe_devices) == 1 and len(hr_devices) == 1:
    SMALL_GAME_FONT.render_to(screen, (5, 100), "Turn on vibe 2", (0, 0, 0))

  elif len(vibe_devices) == 2 and len(hr_devices) == 1:
    SMALL_GAME_FONT.render_to(screen, (5, 100), "Turn on HR monitor 2", (0, 0, 0))

  elif len(vibe_devices) == 2 and len(heart_rates) == 2:
    col = (0, 0, 0) if heart_rates[0] < RED_THRESHOLD else (255, 0, 0)
    SMALL_GAME_FONT.render_to(screen, (80, 100), "Player 1", (0, 0, 0))
    BIG_GAME_FONT.render_to(screen, (100, 200), str(heart_rates[0]), (0, 0, 0))
    col = (0, 0, 0) if heart_rates[1] < RED_THRESHOLD else (255, 0, 0)
    SMALL_GAME_FONT.render_to(screen, (320, 100), "Player 2", (0, 0, 0))
    BIG_GAME_FONT.render_to(screen, (340, 200), str(heart_rates[1]), (0, 0, 0))

  else:
    running = False

  pygame.display.flip()

  # Run the async eveny loop once
  loop.call_soon(loop.stop)
  loop.run_forever()

# Run all tasks until they exit
while len(asyncio.all_tasks(loop)):
  loop.call_soon(loop.stop)
  loop.run_forever()

# Shut down the async loop
loop.run_until_complete(loop.shutdown_asyncgens())
loop.close()

pygame.quit()

