#!/usr/bin/env python3
import argparse, json, socket, time

PORT = 55443
EOL = b"\r\n"
BUF = 65535

def send_call(ip, method, params, mid=1, timeout=3.0):
    s = socket.create_connection((ip, PORT), timeout=timeout)
    s.settimeout(timeout)
    try:
        payload = json.dumps({"id": mid, "method": method, "params": params}).encode() + EOL
        s.sendall(payload)
        deadline = time.time() + timeout
        buf = b""
        while time.time() < deadline:
            try:
                chunk = s.recv(BUF)
            except socket.timeout:
                continue
            if not chunk:
                break
            buf += chunk
            frames = [f for f in buf.split(EOL) if f]
            if buf.endswith(EOL):
                buf = b""
            for f in frames:
                raw = f.decode(errors="ignore")
                # print all frames for visibility
                print(raw)
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                if msg.get("id") == mid:
                    return msg
        raise TimeoutError("no reply before deadline")
    finally:
        s.close()

def parse_rgb(s):
    s = s.strip().lstrip("#")
    return int(s, 16)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Set Yeelight color via LAN")
    ap.add_argument("ip", help="Bulb IP, e.g. 192.168.0.156")
    ap.add_argument("rgb", help="Hex RGB, e.g. FF0000 or #FF9900")
    ap.add_argument("--effect", choices=["smooth","sudden"], default="smooth")
    ap.add_argument("--duration", type=int, default=300, help="transition ms")
    ap.add_argument("--on", action="store_true", help="ensure power on first")
    args = ap.parse_args()

    if args.on:
        send_call(args.ip, "set_power", ["on", args.effect, args.duration], mid=1)

    rgb_int = parse_rgb(args.rgb)
    send_call(args.ip, "set_rgb", [rgb_int, args.effect, args.duration], mid=2)


# #!/usr/bin/env python3
# import argparse
# import json
# import socket

# BUF = 65535
# EOL = b"\r\n"

# def set_rgb(ip, rgb, effect="smooth", duration=300):
#     # Connect to the bulb
#     with socket.create_connection((ip, 55443), timeout=3.0) as s:
#         cmd = {
#             "id": 1,
#             "method": "set_rgb",
#             "params": [rgb, effect, duration]
#         }
#         payload = json.dumps(cmd) + "\r\n"
#         s.sendall(payload.encode())
#         data = s.recv(BUF).decode(errors="ignore")
#         print("[recv]", data.strip())

# if __name__ == "__main__":
#     p = argparse.ArgumentParser(description="Set Yeelight bulb RGB color via LAN control")
#     p.add_argument("ip", help="Bulb IP address")
#     p.add_argument("rgb", help="Color in hex (e.g. FF0000 for red, 00FF00 for green)")
#     p.add_argument("--duration", type=int, default=300, help="Transition duration in ms")
#     p.add_argument("--effect", default="smooth", choices=["smooth", "sudden"], help="Transition effect")
#     args = p.parse_args()

#     # Convert hex string to integer
#     try:
#         rgb_int = int(args.rgb, 16)
#     except ValueError:
#         raise SystemExit("Invalid RGB format. Use hex like FF0000.")

#     set_rgb(args.ip, rgb_int, args.effect, args.duration)

#py yeelight_color.py 192.168.0.156 FF9900
# PS C:\Windows\System32> '{"id":1,"method":"get_prop","params":["power","bright","ct","name"]}' | ncat 192.168.0.156 55443
# {"id":1,"result":["on","50","5053",""]}
# PS C:\Windows\System32> '{"id":2,"method":"set_power","params":["on","smooth",300]}'           | ncat 192.168.0.156 55443
# {"id":2,"result":["ok"]}
# PS C:\Windows\System32>
# PS C:\Windows\System32> '{"id":1,"method":"get_prop","params":["power","bright","ct","rgb","hue","sat","color_mode","name"]}' | ncat 192.168.0.156 55443
# {"id":1,"result":["on","70","5000","16750848","36","100","1",""]}
# PS C:\Windows\System32> '{"id":2,"method":"set_rgb","params":[16750848,"smooth",300]}' | ncat 192.168.0.156 55443
# {"id":2,"result":["ok"]}
# PS C:\Windows\System32> '{"id":3,"method":"set_bright","params":[70,"smooth",300]}'     | ncat 192.168.0.156 55443
# {"id":3,"result":["ok"]}