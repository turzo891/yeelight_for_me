1. winget install -e --id nmap

2. ipconfig

3. Scan your subnet for port 55443:> nmap -p 55443 192.168.0.0/24 --open
should get someting like 'Starting Nmap 7.80 ( https://nmap.org ) at 2025-08-16 04:11 Bangladesh Standard Time
Stats: 0:00:01 elapsed; 0 hosts completed (0 up), 255 undergoing ARP Ping Scan
ARP Ping Scan Timing: About 21.76% done; ETC: 04:11 (0:00:07 remaining)
Nmap scan report for 192.168.0.156
Host is up (0.18s latency).

PORT      STATE SERVICE
55443/tcp open  unknown
MAC Address: 54:48:E6:31:0F:4C (Unknown)' 

4. to discover by py 'py discover_yeelight.py
Scanning 192.168.0.0/24 ...
FOUND 192.168.0.156' then try this 'py yeelight_color.py 192.168.0.156 FFFFFF' 

or py yeelight_cli.py --on --rgb FF9900 --bright 70

Use this :

py yeelight_color.py 192.168.0.156 FFFFFF
