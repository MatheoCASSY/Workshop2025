#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --------------------
# Imports
# --------------------
import sys, time, socket, threading, struct
from queue import Queue

try:
    from gfxhat import lcd, backlight, touch, fonts
    from PIL import Image, ImageFont, ImageDraw
    GFX = True
except Exception:
    GFX = False

# --------------------
# Config
# --------------------
PORT_RANGE = range(1, 1025)
THREADS = 200
CONN_TIMEOUT = 0.35
OUTPUT_LINES_PER_PAGE = 5

# --------------------
# Réseau helpers
# --------------------
def ip_from_octets(o): return "{}.{}.{}.{}".format(*o)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = None
    finally:
        s.close()
    return ip

def get_default_gateway():
    """
    Lecture de la passerelle par défaut dans /proc/net/route
    (Linux only, ex: Raspberry Pi)
    """
    try:
        with open("/proc/net/route") as f:
            for line in f.readlines():
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    continue
                gw = socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
                return gw
    except:
        return None

def scan_ports(target_ip, ports=PORT_RANGE, threads=THREADS, timeout=CONN_TIMEOUT):
    q = Queue()
    open_ports = []
    lock = threading.Lock()
    def worker():
        while not q.empty():
            p = q.get()
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                s.connect((target_ip, p))
                s.close()
                with lock: open_ports.append(p)
            except: pass
            finally: q.task_done()
    for p in ports: q.put(p)
    for _ in range(min(threads, q.qsize())):
        t = threading.Thread(target=worker); t.daemon = True; t.start()
    q.join()
    open_ports.sort()
    return open_ports

def scan_lan_quick(port_probe=80, timeout=0.18, threads=200):
    local = get_local_ip()
    if not local: return [], None
    base = ".".join(local.split(".")[:3])
    q = Queue(); found = []; lock = threading.Lock()
    def worker():
        while not q.empty():
            sfx = q.get()
            tgt = base + "." + str(sfx)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                s.connect((tgt, port_probe)); s.close()
                with lock: found.append(tgt)
            except: pass
            finally: q.task_done()
    for i in range(1,255): q.put(i)
    for _ in range(min(threads, q.qsize())):
        t = threading.Thread(target=worker); t.daemon = True; t.start()
    q.join()
    found.sort()
    return found, local

# --------------------
# État UI
# --------------------
mode = "ip_entry"            # ip_entry / lan_option / scanning / results / host_select
gw = get_default_gateway()
if gw:
    octets = [int(x) for x in gw.split(".")]
else:
    octets = [192,168,1,1]   # fallback si routeur non trouvé
cur_octet = 0
brightness = 128
lan_hosts = []
selected_host = 0
output_lines = []
output_offset = 0

# --------------------
# GFX helpers
# --------------------
if GFX:
    W,H = lcd.dimensions()
    try:
        font = ImageFont.truetype(fonts.BitbuntuFull, 10)
    except:
        font = ImageFont.load_default()
    img = Image.new('1', (W,H)); draw = ImageDraw.Draw(img)

    def show_image():
        pix = img.load()
        for y in range(H):
            for x in range(W):
                lcd.set_pixel(x,y, 1 if pix[x,y] else 0)
        lcd.show()

    def draw_ip_entry():
        draw.rectangle((0,0,W,H), fill=0)
        draw.rectangle((0,0,W,9), fill=1)
        draw.text((4,1), "Port Scan", font=font, fill=0)
        draw.text((4,14), "IP:", font=font, fill=1)
        ip_text = ip_from_octets(octets)
        draw.text((30,14), ip_text, font=font, fill=1)
        parts = ip_text.split(".")
        x = 30
        for i,p in enumerate(parts):
            w = font.getsize(p)[0]
            if i == cur_octet:
                draw.rectangle((x-1,26,x+w+1,28), fill=1)
                draw.text((x,24), p, font=font, fill=0)
            else:
                draw.text((x,24), p, font=font, fill=1)
            x += w + font.getsize(".")[0] + 2
        draw.text((4,H-9), "OK=start  BACK=LAN  +/- lum", font=font, fill=1)
        show_image()

    def draw_status(msg):
        draw.rectangle((0,0,W,H), fill=0)
        draw.rectangle((0,0,W,9), fill=1)
        draw.text((4,1), "Scanning...", font=font, fill=0)
        draw.text((4,14), msg, font=font, fill=1)
        show_image()

    def draw_lines(lines, offset=0):
        draw.rectangle((0,0,W,H), fill=0)
        draw.rectangle((0,0,W,9), fill=1)
        draw.text((4,1), "Results", font=font, fill=0)
        top = 12
        for i in range(OUTPUT_LINES_PER_PAGE):
            idx = offset + i
            if idx >= len(lines): break
            draw.text((4, top + i*10), lines[idx], font=font, fill=1)
        draw.text((4,H-9), "<BACK menu  +/- lum", font=font, fill=1)
        show_image()

    try:
        backlight.set_all(brightness,brightness,brightness); backlight.show()
    except: pass
    draw_ip_entry()

# --------------------
# Touch handler
# --------------------
if GFX:
    def touch_handler(ch, event):
        global cur_octet, mode, octets, brightness, output_offset, lan_hosts, selected_host
        if event != "press": return
        if mode == "ip_entry":
            if ch == 0: octets[cur_octet] = min(255, octets[cur_octet]+1); draw_ip_entry()
            elif ch == 1: octets[cur_octet] = max(0, octets[cur_octet]-1); draw_ip_entry()
            elif ch == 4:
                if cur_octet < 3: cur_octet += 1; draw_ip_entry()
                else: mode = "scanning"
            elif ch == 2:
                mode = "lan_option"; draw_status("LAN scan: OK to start")
            elif ch == 5:
                brightness = min(255, brightness+16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_ip_entry()
            elif ch == 3:
                brightness = max(0, brightness-16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_ip_entry()
        elif mode == "lan_option":
            if ch == 4: mode = "scanning"
            elif ch == 2: mode = "ip_entry"; draw_ip_entry()
        elif mode == "results":
            if ch == 0: output_offset = max(0, output_offset-1); draw_lines(output_lines, output_offset)
            elif ch == 1: output_offset = min(max(0, len(output_lines)-OUTPUT_LINES_PER_PAGE), output_offset+1); draw_lines(output_lines, output_offset)
            elif ch == 2: mode = "ip_entry"; draw_ip_entry()
        elif mode == "host_select":
            if ch == 0: selected_host = max(0, selected_host-1); draw_lines(["Hosts:"]+lan_hosts, selected_host)
            elif ch == 1: selected_host = min(len(lan_hosts)-1, selected_host+1); draw_lines(["Hosts:"]+lan_hosts, selected_host)
            elif ch == 4:
                tgt = lan_hosts[selected_host]
                parts = tgt.split(".")
                for i in range(4):
                    octets[i] = int(parts[i])
                mode = "scanning"
            elif ch == 2:
                mode = "ip_entry"; draw_ip_entry()

    for i in range(6):
        try: touch.on(i, touch_handler)
        except: pass

# --------------------
# Console fallback
# --------------------
def console_mode():
    print("GFX HAT non disponible -> mode console.")
    print("1) Enter IP")
    print("2) LAN scan (quick)")
    c = input("Choice [1/2]: ").strip() or "1"
    if c == "1":
        ip = input(f"IP [{ip_from_octets(octets)}]: ").strip() or ip_from_octets(octets)
        print("Scanning", ip)
        ports = scan_ports(ip)
        if ports:
            print("Open ports:", ports)
        else:
            print("No open ports.")
    else:
        hosts, local = scan_lan_quick()
        print("Local IP:", local)
        if not hosts: print("No hosts found.")
        else:
            for i,h in enumerate(hosts): print(i, h)
            pick = input("Index to scan: ").strip()
            try: idx = int(pick); tgt = hosts[idx]
            except: return
            ports = scan_ports(tgt)
            print("Open ports on", tgt, ":", ports)

# --------------------
# Main loop
# --------------------
def main_loop():
    global mode, output_lines, output_offset, lan_hosts, selected_host
    if not GFX:
        console_mode(); return

    while True:
        if mode == "ip_entry":
            time.sleep(0.1)
        elif mode == "lan_option":
            time.sleep(0.1)
        elif mode == "scanning":
            target = ip_from_octets(octets)
            draw_status("Scan " + target)
            ports = scan_ports(target)
            if ports:
                grouped = [", ".join(map(str, ports[i:i+6])) for i in range(0, len(ports), 6)]
                output_lines = ["Open ports on " + target + ":"] + grouped
            else:
                output_lines = ["No open ports on " + target]
            mode = "results"; output_offset = 0
            draw_lines(output_lines, 0)
        elif mode == "host_select":
            if not lan_hosts:
                draw_status("Scanning LAN...")
                hosts, _ = scan_lan_quick()
                lan_hosts = hosts
                if not lan_hosts:
                    output_lines = ["No hosts found on LAN"]; mode = "results"; draw_lines(output_lines,0); continue
            draw_lines(["Hosts:"]+lan_hosts, 0)
            time.sleep(0.1)
        elif mode == "results":
            time.sleep(0.1)
        else:
            time.sleep(0.1)

# --------------------
# Entrée
# --------------------
if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        if GFX:
            try: backlight.set_all(0,0,0); backlight.show(); lcd.clear(); lcd.show()
            except: pass
        sys.exit(0)
