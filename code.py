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
DEFAULT_RESPONSE = "OK"

# WiFi AP setup
mac = wifi.radio.mac_address
ap_ssid = "Claw-" + "".join(f"{b:02x}" for b in mac)
wifi.radio.start_ap(ssid=ap_ssid, password="", max_connections=1)
logger.info(f"Access Point started with SSID: {ap_ssid}")

ip_addr = str(wifi.radio.ipv4_address_ap)
pool = socketpool.SocketPool(wifi.radio)
sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
sock.bind((ip_addr, PORT))
logger.info(f"Listening on {ip_addr}:{PORT}")


BASE = kit.servo[0]
ARM_L = kit.servo[1]
ARM_R = kit.servo[2]
CLAW = kit.servo[3]
WRIST = kit.servo[4]


def home():
    for ch in range(4):
        kit.servo[ch].angle = 0
    logger.info("All servos moved to home position.")


def move_arm(angle):
    ARM_L.angle = int(angle)


def move_wrist(angle):
    WRIST.angle = int(angle)


def rotate_base(angle):
    BASE.angle = int(angle)


def grab():
    CLAW.angle = 180


def release():
    CLAW.angle = 0


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


def encode_response(res):
    resp = bytearray()
    resp.extend(res)
    return resp

# Main loop (UDP)
udp_buffer = bytearray(1024)
while True:
    n_bytes, addr = sock.recvfrom_into(udp_buffer)
    datastr = bytes(udp_buffer[:n_bytes]).decode().strip()
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
        resp = None
        if cmd in movement_commands:
            resp = cmd_map[cmd](angle)
        else:
            resp = cmd_map[cmd]()

        res = encode_response(resp if resp is not None else DEFAULT_RESPONSE)
        sock.sendto(res, addr)
    except (InvalidCommandError, InvalidAngleError) as e:
        logger.error(e)
        res = encode_response(e)
        sock.sendto(res, addr)
    except Exception as e:
        logger.exception(e)
        res = encode_response(e)
        sock.sendto(res, addr)
