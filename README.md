# Robot Claw Firmware

Inspired by the DJI Tello Drone, this project aims to provide a similar, easy-to-use network-controlled experience, but for a robotic claw. The goal is to enable simple programming and interaction using clear, concise commands. Making it accessible for both beginners and advanced users. 

## Hardware

- **Claw Model:** [Robot Claw 3D Model](https://makerworld.com/en/models/1372133-big-robotic-armds3dmax-with-magnetic-gripper#profileId-1418848)  
  *(You can adapt the code for any servo-controlled robotic claw.)*
- **Micro Controller:** [ESP32 S2 Feather](https://www.adafruit.com/product/5000)  
  *(Built-in WiFi for network control.)*
- **Servo Controller:** [8 Channel PWM Servo FeatherWing AddOn](https://www.adafruit.com/product/2928)  
  *(Controls the servos for the claw and arm.)*

## Network Configuration

- **WiFi Access Point:**  
  - SSID: `Claw-XX:XX:XX:XX:XX:XX` (where `XX:XX:XX:XX:XX:XX` is the MAC address)  
  - *No password required*
- **Device IP:** `192.168.4.1`
- **UDP Port:** `8889`

## Setup Instructions

1. Flash the firmware onto the ESP32 S2 Feather using [Circuit Pythons Web Installer](https://circuitpython.org/board/adafruit_feather_esp32s2/).
2. Power on the claw and wait for it to boot. The device should show up as a USB drive named `CIRCUITPY`.
   - If you don't see the drive, ensure the device is in bootloader mode by holding the reset button while connecting it to your computer.
3. Move the code.py and libraries folder to the root of the CIRCUITPY drive.
4. Disconnect the USB cable and power the claw using a suitable battery or power supply.
5. Connect to the claw's WiFi access point.
5. Use any UDP client to send commands to `192.168.4.1:8889` as described below.

## Command Reference

| Command                     | Description                                                    | Example               | Expected Response                               |
|-----------------------------|----------------------------------------------------------------|-----------------------|-------------------------------------------------|
| `base set <angle>`          | Rotate the base to an absolute angle (0–180)                   | `base set 45`         | `OK`                                            |
| `base inc <angle>`          | Rotate the base +<angle> degrees (clamped 0–180)               | `base inc 15`         | `OK`                                            |
| `base dec <angle>`          | Rotate the base –<angle> degrees (clamped 0–180)               | `base dec 20`         | `OK`                                            |
| `arm1 set <angle>`          | Move arm segment 1 to an absolute angle (0–180)                | `arm1 set 90`         | `OK`                                            |
| `arm1 inc <angle>`          | Move arm1 +<angle> degrees (clamped 0–180)                     | `arm1 inc 10`         | `OK`                                            |
| `arm1 dec <angle>`          | Move arm1 –<angle> degrees (clamped 0–180)                     | `arm1 dec 15`         | `OK`                                            |
| `arm2 set <angle>`          | Move arm segment 2 to an absolute angle (0–180)                | `arm2 set 120`        | `OK`                                            |
| `arm2 inc <angle>`          | Move arm2 +<angle> degrees (clamped 0–180)                     | `arm2 inc 5`          | `OK`                                            |
| `arm2 dec <angle>`          | Move arm2 –<angle> degrees (clamped 0–180)                     | `arm2 dec 30`         | `OK`                                            |
| `wrist set <angle>`         | Tilt the wrist to an absolute angle (0–180)                    | `wrist set 60`        | `OK`                                            |
| `wrist inc <angle>`         | Tilt wrist +<angle> degrees (clamped 0–180)                    | `wrist inc 20`        | `OK`                                            |
| `wrist dec <angle>`         | Tilt wrist –<angle> degrees (clamped 0–180)                    | `wrist dec 10`        | `OK`                                            |
| `claw open`                 | Open the claw fully (sets claw to 180°)                        | `claw open`           | `OK`                                            |
| `claw close`                | Close the claw fully (sets claw to 0°)                         | `claw close`          | `OK`                                            |
| `home`                      | Move all servos to home positions (base/arms/wrist → 90°, claw → 0°) | `home`                | `OK`                                            |
| `state`                     | Query current positions of all servos                          | `state`               | `base:45;arm1:100;arm2:125;wrist:80;claw:180`   |
                                                  

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

HOST = '192.168.4.1'
PORT = 8889

def send_command(command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    sock.sendto(command.encode(), (HOST, PORT))
    try:
        response, _ = sock.recvfrom(1024)
        print(f"> {command!r}  →  {response.decode()}")
    except socket.timeout:
        print(f"> {command!r}  →  No response")
    finally:
        sock.close()

# “Wake up” the claw (enable SDK mode)
send_command('wakeup')
time.sleep(1)

# Center all joints
send_command('home')        
time.sleep(1)

# Rotate the base to 90°
send_command('base set 90')
time.sleep(1)

# Raise the first arm segment by 45°
send_command('arm1 inc 45')
time.sleep(1)

# Open and then close the claw
send_command('claw open')
time.sleep(0.5)
send_command('claw close')

```

**Device Logs**
```
19.905: INFO - Access Point started with SSID: Claw-70041df18f38
19.908: INFO - Listening on 192.168.4.1:8889

```
---

Feel free to adapt the hardware or commands to suit your own robotic claw project!

## Roadmap
- [x] Enhance commands 
- [ ] Add a web interface for easier control