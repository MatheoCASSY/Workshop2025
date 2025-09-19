#!/usr/bin/env python3

# --------------------
# Imports
# --------------------
import sys, time, socket, threading, struct, subprocess, os
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
    octets = [192,168,1,1]
cur_octet = 0
brightness = 128
lan_hosts = []
selected_host = 0
output_lines = []
output_offset = 0

# Home script lookup (to return to menu)
HOME = os.path.expanduser("~")
HOME_SCRIPT = os.path.join(HOME, "projet", "scripts", "Home.py")
# fallback to local Home.py
if not os.path.exists(HOME_SCRIPT):
    HOME_SCRIPT = "Home.py"

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

    def cleanup_and_launch_home():
        try:
            backlight.set_all(0,0,0); backlight.show()
            lcd.clear(); lcd.show()
        except:
            pass
        # try to launch Home.py and exit this script
        try:
            subprocess.Popen(["python3", HOME_SCRIPT])
        except Exception:
            pass
        sys.exit(0)

    def show_image():
        pix = img.load()
        for y in range(H):
            for x in range(W):
                lcd.set_pixel(x,y, 1 if pix[x,y] else 0)
        lcd.show()

    def draw_ip_entry():
        draw.rectangle((0,0,W,H), fill=0)
        # Header
        draw.rectangle((0,0,W,9), fill=1)
        draw.text((4,1), "Port Scan", font=font, fill=0)

        # Label
        draw.text((4,16), "IP:", font=font, fill=1)

        # Compose IP display nicely and highlight current octet
        ip_text = ip_from_octets(octets)
        parts = ip_text.split(".")
        # start x for ip (after label)
        x = 30
        for i,p in enumerate(parts):
            w = draw.textsize(p, font=font)[0]
            if i == cur_octet:
                # draw an outlined rounded-ish rect as highlight (2px tall area)
                draw.rectangle((x-2, 22, x + w + 2, 30), fill=1)
                draw.text((x, 24), p, font=font, fill=0)
            else:
                draw.text((x, 24), p, font=font, fill=1)
            x += w + draw.textsize(".", font=font)[0] + 4

        # Footer
        draw.text((4,H-9), "OK=start  BACK=LAN  +/- lum", font=font, fill=1)
        show_image()

    def draw_status(msg):
        draw.rectangle((0,0,W,H), fill=0)
        draw.rectangle((0,0,W,9), fill=1)
        draw.text((4,1), "Port Scan", font=font, fill=0)
        # keep message short and centered-ish
        draw.text((4,18), msg, font=font, fill=1)
        show_image()

    def split_lines_to_width(texts, max_w):
        """split long strings into several lines that fit the display using font metrics"""
        out = []
        for t in texts:
            # simple split by comma or space if too long
            if draw.textsize(t, font=font)[0] <= max_w:
                out.append(t)
            else:
                # split naive into chunks of characters until fits
                cur = ""
                for token in t.replace(",", ", ").split(" "):
                    if cur:
                        candidate = cur + " " + token
                    else:
                        candidate = token
                    if draw.textsize(candidate, font=font)[0] <= max_w:
                        cur = candidate
                    else:
                        if cur:
                            out.append(cur)
                        # token might still be too long -> hard chop
                        if draw.textsize(token, font=font)[0] <= max_w:
                            cur = token
                        else:
                            # hard chop by characters
                            tmp = token
                            while draw.textsize(tmp, font=font)[0] > max_w and len(tmp) > 1:
                                tmp = tmp[:-1]
                            if tmp:
                                out.append(tmp + "-")
                            cur = token[len(tmp):]
                if cur:
                    out.append(cur)
        return out

    def draw_lines(lines, offset=0):
        draw.rectangle((0,0,W,H), fill=0)
        draw.rectangle((0,0,W,9), fill=1)
        draw.text((4,1), "Results", font=font, fill=0)

        # preprocess lines to fit width
        max_w = W - 8
        wrapped = split_lines_to_width(lines, max_w)
        top = 12
        for i in range(OUTPUT_LINES_PER_PAGE):
            idx = offset + i
            if idx >= len(wrapped): break
            draw.text((4, top + i*10), wrapped[idx], font=font, fill=1)

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
        global cur_octet, mode, octets, brightness, output_offset, lan_hosts, selected_host, output_lines
        if event != "press": return

        # ip entry mode
        if mode == "ip_entry":
            if ch == 0: 
                octets[cur_octet] = min(255, octets[cur_octet]+1); draw_ip_entry()
            elif ch == 1: 
                octets[cur_octet] = max(0, octets[cur_octet]-1); draw_ip_entry()
            elif ch == 4:
                if cur_octet < 3: 
                    cur_octet += 1; draw_ip_entry()
                else:
                    mode = "scanning"
            elif ch == 2:
                # go to LAN quick option
                mode = "lan_option"; draw_status("LAN scan: OK to start")
            elif ch == 5:
                brightness = min(255, brightness+16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_ip_entry()
            elif ch == 3:
                brightness = max(0, brightness-16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_ip_entry()

        elif mode == "lan_option":
            if ch == 4:
                mode = "scanning"
            elif ch == 2:
                mode = "ip_entry"; draw_ip_entry()

        elif mode == "results":
            if ch == 0:
                output_offset = max(0, output_offset-1); draw_lines(output_lines, output_offset)
            elif ch == 1:
                output_offset = min(max(0, len(output_lines)-OUTPUT_LINES_PER_PAGE), output_offset+1); draw_lines(output_lines, output_offset)
            elif ch == 2:
                # BACK -> return to Home menu (launch Home.py)
                cleanup_and_launch_home()

        elif mode == "host_select":
            if not lan_hosts:
                # should not happen, but return to ip_entry
                mode = "ip_entry"; draw_ip_entry(); return
            if ch == 0:
                selected_host = max(0, selected_host-1); draw_lines(["Hosts:"]+lan_hosts, selected_host)
            elif ch == 1:
                selected_host = min(len(lan_hosts)-1, selected_host+1); draw_lines(["Hosts:"]+lan_hosts, selected_host)
            elif ch == 4:
                tgt = lan_hosts[selected_host]
                parts = tgt.split(".")
                for i in range(4):
                    octets[i] = int(parts[i])
                mode = "scanning"
            elif ch == 2:
                # BACK -> return to Home menu
                cleanup_and_launch_home()

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
            # if lan_option selected, do lan quick scan
            if mode == "scanning" and 'LAN' in target:
                pass
            ports = scan_ports(target)
            if ports:
                # group ports into chunks that will render nicely (no huge long lines)
                grouped = [", ".join(map(str, ports[i:i+8])) for i in range(0, len(ports), 8)]
                # prepend header
                lines = ["Open ports on " + target + ":"]
                lines.extend(grouped)
                # ensure each line fits using wrap helper
                max_w = W - 8
                output_lines = []
                for l in lines:
                    # if line too long, break it by commas into smaller pieces
                    if draw.textsize(l, font=font)[0] <= max_w:
                        output_lines.append(l)
                    else:
                        parts = l.split(", ")
                        buf = ""
                        for p in parts:
                            cand = (buf + ", " + p) if buf else p
                            if draw.textsize(cand, font=font)[0] <= max_w:
                                buf = cand
                            else:
                                if buf: output_lines.append(buf)
                                buf = p
                        if buf: output_lines.append(buf)
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
