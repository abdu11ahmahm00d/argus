import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import yaml
from comms.serial_bridge import SerialBridge

SHORTCUTS = {
    "b": {"cmd": "BARRIER_DROP"},
    "r": {"cmd": "BARRIER_RAISE"},
    "f": {"cmd": "FLAG_RAISE"},
    "l": {"cmd": "FLAG_LOWER"},
    "L": {"cmd": "LASER_ON"},
    "o": {"cmd": "LASER_OFF"},
    "z": {"cmd": "BUZZ", "duration": 500},
    "1": {"cmd": "LED_RED", "mode": "on"},
    "2": {"cmd": "LED_GREEN", "mode": "on"},
    "0": {"cmd": "LED_OFF", "target": "all"},
    "p": {"cmd": "PING"},
    "x": {"cmd": "RESET"},
}


async def main():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    bridge = SerialBridge(
        port=config["serial"]["port"],
        baud=config["serial"]["baud"],
        timeout=config["serial"]["timeout"],
    )
    await bridge.connect()

    if not bridge.connected:
        print("Failed to connect. Check COM port and HC-05 pairing.")
        return

    print("=== ARGUS Serial Test ===")
    print("Type a JSON command, or use shortcuts:")
    print("  b=barrier drop  r=barrier raise  f=flag raise  l=flag lower")
    print("  L=laser on  o=laser off  z=buzz  p=ping  x=reset")
    print("  1=red LED on  2=green LED on  0=all LEDs off")
    print("  q=quit\n")

    loop = asyncio.get_event_loop()

    while True:
        inp = await loop.run_in_executor(None, input, ">>> ")

        if inp.lower() == "q":
            break

        if inp in SHORTCUTS:
            cmd = SHORTCUTS[inp]
        else:
            try:
                cmd = json.loads(inp)
            except json.JSONDecodeError:
                print("Invalid JSON. Try again.")
                continue

        ack = await bridge.send(cmd)
        if ack:
            print(f"ACK: {json.dumps(ack, indent=2)}")
        else:
            print("No ACK received (timeout)")

    await bridge.close()
    print("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())
