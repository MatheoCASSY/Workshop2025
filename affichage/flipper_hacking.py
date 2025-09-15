#!/usr/bin/env python3

import time
import sys
import atexit
import subprocess
from os.path import expanduser
from gfxhat import lcd, backlight, touch, fonts
from PIL import Image, ImageFont, ImageDraw

HOME = expanduser("~")
SCRIPTS_DIR = HOME + "/projet/scripts"
MENU_ITEMS = [
    ("Wi-Fi Scan", SCRIPTS_DIR + "/wifi_scan.py"),
    ("Port Scan", SCRIPTS_DIR + "/port_scan.py"),
    ("Keylogger Sim", SCRIPTS_DIR + "/keylogger_sim.py"),
    ("NFC Sim", SCRIPTS_DIR + "/nfc_sim.py"),
    ("Exit", SCRIPTS_DIR + "/exit_script.py"),
]

width, height = lcd.dimensions()
try:
    font = ImageFont.truetype(fonts.BitbuntuFull, 10)
except:
    font = ImageFont.load_default()

image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

ICONS = {
    "Wi-Fi Scan": ["00100","01010","10001","00000","00100","00000","00100","00000"],
    "Port Scan": ["11111","10001","10101","10001","11111","00000","00000","00000"],
    "Keylogger Sim": ["01010","10101","01010","10101","01010","00000","01010","00000"],
    "NFC Sim": ["00100","01010","00100","01010","00100","00000","00100","00000"],
    "Exit": ["11111","10001","10101","10001","11111","00000","00000","00000"]
}

current_index = 0
trigger_action = False
mode = "menu"
output_lines = []
output_offset = 0
OUTPUT_LINES_PER_PAGE = 5
brightness = 128

def draw_icon_on_image(x_offset, y_offset, icon, invert=False):
    for ry, row in enumerate(icon):
        for rx, ch in enumerate(row):
            px = x_offset + rx
            py = y_offset + ry
            if 0 <= px < width and 0 <= py < height:
                if ch == "1":
                    draw.point((px, py), 0 if invert else 1)

def run_script_capture(path):
    try:
        proc = subprocess.run(["python3", path], capture_output=True, text=True, timeout=30)
        out = proc.stdout or ""
        err = proc.stderr or ""
        text = out + (("\nERR:\n" + err) if err else "")
    except subprocess.TimeoutExpired:
        text = "Script timeout."
    except Exception as e:
        text = "Error running script: " + str(e)
    lines = []
    for line in text.splitlines():
        max_chars = 20
        for i in range(0, len(line), max_chars):
            lines.append(line[i:i+max_chars])
    if not lines:
        lines = ["<no output>"]
    return lines

def handler(ch, event):
    global current_index, trigger_action, mode, output_offset, brightness
    if event != "press":
        return

    if mode == "output":
        if ch == 0:            # Up -> scroll up
            output_offset = max(0, output_offset - 1)
        elif ch == 1:          # Down -> scroll down
            max_off = max(0, len(output_lines) - OUTPUT_LINES_PER_PAGE)
            output_offset = min(max_off, output_offset + 1)
        elif ch == 2:          # Retour -> go back to menu
            mode = "menu"
        elif ch == 5:          # + luminosité
            brightness = min(255, brightness + 16)
            backlight.set_all(brightness, brightness, brightness)
            backlight.show()
        elif ch == 3:          # - luminosité
            brightness = max(0, brightness - 16)
            backlight.set_all(brightness, brightness, brightness)
            backlight.show()
        return

    # mode menu
    if ch == 0:                # Up
        current_index -= 1
    elif ch == 1:              # Down
        current_index += 1
    elif ch == 4:              # OK / exécuter
        trigger_action = True
    elif ch == 5:              # + luminosité
        brightness = min(255, brightness + 16)
        backlight.set_all(brightness, brightness, brightness)
        backlight.show()
    elif ch == 3:              # - luminosité
        brightness = max(0, brightness - 16)
        backlight.set_all(brightness, brightness, brightness)
        backlight.show()
    elif ch == 2:              # Retour (en menu, reste au menu)
        mode = "menu"

    current_index %= len(MENU_ITEMS)

for i in range(6):
    try: touch.set_led(i, 0)
    except: pass
    try: backlight.set_pixel(i, 255, 255, 255)
    except: pass
    try: touch.on(i, handler)
    except: pass
backlight.set_all(brightness, brightness, brightness)
backlight.show()

def cleanup():
    backlight.set_all(0,0,0)
    backlight.show()
    lcd.clear()
    lcd.show()
atexit.register(cleanup)

def redraw():
    draw.rectangle((0,0,width,height), fill=0)
    draw.rectangle((0,0,width,9), fill=1)
    draw.text((4,1), time.strftime("%H:%M"), font=font, fill=0)
    draw.text((width-28,1), f"L:{brightness}", font=font, fill=0)

    if mode == "menu":
        start_y = (height // 2) - 4
        offset_top = sum(12 for _ in range(current_index))
        for idx, (name, path) in enumerate(MENU_ITEMS):
            y = (idx*12) + start_y - offset_top
            icon = ICONS.get(name, ["00000"]*8)
            invert = (idx == current_index)
            if invert:
                draw.rectangle(((20-4, y-1), (width, y+10)), fill=1)
            draw_icon_on_image(2, y, icon, invert=invert)
            draw.text((20, y), name, font=font, fill=0 if invert else 1)
        draw.text((0,(height-font.getsize(">")[1])//2), ">", font=font, fill=1)
    elif mode == "output":
        top = 12
        for i in range(OUTPUT_LINES_PER_PAGE):
            idx = output_offset + i
            if idx >= len(output_lines):
                break
            draw.text((4, top + i*10), output_lines[idx], font=font, fill=1)
        hint = "<BACK pour menu> +/- Lum"
        draw.text((4, height - 9), hint, font=font, fill=1)

    pixels = image.load()
    for yy in range(height):
        for xx in range(width):
            lcd.set_pixel(xx, yy, 1 if pixels[xx, yy] else 0)
    lcd.show()

redraw()

try:
    while True:
        if trigger_action and mode == "menu":
            name, path = MENU_ITEMS[current_index]
            if name.lower().startswith("exit"):
                try: subprocess.run(["python3", path])
                except: pass
                cleanup()
                sys.exit(0)
            output_lines = run_script_capture(path)
            output_offset = 0
            mode = "output"
            trigger_action = False
            redraw()
        else:
            redraw()
            time.sleep(0.1)
except KeyboardInterrupt:
    cleanup()
