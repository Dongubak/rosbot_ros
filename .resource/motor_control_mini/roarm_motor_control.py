"""RoArm-M2 Motor Control via HTTP"""

import requests
import json

CONTROLLER_IP = "192.168.0.44"
BASE_URL = f"http://{CONTROLLER_IP}/js"


def send_command(command: dict) -> dict:
    resp = requests.get(BASE_URL, params={"json": json.dumps(command)}, timeout=5)
    resp.raise_for_status()
    return resp.json()


def move(x: float, z: float) -> dict:
    """Move the arm with X and Z values."""
    return send_command({"T": 13, "X": x, "Z": z})


if __name__ == "__main__":
    x = float(input("X: "))
    z = float(input("Z: "))
    print(f"Moving to X={x}, Z={z}...")
    result = move(x, z)
    print(f"Response: {result}")
g