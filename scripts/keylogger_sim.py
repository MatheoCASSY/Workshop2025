#!/usr/bin/env python3
import time

print("Simulating keylogger movement...")
keys = ["W", "A", "S", "D", "ENTER"]
for k in keys:
    print(f"Key pressed: {k}")
    time.sleep(0.5)
print("Keylogger simulation complete (safe, no real keys logged).")
