# find_yeelight_tcp.py — scan local /24 and verify Yeelight on tcp/55443
import os, ipaddress, socket, json

PORT = 55443
TIMEOUT = 0.35

def local_ipv4s():
    ips=[]
    for line in os.popen("ipconfig").read().splitlines():
        line=line.strip()
        if line.startswith("IPv4 Address") or line.startswith("IPv4-adres"):
            ip=line.split(":")[-1].strip()
            if ip and not ip.startswith("169.254."):
                ips.append(ip)
    return ips

def is_yeelight(ip):
    try:
        s=socket.create_connection((ip,PORT),timeout=TIMEOUT)
        s.settimeout(TIMEOUT)
        msg=json.dumps({"id":1,"method":"get_prop","params":["power","bright","ct","name"]})+"\r\n"
        s.sendall(msg.encode())
        data=s.recv(1024).decode(errors="ignore")
        s.close()
        return '"result"' in data or '"ok"' in data
    except Exception:
        return False

def main():
    seen=set(); found=[]
    for ip in local_ipv4s():
        net=ipaddress.ip_interface(ip+"/24").network
        print(f"Scanning {net} ...")
        for host in net.hosts():
            h=str(host)
            if h in seen: continue
            seen.add(h)
            try:
                socket.create_connection((h,PORT),timeout=0.12).close()
                if is_yeelight(h):
                    print(f"FOUND {h}")
                    found.append(h)
            except Exception:
                pass
    if not found:
        print("No bulbs found")
    else:
        print("Bulbs:", ", ".join(found))

if __name__=="__main__":
    main()
