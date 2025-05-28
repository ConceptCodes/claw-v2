import wifi
import socketpool
import adafruit_logging as logging
from adafruit_servokit import ServoKit

logger = logging.getLogger("ClawRobot")
logger.setLevel(logging.INFO)


class InvalidCommandError(Exception):
    pass


class InvalidAngleError(Exception):
    pass


kit = ServoKit(channels=8)

PORT = 8889
SDK_MODE_ENABLED = False
DEFAULT_RESPONSE = "OK"

COMPONENTS = {
    "base": kit.servo[0],
    "arm1": kit.servo[1],
    "arm2": kit.servo[2],
    "wrist": kit.servo[3],
    "claw": kit.servo[4],
}

current_angles = {
    "base": 90,
    "arm1": 90,
    "arm2": 90,
    "wrist": 90,
    "claw": 0,
}


mac = wifi.radio.mac_address
ap_ssid = "Claw-" + "".join(f"{b:02x}" for b in mac)
wifi.radio.start_ap(ssid=ap_ssid, password="", max_connections=1)
logger.info(f"Access Point started with SSID: {ap_ssid}")

ip_addr = str(wifi.radio.ipv4_address_ap)
pool = socketpool.SocketPool(wifi.radio)
sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
sock.bind((ip_addr, PORT))
logger.info(f"Listening on {ip_addr}:{PORT}")


def home():
    for name, servo in COMPONENTS.items():
        angle = 0 if name == "claw" else 90
        servo.angle = angle
        current_angles[name] = angle
    logger.info("All servos moved to home position.")


def get_state():
    return ";".join(f"{name}:{current_angles[name]}" for name in COMPONENTS)


def enable_sdk_mode():
    global SDK_MODE_ENABLED
    SDK_MODE_ENABLED = True
    logger.info("SDK Mode enabled.")


def parse_command(request: str):
    parts = request.lower().strip().split()
    cmd = parts[0] if parts else ""

    if cmd in ("state", "wakeup", "home"):
        return (cmd,)
    
    if cmd not in COMPONENTS:
        raise InvalidCommandError(f"Unknown component: {cmd}")
    action = parts[1] if len(parts) > 1 else None

    if cmd == "claw" and action in ("open", "close"):
        angle = 180 if action == "open" else 0
        return ("set", cmd, angle)

    if action in ("set", "inc", "dec") and len(parts) == 3:
        try:
            val = int(parts[2])
        except ValueError:
            raise InvalidAngleError(f"Invalid angle value: {parts[2]}")
        if not (0 <= val <= 180):
            raise InvalidAngleError(f"Angle out of range: {val}")
        return (action, cmd, val)

    raise InvalidCommandError(
        "Syntax error: use '<component> set|inc|dec <0 - 180>' or 'claw open|close' or 'state'"
    )


def execute_command(cmd_tuple):
    typ = cmd_tuple[0]
    if typ == "state":
        return get_state()

    _, comp, val = cmd_tuple
    servo = COMPONENTS[comp]

    if typ == "set":
        new_angle = val
    else:
        delta = val if typ == "inc" else -val
        new_angle = max(0, min(180, current_angles[comp] + delta))

    servo.angle = new_angle
    current_angles[comp] = new_angle
    logger.info(f"{comp} {typ} → {new_angle}")


def encode_response(res):
    resp = bytearray()
    resp.extend(str(res))
    return resp


udp_buffer = bytearray(1024)
while True:
    n_bytes, addr = sock.recvfrom_into(udp_buffer)
    data = bytes(udp_buffer[:n_bytes]).decode().strip()
    logger.info(f"Received: {data} from {addr}")

    try:
        if not SDK_MODE_ENABLED:
            raise InvalidCommandError("SDK Mode is not enabled.")

        parsed = parse_command(data)

        result = DEFAULT_RESPONSE
        if parsed[0] == "wakeup":
            enable_sdk_mode()
        elif parsed[0] == "home":
            home()
        else:
            result = execute_command(parsed)

        sock.sendto(encode_response(result), addr)

    except (InvalidCommandError, InvalidAngleError) as e:
        logger.error(e)
        sock.sendto(encode_response(f"Error: {e}"), addr)

    except Exception as e:
        logger.exception(e)
        sock.sendto(encode_response(f"Error: {e}"), addr)
