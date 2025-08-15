#!/usr/bin/env python3
# Yeelight Classic LAN CLI: auto-discover/select IP, set color and brightness.
import argparse, json, os, socket, time, ipaddress, sys

UDP_GRP = "239.255.255.250"; UDP_PORT = 1982
TCP_PORT = 55443; EOL = b"\r\n"; BUF = 65535

def send_call(ip, method, params, mid=1, timeout=4.0, verbose=False):
    s = socket.create_connection((ip, TCP_PORT), timeout=timeout)
    s.settimeout(timeout)
    try:
        payload = json.dumps({"id": mid, "method": method, "params": params}).encode() + EOL
        if verbose: print("[send]", payload.decode().rstrip())
        s.sendall(payload)
        deadline = time.time() + timeout
        buf = b""
        while time.time() < deadline:
            try:
                chunk = s.recv(BUF)
            except socket.timeout:
                continue
            if not chunk: break
            buf += chunk
            frames = [f for f in buf.split(EOL) if f]
            if buf.endswith(EOL): buf = b""
            for f in frames:
                raw = f.decode(errors="ignore")
                if verbose: print("[recv]", raw)
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                if msg.get("id") == mid:
                    return msg
        raise TimeoutError("no reply before deadline")
    finally:
        s.close()

def discover(timeout=1.5, verbose=False):
    """SSDP-like discovery (fast)"""
    msg = ("M-SEARCH * HTTP/1.1\r\n"
           f"HOST: {UDP_GRP}:{UDP_PORT}\r\n"
           'MAN: "ssdp:discover"\r\n'
           "ST: wifi_bulb\r\n\r\n").encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(timeout); s.bind(("", 0))
    s.sendto(msg, (UDP_GRP, UDP_PORT))
    found = {}
    end = time.time() + timeout
    while time.time() < end:
        try:
            data, _ = s.recvfrom(BUF)
        except socket.timeout:
            break
        txt = data.decode(errors="ignore")
        if verbose: print("--- DISCOVERY ---\n", txt)
        headers = {}
        for line in txt.split("\r\n")[1:]:
            if ":" in line:
                k, v = line.split(":", 1); headers[k.strip().lower()] = v.strip()
        loc = headers.get("location") or headers.get("Location")
        _id = headers.get("id"); model = headers.get("model"); power = headers.get("power"); bright = headers.get("bright")
        if loc and _id and loc.startswith("yeelight://"):
            host = loc.split("://",1)[1].split(":")[0]
            found[_id] = {"id":_id,"ip":host,"model":model,"power":power,"bright":bright}
    return list(found.values())

def local_ips():
    """Parse Windows ipconfig for active IPv4s (skip APIPA)."""
    ips=[]
    for line in os.popen("ipconfig").read().splitlines():
        line=line.strip()
        if line.startswith("IPv4 Address") or line.startswith("IPv4-adres"):
            ip=line.split(":")[-1].strip()
            if ip and not ip.startswith("169.254."): ips.append(ip)
    return ips

def scan_subnet(timeout=0.25, verbose=False):
    """Fallback: TCP scan /24 for port 55443 and verify with get_prop."""
    devices=[]
    for ip in local_ips():
        net = ipaddress.ip_interface(ip + "/24").network
        if verbose: print(f"Scanning {net} ...")
        for host in net.hosts():
            h=str(host)
            try:
                sock=socket.create_connection((h,TCP_PORT),timeout=timeout)
                sock.close()
                # verify it is Yeelight
                try:
                    r = send_call(h,"get_prop",["power","bright","ct","name"],mid=1,timeout=1.0,verbose=False)
                    if "result" in r:
                        devices.append({"id":f"{h}", "ip":h, "model":"?", "power":r["result"][0], "bright":r["result"][1]})
                except Exception:
                    pass
            except Exception:
                pass
    return devices

def pick_device(devs):
    if len(devs)==1: return devs[0]["ip"]
    print("Multiple bulbs found:")
    for i,d in enumerate(devs,1):
        print(f"[{i}] ip={d['ip']} model={d.get('model')} power={d.get('power')} bright={d.get('bright')}")
    while True:
        sel = input("Select number: ").strip()
        if sel.isdigit():
            idx=int(sel)
            if 1<=idx<=len(devs): return devs[idx-1]["ip"]

def parse_rgb(s):
    s = s.strip().lstrip("#"); return int(s,16)

def main():
    ap = argparse.ArgumentParser(description="Yeelight LAN control: auto-select IP, set color and brightness")
    ap.add_argument("--ip", help="Bulb IP (skip discovery)")
    ap.add_argument("--rgb", help="Hex color like FF9900 or #FF9900")
    ap.add_argument("--bright", type=int, help="Brightness 1..100")
    ap.add_argument("--on", action="store_true", help="Ensure power on")
    ap.add_argument("--off", action="store_true", help="Power off")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    # resolve IP
    target_ip = args.ip
    if not target_ip:
        devs = discover(timeout=1.5, verbose=args.verbose)
        if not devs:
            devs = scan_subnet(verbose=args.verbose)
        if not devs:
            print("No bulbs found. Use --ip <addr>.")
            sys.exit(1)
        target_ip = pick_device(devs)

    # actions
    mid=1
    if args.off:
        print(send_call(target_ip,"set_power",["off","smooth",300],mid=mid,verbose=args.verbose)); mid+=1
        return

    if args.on:
        print(send_call(target_ip,"set_power",["on","smooth",300],mid=mid,verbose=args.verbose)); mid+=1

    if args.bright is not None:
        b = max(1, min(100, int(args.bright)))
        print(send_call(target_ip,"set_bright",[b,"smooth",300],mid=mid,verbose=args.verbose)); mid+=1

    if args.rgb:
        rgb = parse_rgb(args.rgb)
        print(send_call(target_ip,"set_rgb",[rgb,"smooth",300],mid=mid,verbose=args.verbose)); mid+=1

    if args.rgb is None and args.bright is None and not args.on and not args.off:
        # default: show props
        print(send_call(target_ip,"get_prop",["power","bright","ct","rgb","hue","sat","color_mode","name"],mid=mid,verbose=args.verbose))

if __name__ == "__main__":
    main()

# Auto-discover and set orange at 70%:
# py yeelight_cli.py --on --rgb FF9900 --bright 70

# Direct IP with only brightness change:
# py yeelight_cli.py --ip 192.168.0.156 --bright 30

# Turn off:
# py yeelight_cli.py --ip 192.168.0.156 --off
