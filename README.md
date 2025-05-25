# Robot Claw Firmware

Inspired by the DJI Tello Drone SDK, this project aims to provide a similar, easy-to-use network-controlled experience for a robotic claw. The goal is to enable simple programming and interaction using clear, concise commands—making it accessible for both beginners and advanced users.

## Hardware

- **Claw Model:** [Robot Claw 3D Model](https://makerworld.com/en/models/1372133-big-robotic-armds3dmax-with-magnetic-gripper#profileId-1418848)  
  *(You can adapt the code for any servo-controlled robotic claw.)*
- **Microcontroller:** [ESP32-Feather](https://www.adafruit.com/product/3405)  
  *(Built-in WiFi for network control.)*
- **Servo Controller:** [8 Channel PWM Servo FeatherWing AddOn](https://www.adafruit.com/product/2928)  
  *(Controls the servos for the claw and arm.)*

## Network Configuration

- **WiFi Access Point:**  
  - SSID: `Claw-XX:XX:XX:XX:XX:XX` (where `XX:XX:XX:XX:XX:XX` is the MAC address)  
  - *No password required*
- **Device IP:** `192.168.10.1`
- **UDP Port:** `8889`

## Setup Instructions

1. Connect to the claw's WiFi access point.
2. Use any UDP client to send commands to `192.168.10.1:8889` as described below.

## Command Reference

| Command             | Description                               | Example           | Expected Response |
|---------------------|-------------------------------------------|-------------------| -------------------|
| `wakeup`            | Enter SDK mode                            | `wakeup`          | `OK`              |
| `rotate <angle>`    | Rotate base to specified angle (0–180)    | `rotate 90`       | `OK`              |
| `grab`              | Close the claw                            | `grab`            | `OK`              |
| `release`           | Open the claw                             | `release`         | `OK`              |
| `raise <angle>`     | Raise arm to specified angle (0–180)      | `raise 45`        | `OK`              |
| `lower <angle>`     | Lower arm to specified angle (0–180)      | `lower 135`       | `OK`              |
| `home`              | Move claw to home position                | `home`            | `OK`              |
| `state`             | Get current state of the claw             | `state`           | `base:<angle>;arm:<angle>;wrist:<angle>;claw:<angle>` |

> **Note:**  
> Replace `<angle>` with an integer between 0 and 180.

## Response Codes

- `OK` — Command executed successfully.
- `Error: <message>` — Command failed; `<message>` provides details.

## Example: Sending Commands with Python

You can use Python's `socket` library to interact with the claw:

```python
import socket
import time

def send_command(command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    sock.sendto(command.encode(), ('192.168.10.1', 8889))
    try:
        response, _ = sock.recvfrom(1024)
        decoded = response.decode()
        if decoded != "OK":
            print(f"Command failed: {decoded}")
    except socket.timeout:
        print("No response from claw.")
    finally:
        sock.close()

send_command('wakeup')
time.sleep(1)
send_command('rotate 90')
time.sleep(1)
```

---

Feel free to adapt the hardware or commands to suit your own robotic claw project!