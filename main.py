import wifi
import socket
import board
import pwmio
from adafruit_motor import servo
import adafruit_logging as logging

# Configure logging
logger = logging.getLogger("ClawRobot")
logger.setLevel(logging.ERROR)


# Custom exception classes
class InvalidCommandError(Exception):
    pass


class InvalidAngleError(Exception):
    pass


# Servo wrapper class for easier control
class Servo:
    def __init__(self, pin):
        self.pin = pin
        pwm = pwmio.PWMOut(pin, duty_cycle=2**15, frequency=50)
        self.servo = servo.Servo(pwm)

    def move(self, angle):
        # Move servo to specified angle if valid
        self.servo.angle = angle
        logging.info(f"Servo on pin {self.pin} moved to {angle} degrees.")

    def __repr__(self):
        return f"Servo(pin={self.pin})"


# UDP port for receiving commands
PORT = 8889
SDK_MODE_ENABLED = False  # Flag to enable SDK mode

# Define valid movement and base commands
movement_commands = [
    "raise",
    "lower",
    "rotate",
]
base_commands = ["wakeup", "grab", "release", "home", "state"]
valid_commands = movement_commands.extend(base_commands)

# Initialize servos on specified pins
base = Servo(board.D1)
arm = Servo(board.D2)
wrist = Servo(board.D3)
claw = Servo(board.D4)

# Setup WiFi Access Point with unique SSID based on MAC address
mac = wifi.radio.mac_address
ap_ssid = "Claw-" + "".join(f"{b:02x}" for b in mac)
wifi.radio.start_ap(ssid=ap_ssid, password="")
logging.info(f"Access Point started with SSID: {ap_ssid}")

# Create UDP socket and bind to port
socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind(("", PORT))
logging.info(f"Listening for UDP packets on port {PORT}...")


# Validate incoming command and angle
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


def home():
    # Move all servos to home position (0 degrees)
    base.move(0)
    arm.move(0)
    wrist.move(0)
    claw.move(0)
    logging.info("All servos moved to home position.")


def enable_sdk_mode():
    global SDK_MODE_ENABLED
    if not SDK_MODE_ENABLED:
        SDK_MODE_ENABLED = True
        logging.info("SDK Mode enabled. Claw will respond to commands.")
        home()  # Move to home position when SDK mode is enabled


def move_arm(angle):
    logging.info(f"Moving arm to angle: {angle}")
    arm.move(int(angle))


def rotate_base(angle):
    logging.info(f"Rotating base to angle: {angle}")
    base.move(int(angle))


def grab():
    logging.info("Grabbing with claw.")
    claw.move(180)


def release():
    logging.info("Releasing claw.")
    claw.move(0)


def get_state():
    state = f"base:{base.servo.angle};arm:{arm.servo.angle};wrist:{wrist.servo.angle};claw:{claw.servo.angle};"
    logging.info(f"Current state: {state}")
    return state


# Main loop: receive and process commands
while True:
    data, ip = socket.recvfrom(1024)
    datastr = "".join([chr(b) for b in data])
    logging.info(f"Received command: {datastr} from {ip}")

    try:
        command, angle = validate_command(datastr)
        logging.info(f"Command '{command}' is valid.")

        # Only process commands if the claw is awake
        if not SDK_MODE_ENABLED and command != "wakeup":
            raise InvalidCommandError("SDK Mode is not enabled.")

        # Map commands to servo actions
        switcher = {
            "wakeup": enable_sdk_mode,
            "home": home,
            "raise": move_arm,
            "lower": move_arm,
            "rotate": rotate_base,
            "grab": grab,
            "release": release,
            "state": get_state,
        }

        if command in switcher:
            if command in movement_commands:
                switcher[command](angle)
            else:
                switcher[command]()
        else:
            raise InvalidCommandError(f"Command '{command}' not implemented.")
        logging.info(f"Command '{command}' executed successfully.")

        response = bytearray()
        response.extend("OK")
        socket.sendto(response, ip)
    except (InvalidCommandError, InvalidAngleError) as e:
        logging.error(f"Error: {e}")
        response = bytearray()
        response.extend(f"Error: {e}")
        socket.sendto(response, ip)
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        response = bytearray()
        response.extend(f"Error: {e}")
        socket.sendto(response, ip)
