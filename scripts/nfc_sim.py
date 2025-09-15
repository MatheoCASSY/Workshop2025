#!/usr/bin/env python3
import time

print("Scanning for NFC/RFID tags nearby...")
tags = ["TAG_001", "TAG_ABC", "TAG_XYZ"]
for t in tags:
    print("Detected tag:", t)
    time.sleep(0.5)
print("NFC scan complete.")
