#!/usr/bin/env python3
import argparse, json, socket, time

MCAST_GRP = "239.255.255.250"; MCAST_PORT = 1982
TCP_PORT_DEFAULT = 55443; BUF = 65535; EOL = b"\r\n"

VERBOSE = False
def vprint(*a): 
    if VERBOSE: print(*a)

def discover(timeout=2.0):
    msg = ("M-SEARCH * HTTP/1.1\r\n"
           f"HOST: {MCAST_GRP}:{MCAST_PORT}\r\n"
           'MAN: "ssdp:discover"\r\n'
           "ST: wifi_bulb\r\n\r\n").encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(timeout); s.bind(("", 0))
    s.sendto(msg, (MCAST_GRP, MCAST_PORT))
    seen = {}
    end = time.time() + timeout
    while time.time() < end:
        try:
            data, _ = s.recvfrom(BUF)
        except socket.timeout:
            break
        if VERBOSE: print("--- DISCOVERY REPLY ---\n", data.decode(errors="ignore"))
        headers = {}
        for line in data.decode(errors="ignore").split("\r\n")[1:]:
            if ":" in line:
                k, v = line.split(":", 1); headers[k.strip().lower()] = v.strip()
        if "id" in headers and "location" in headers:
            seen[headers["id"]] = headers
    return list(seen.values())

class YeelightBulb:
    def __init__(self, host, port=TCP_PORT_DEFAULT, timeout=3.0):
        self.host, self.port, self.timeout = host, port, timeout
        self._sock = None; self._next_id = 1

    def connect(self):
        if self._sock: return
        s = socket.create_connection((self.host, self.port), timeout=self.timeout)
        s.settimeout(self.timeout); self._sock = s
        vprint(f"[connect] TCP {self.host}:{self.port}")

    def close(self):
        if self._sock:
            try: self._sock.close()
            finally: self._sock = None

    def _recv_frames_until(self, want_id, deadline):
        buf = b""
        while time.time() < deadline:
            try:
                chunk = self._sock.recv(BUF)
            except socket.timeout:
                continue
            if not chunk: break
            buf += chunk
            frames = [f for f in buf.split(EOL) if f]
            if buf.endswith(EOL): buf = b""
            for f in frames:
                raw = f.decode(errors="ignore")
                vprint("[recv]", raw)
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                # ignore notifications (no id)
                if "id" in msg and (want_id is None or msg["id"] == want_id):
                    return msg
        raise TimeoutError("no reply before deadline")

    def call(self, method, params):
        if not self._sock: self.connect()
        mid = self._next_id; self._next_id += 1
        obj = {"id": mid, "method": method, "params": params}
        payload = json.dumps(obj, separators=(",", ":")).encode() + EOL
        vprint("[send]", payload.decode().rstrip())
        self._sock.sendall(payload)
        return self._recv_frames_until(mid, time.time() + 4.0)

    # helpers
    def get_prop(self, props): return self.call("get_prop", props)
    def set_power(self, on, effect="smooth", duration_ms=300, mode=None):
        p = ["on" if on else "off", effect, int(duration_ms)]
        if mode is not None: p.append(int(mode))
        return self.call("set_power", p)
    def set_bright(self, pct, effect="smooth", duration_ms=300):
        return self.call("set_bright", [int(pct), effect, int(duration_ms)])
    def set_ct_abx(self, k, effect="smooth", duration_ms=300):
        return self.call("set_ct_abx", [int(k), effect, int(duration_ms)])
    def set_rgb(self, rgb, effect="smooth", duration_ms=300):
        return self.call("set_rgb", [int(rgb), effect, int(duration_ms)])

def demo_control(b):
    print("Props:", b.get_prop(["power","bright","ct","color_mode","name"]))
    print("Power ON:", b.set_power(True))
    print("Bright 70%:", b.set_bright(70))
    print("CT 5000K:", b.set_ct_abx(5000))
    print("RGB orange:", b.set_rgb(0xFF9900))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--discover", action="store_true")
    p.add_argument("--ip"); p.add_argument("--port", type=int, default=TCP_PORT_DEFAULT)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    global VERBOSE; VERBOSE = args.verbose

    if args.discover or not args.ip:
        print("Discovering bulbs...")
        res = discover(2.0)
        if not res:
            print("No bulbs found. Provide --ip to control directly.")
            return
        for h in res:
            print(f"id={h.get('id')} model={h.get('model')} power={h.get('power')} "
                  f"bright={h.get('bright')} location={h.get('location')}")
        if not args.ip:
            return

    y = YeelightBulb(args.ip, args.port)
    try:
        y.connect()
        demo_control(y)
    finally:
        y.close()

if __name__ == "__main__":
    main()
