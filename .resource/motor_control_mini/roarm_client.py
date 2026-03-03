"""RoArm-M2 Python Client - WiFi Info Example"""

import requests
import json

CONTROLLER_IP = "192.168.0.44"
BASE_URL = f"http://{CONTROLLER_IP}/js"


def send_command(command: dict) -> dict:
    """Send a JSON command to the RoArm-M2 controller and return the response."""
    resp = requests.get(BASE_URL, params={"json": json.dumps(command)}, timeout=5)
    resp.raise_for_status()
    return resp.json()


def get_wifi_info() -> dict:
    """Get WiFi information (T:405)."""
    return send_command({"T": 405})


def get_motor_status() -> dict:
    """Get motor status (T:130)."""
    return send_command({"T": 130})


if __name__ == "__main__":
    print("=== RoArm-M2 WiFi Info ===")
    wifi = get_wifi_info()
    print(f"  IP:        {wifi['ip']}")
    print(f"  MAC:       {wifi['mac']}")
    print(f"  RSSI:      {wifi['rssi']} dBm")
    print(f"  STA SSID:  {wifi['sta_ssid']}")
    print(f"  AP SSID:   {wifi['ap_ssid']}")
    print(f"  WiFi Mode: {wifi['wifi_mode_on_boot']}")

    print("\n=== Motor Status ===")
    status = get_motor_status()
    print(f"  M1: {status['M1']}, M2: {status['M2']}, M3: {status['M3']}, M4: {status['M4']}")
    print(f"  ODL: {status['odl']}, ODR: {status['odr']}")
    print(f"  Voltage: {status['v']}")
