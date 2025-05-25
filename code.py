import wifi
import socketpool
import adafruit_logging as logging
from adafruit_servokit import ServoKit

# Setup Logging
logger = logging.getLogger("ClawRobot")
logger.setLevel(logging.ERROR)


# Custom exceptions
class InvalidCommandError(Exception):
    pass


class InvalidAngleError(Exception):
    pass


# Initialize ServoKit for 8 channels on PCA9685
kit = ServoKit(channels=8)

# Command definitions
movement_commands = ["raise", "lower", "rotate"]
base_commands = ["wakeup", "grab", "release", "home", "state"]
valid_commands = movement_commands + base_commands

PORT = 8889
SDK_MODE_ENABLED = False

# WiFi AP setup
mac = wifi.radio.mac_address
ap_ssid = "Claw-" + "".join(f"{b:02x}" for b in mac)
wifi.radio.start_ap(ssid=ap_ssid, password="", max_connections=1)
logger.info(f"Access Point started with SSID: {ap_ssid}")

udp_host = str(wifi.radio.ipv4_address)
pool = socketpool.SocketPool(wifi.radio)
sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
sock.bind((udp_host, PORT))

def home():
    for ch in range(4):
        kit.servo[ch].angle = 0
    logger.info("All servos moved to home position.")


def move_arm(angle):
    kit.servo[1].angle = int(angle)
    kit.continuous_servo[1].throttle = 1


def rotate_base(angle):
    kit.servo[0].angle = int(angle)
    kit.continuous_servo[1].throttle = 1


def grab():
    kit.servo[3].angle = 180
    kit.continuous_servo[1].throttle = 1


def release():
    kit.servo[3].angle = 0
    kit.continuous_servo[1].throttle = 1


def get_state():
    return ";".join(
        f"{name}:{kit.servo[idx].angle}"
        for idx, name in enumerate(["base", "arm", "wrist", "claw"])
    )


def enable_sdk_mode():
    global SDK_MODE_ENABLED
    SDK_MODE_ENABLED = True
    logger.info("SDK Mode enabled.")


def validate_command(command):
    parts = command.split()
    tmp = parts[0]
    angle = parts[1] if len(parts) > 1 else None

    if tmp not in valid_commands:
        raise InvalidCommandError(f"Invalid command: {tmp}")

    if tmp in movement_commands and (
        angle is None or not angle.isdigit() or not (0 <= int(angle) <= 180)
    ):
        raise InvalidAngleError(f"Invalid angle for command {tmp}: {angle}")

    return tmp, angle


# Main loop (UDP)
while True:
    data, addr = sock.recvfrom_into(1024)
    datastr = data.decode().strip()
    logger.info(f"Received: {datastr} from {addr}")

    try:
        cmd, angle = validate_command(datastr)
        if not SDK_MODE_ENABLED and cmd != "wakeup":
            raise InvalidCommandError("SDK Mode is not enabled.")
        cmd_map = {
      "wakeup": enable_sdk_mode,
      "home": home,
      "raise": move_arm,
      "lower": move_arm,
      "rotate": rotate_base,
      "grab": grab,
      "release": release,
      "state": get_state,
    }
        if cmd in movement_commands:
            cmd_map[cmd](angle)
            resp = "OK"
        else:
            resp = cmd_map[cmd]()
        sock.sendto(str(resp).encode(), addr)
    except (InvalidCommandError, InvalidAngleError) as e:
        logger.error(e)
        sock.sendto(f"Error: {e}".encode(), addr)
    except Exception as e:
        logger.exception(e)
        sock.sendto(f"Error: {e}".encode(), addr)
