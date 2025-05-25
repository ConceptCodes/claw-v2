import socket
import time

host = "192.168.4.1"
port = 8889

def send_command(command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    sock.sendto(command.encode(), (host, port))
    try:
        response, addr = sock.recvfrom(1024)
        decoded = response.decode()
        print(f"decoded: {decoded} from addr: {addr}")
        if decoded != "OK":
            print(f"Command failed: {decoded}")
    except socket.timeout:
        print("No response from claw.")
    finally:
        sock.close()


send_command("wakeup")
time.sleep(1)
# send_command("rotate 90")
# time.sleep(1)
