#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import atexit
import subprocess
from os.path import expanduser
from gfxhat import lcd, backlight, touch, fonts
from PIL import Image, ImageFont, ImageDraw

# ------------------------
# Paths / Menu items (fournis)
# ------------------------
HOME = expanduser("~")
SCRIPTS_DIR = HOME + "/projet/scripts"
MENU_ITEMS = [
    ("Wi-Fi Scan", SCRIPTS_DIR + "/wifi_scan.py"),
    ("Port Scan", SCRIPTS_DIR + "/port_scan.py"),
    ("Keylogger Sim", SCRIPTS_DIR + "/keylogger_sim.py"),
    ("NFC Sim", SCRIPTS_DIR + "/nfc_sim.py")
]

# ------------------------
# Init écran / police
# ------------------------
width, height = lcd.dimensions()
try:
    font = ImageFont.truetype(fonts.BitbuntuFull, 10)
except Exception:
    font = ImageFont.load_default()

image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# ------------------------
# Icônes pour menu (style 0/1)
# ------------------------
ICONS = {
    "Wi-Fi Scan": ["00100","01010","10001","00000","00100","00000","00100","00000"],
    "Port Scan":  ["11111","10001","10101","10001","11111","00000","00000","00000"],
    "Keylogger Sim": ["01010","10101","01010","10101","01010","00000","01010","00000"],
    "NFC Sim":    ["00100","01010","00100","01010","00100","00000","00100","00000"]}

# ------------------------
# États et variables UI / Tamagotchi
# ------------------------
current_index = 0
trigger_action = False
mode = "lock"            # lock / unlock_confirm / menu / output / loading
sequence = []            # pour combinaison U-D-U (uniquement en unlock_confirm)
output_lines = []
output_offset = 0
OUTPUT_LINES_PER_PAGE = 5
brightness = 128

# Tamagotchi (sprite 16x16, 2 frames)
tama_eye_open = True

# ------------------------
# mascotte 16x16 (2 frames)
# ------------------------
mascotte_IDLE_1 = [
"1000001000000000",
"1100011000000000",
"1011101000000000",
"1000001000011000",
"1000001000100100",
"1100101000100010",
"1000001000011001",
"1000001000000101",
"1000011000000101",
"1100000111001001",
"0110000000110010",
"0010000000010100",
"0010000000011000",
"0010010010010000",
"0010010010010000",
"0011111111110000",
]

mascotte_IDLE_2 = [
"0100000100000000",
"1010001010000000",
"1001110010000000",
"1000000010001100",
"1000000010010010",
"1010010010010001",
"1000000010001001",
"1000000010000101",
"0100000110000101",
"0010000001000101",
"0010000000111001",
"0010000000010010",
"0010000000011100",
"0010010010010000",
"0010010010010000",
"0011111111110000",
]

# ------------------------
# Cleanup on exit
# ------------------------
def cleanup():
    try:
        backlight.set_all(0,0,0)
        backlight.show()
        lcd.clear()
        lcd.show()
    except Exception:
        pass

atexit.register(cleanup)

# ------------------------
# Draw helpers
# ------------------------
def draw_image_to_lcd():
    pix = image.load()
    for y in range(height):
        for x in range(width):
            lcd.set_pixel(x, y, 1 if pix[x, y] else 0)
    lcd.show()

def draw_bitmap(x_offset, y_offset, bitmap_rows, invert=False):
    for ry, row in enumerate(bitmap_rows):
        for rx, ch in enumerate(row):
            if ch != '1':
                continue
            px = x_offset + rx
            py = y_offset + ry
            if 0 <= px < width and 0 <= py < height:
                draw.point((px, py), 0 if invert else 1)

def draw_bitmap_scaled(x_offset, y_offset, bitmap_rows, scale=1, invert=False):
    # Dessin nearest-neighbor (pixel-art), échelle entière
    if scale <= 1:
        draw_bitmap(x_offset, y_offset, bitmap_rows, invert=invert)
        return
    for ry, row in enumerate(bitmap_rows):
        for rx, ch in enumerate(row):
            if ch != '1':
                continue
            x0 = x_offset + rx*scale
            y0 = y_offset + ry*scale
            x1 = x0 + scale - 1
            y1 = y0 + scale - 1
            if x0 >= width or y0 >= height or x1 < 0 or y1 < 0:
                continue
            draw.rectangle((x0, y0, min(x1, width-1), min(y1, height-1)), fill=(0 if invert else 1))

def draw_icon_on_image(x_offset, y_offset, icon_rows, invert=False):
    for ry, row in enumerate(icon_rows):
        for rx, ch in enumerate(row):
            if ch != "1": 
                continue
            px = x_offset + rx
            py = y_offset + ry
            if 0 <= px < width and 0 <= py < height:
                draw.point((px, py), 0 if invert else 1)

def draw_footer(text):
    # Affiche une ligne d’instructions en bas, tronquée si nécessaire
    footer_y = height - 9
    max_w = width - 4
    t = text
    while draw.textlength(t, font=font) > max_w and len(t) > 3:
        t = t[:-4] + "..."
    draw.text((2, footer_y), t, font=font, fill=1)

def draw_text_centered(line):
    w = draw.textlength(line, font=font)
    x = max(0, (width - w)//2)
    # hauteur approx 10px pour BitbuntuFull 10
    y = max(0, (height//2) - 5)
    draw.text((x, y), line, font=font, fill=1)

# ------------------------
# Loading screen + barre
# ------------------------
def draw_loading_screen(title="Loading...", seconds=1.0):
    steps = 20
    delay = max(0.01, seconds / steps)
    draw.rectangle((0,0,width,height), fill=0)
    draw.text((4,8), title, font=font, fill=1)
    bar_x, bar_y = 6, 30
    bar_w, bar_h = width - 12, 8
    for s in range(steps+1):
        draw.rectangle((bar_x,bar_y,bar_x+bar_w,bar_y+bar_h), fill=0)
        draw.rectangle((bar_x-1,bar_y-1,bar_x+bar_w+1,bar_y+bar_h+1), outline=1)
        fill_w = int((s/steps) * bar_w)
        if fill_w > 0:
            draw.rectangle((bar_x,bar_y,bar_x+fill_w,bar_y+bar_h), fill=1)
        draw_image_to_lcd()
        time.sleep(delay)

# ------------------------
# Tamagotchi drawing / animation (lock screen)
# ------------------------
def draw_tamagotchi():
    draw.rectangle((0,0,width,height), fill=0)

    # Pas de stats en haut — seulement le sprite centré + footer
    base = 16
    reserved_bottom = 10  # pour le footer
    avail_h = height - reserved_bottom
    scale_h = max(1, avail_h // base)
    scale_w = max(1, width // base)
    scale = max(1, min(scale_h, scale_w))
    while (base*scale) > avail_h and scale > 1:
        scale -= 1

    sprite = mascotte_IDLE_1 if tama_eye_open else mascotte_IDLE_2
    sprite_w = base * scale
    sprite_h = base * scale
    sx = (width - sprite_w) // 2
    sy = ((avail_h - sprite_h) // 2)

    draw_bitmap_scaled(sx, sy, sprite, scale=scale)

    # Footer demandé
    draw_footer("BACK: Code de triche  +/-:Lum")

    draw_image_to_lcd()

def animate_tamagotchi():
    global tama_eye_open
    tama_eye_open = not tama_eye_open
    draw_tamagotchi()

# ------------------------
# Menu style Flipper Zero (affichage)
# ------------------------
def draw_menu():
    draw.rectangle((0,0,width,height), fill=0)
    # Header (inversé)
    draw.rectangle((0,0,width,9), fill=1)
    draw.text((4,1), time.strftime("%H:%M"), font=font, fill=0)
    draw.text((width-36,1), f"L:{brightness}", font=font, fill=0)

    if not MENU_ITEMS:
        msg1, msg2 = "Aucun programme", "installe"
        w1 = draw.textlength(msg1, font=font)
        w2 = draw.textlength(msg2, font=font)
        draw.text(((width - w1)//2, (height//2)-12), msg1, font=font, fill=1)
        draw.text(((width - w2)//2, (height//2)+2), msg2, font=font, fill=1)
        draw.text((0,(height - font.getbbox(">")[3])//2), ">", font=font, fill=1)
        draw_image_to_lcd()
        return

    # Scrolling menu with icons and selection bar
    start_y = (height // 2) - 4
    offset_top = current_index * 12
    for idx, (name, _) in enumerate(MENU_ITEMS):
        y = (idx*12) + start_y - offset_top
        icon = ICONS.get(name, ["00000"]*8)
        invert = (idx == current_index)
        if invert:
            draw.rectangle(((20-4, y-1), (width, y+10)), fill=1)
        draw_icon_on_image(2, y, icon, invert=invert)
        draw.text((20, y), name, font=font, fill=0 if invert else 1)

    # Curseur gauche
    draw.text((0,(height - font.getbbox(">")[3])//2), ">", font=font, fill=1)

    # Footer court
    draw_footer("BACK:Lock  OK:Lancer  +/-:Lum  U/D:Nav")

    draw_image_to_lcd()

# ------------------------
# Output display (after running a script)
# ------------------------
def draw_output():
    draw.rectangle((0,0,width,height), fill=0)
    draw.rectangle((0,0,width,9), fill=1)
    draw.text((4,1), time.strftime("%H:%M"), font=font, fill=0)
    draw.text((width-36,1), f"L:{brightness}", font=font, fill=0)
    top = 12
    for i in range(OUTPUT_LINES_PER_PAGE):
        idx = output_offset + i
        if idx >= len(output_lines):
            break
        draw.text((4, top + i*10), output_lines[idx], font=font, fill=1)
    draw_footer("<BACK menu>  +/- Lum  U/D Scroll")
    draw_image_to_lcd()

# ------------------------
# Execution helper (capture stdout/stderr)
# ------------------------
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

# ------------------------
# Touch handler (0=Up,1=Down,2=Back,3=-,4=OK,5=+)
# ------------------------
def handler(ch, event):
    global current_index, trigger_action, mode, output_offset, brightness, output_lines
    global tama_eye_open, sequence

    if event != "press":
        return

    # If viewing output
    if mode == "output":
        if ch == 0:
            output_offset = max(0, output_offset - 1)
            draw_output()
            return
        elif ch == 1:
            max_off = max(0, len(output_lines) - OUTPUT_LINES_PER_PAGE)
            output_offset = min(max_off, output_offset + 1)
            draw_output()
            return
        elif ch == 2:
            mode = "menu"
            draw_menu()
            return
        elif ch == 5:
            brightness = min(255, brightness + 16)
            backlight.set_all(brightness, brightness, brightness); backlight.show()
            draw_output()
            return
        elif ch == 3:
            brightness = max(0, brightness - 16)
            backlight.set_all(brightness, brightness, brightness); backlight.show()
            draw_output()
            return

    # Ignore presses during explicit loading
    if mode == "loading":
        return

    # ------------------------
    # Lock / unlock prompt (code de triche)
    # ------------------------
    if mode in ("lock", "unlock_confirm"):
        if ch == 2:  # BACK -> écran code (après une petite barre)
            mode = "loading"
            draw_loading_screen("Chargement...", seconds=0.8)

            mode = "unlock_confirm"
            draw.rectangle((0,0,width,height), fill=0)
            draw_text_centered("Code de triche ?")
            draw_image_to_lcd()
            sequence = []
            return

        # petites interactions visuelles sur lock
        if ch == 4:  # OK -> blink
            tama_eye_open = not tama_eye_open
            draw_tamagotchi(); return
        elif ch == 5:
            brightness = min(255, brightness+16)
            backlight.set_all(brightness, brightness, brightness); backlight.show()
            draw_tamagotchi(); return
        elif ch == 3:
            brightness = max(0, brightness-16)
            backlight.set_all(brightness, brightness, brightness); backlight.show()
            draw_tamagotchi(); return

        if mode == "unlock_confirm":
            if ch == 0:
                sequence.append('U')
            elif ch == 1:
                sequence.append('D')
            if len(sequence) > 3:
                sequence = sequence[-3:]

            # On n'affiche jamais la séquence : écran identique
            draw.rectangle((0,0,width,height), fill=0)
            draw_text_centered("Code de triche ?")
            draw_image_to_lcd()

            # Code correct -> ouvrir menu (forcer l'affichage)
            if len(sequence) == 3 and sequence == ['U','D','U']:
                mode = "loading"
                draw_loading_screen("Ouverture...", seconds=0.8)
                mode = "menu"
                sequence = []
                draw_menu()
            return

        if mode == "lock":
            draw_tamagotchi()
        return

    # ------------------------
    # Menu interactions
    # ------------------------
    if mode == "menu":
        if ch == 0:
            current_index = (current_index - 1) % len(MENU_ITEMS)
            draw_menu(); return
        elif ch == 1:
            current_index = (current_index + 1) % len(MENU_ITEMS)
            draw_menu(); return
        elif ch == 4:  # OK -> exécute
            name, path = MENU_ITEMS[current_index]
            mode = "loading"
            draw_loading_screen(f"Lancement: {name}", seconds=1.0)
            output_lines.clear()
            output_lines.extend(run_script_capture(path))
            output_offset = 0
            mode = "output"
            draw_output()
            return
        elif ch == 2:  # BACK -> reverrouiller
            mode = "loading"
            draw_loading_screen("Verrouillage...", seconds=0.6)
            mode = "lock"
            draw_tamagotchi()
            return
        elif ch == 5:
            brightness = min(255, brightness + 16)
            backlight.set_all(brightness, brightness, brightness); backlight.show()
            draw_menu(); return
        elif ch == 3:
            brightness = max(0, brightness - 16)
            backlight.set_all(brightness, brightness, brightness); backlight.show()
            draw_menu(); return

# ------------------------
# Hook touches
# ------------------------
for i in range(6):
    try: touch.set_led(i, 0)
    except: pass
    try: backlight.set_pixel(i, 255, 255, 255)
    except: pass
    try: touch.on(i, handler)
    except: pass

backlight.set_all(brightness, brightness, brightness)
backlight.show()

# ------------------------
# Main loop
# ------------------------
draw_tamagotchi()
try:
    while True:
        if mode == "lock":
            animate_tamagotchi(); time.sleep(0.5)
        elif mode == "menu":
            draw_menu(); time.sleep(0.2)
        elif mode == "output":
            draw_output(); time.sleep(0.2)
        elif mode == "unlock_confirm":
            time.sleep(0.2)
        elif mode == "loading":
            time.sleep(0.1)
        else:
            time.sleep(0.2)
except KeyboardInterrupt:
    cleanup()
    sys.exit(0)
