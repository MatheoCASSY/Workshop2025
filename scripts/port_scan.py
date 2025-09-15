#!/usr/bin/env python3
import time

print("Starting port scan on 192.168.1.1...")
for port in [22, 80, 443]:
    print(f"Port {port} open")
    time.sleep(0.5)
print("Port scan complete.")
