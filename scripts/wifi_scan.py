#!/usr/bin/env python3
import time

print("Starting Wi-Fi scan...")
time.sleep(1)
networks = ["HomeWiFi", "RaspberryPi", "TestNetwork"]
for n in networks:
    print("Found network:", n)
    time.sleep(0.5)
print("Wi-Fi scan complete.")
