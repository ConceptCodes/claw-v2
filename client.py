import socket
import time

host = "192.168.4.1"
port = 8889


def parse_state(resp):
    state = {}
    parts = resp.split(";")
    for part in parts:
        if ":" in part:
            key, value = part.split(":")
            state[key] = value
    return state


def send_command(command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    sock.sendto(command.encode(), (host, port))
    try:
        response, _ = sock.recvfrom(1024)
        decoded = response.decode()
        print(f"Response: {decoded}")
    except socket.timeout:
        print("No response from claw.")
    finally:
        sock.close()


# send_command("wakeup")
# time.sleep(1)

# Raise the first arm segment by 45°
send_command("arm1 inc 90")
time.sleep(1)
