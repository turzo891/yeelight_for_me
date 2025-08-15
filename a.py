import socket, json
ip = "192.168.0.156"
s = socket.create_connection((ip, 55443))
cmd = {"id":1,"method":"get_prop","params":["power","bright","ct","name"]}
s.sendall((json.dumps(cmd) + "\r\n").encode())
print(s.recv(1024).decode())
s.close()

# # py - <<'PY'
# import socket, time
# m=("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1982\r\nMAN: \"ssdp:discover\"\r\nST: wifi_bulb\r\n\r\n").encode()
# s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP); s.bind(("",0)); s.settimeout(3)
# s.sendto(m,("239.255.255.250",1982))
# end=time.time()+3
# got=False
# while time.time()<end:
#     try:
#         d,addr=s.recvfrom(65535); print(d.decode()); got=True
#     except socket.timeout: break
# print("No replies" if not got else "OK")
# # PY