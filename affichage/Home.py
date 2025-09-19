#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, sys, atexit, subprocess
from os.path import expanduser
from gfxhat import lcd, backlight, touch, fonts
from PIL import Image, ImageFont, ImageDraw

# ------------------------
# Paths / Menu items
# ------------------------
HOME = expanduser("~")
SCRIPTS_DIR = HOME + "/projet/scripts"
MENU_ITEMS = [
    ("Wi-Fi Scan", SCRIPTS_DIR + "/wifi_scan.py"),
    ("Port Scan",  SCRIPTS_DIR + "/port_scan.py"),
    ("Keylogger Sim", SCRIPTS_DIR + "/keylogger_sim.py"),
    ("NFC Sim",    SCRIPTS_DIR + "/nfc_sim.py"),
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
# Icônes menu (8x5)
# ------------------------
ICONS = {
    "Wi-Fi Scan":     ["00100","01010","10001","00000","00100","00000","00100","00000"],
    "Port Scan":      ["11111","10001","10101","10001","11111","00000","00000","00000"],
    "Keylogger Sim":  ["01010","10101","01010","10101","01010","00000","01010","00000"],
    "NFC Sim":        ["00100","01010","00100","01010","00100","00000","00100","00000"],
}

# ------------------------
# États
# ------------------------
current_index = 0
mode = "lock"     # lock / unlock_confirm / menu / output / loading
sequence = []
output_lines = []
output_offset = 0
OUTPUT_LINES_PER_PAGE = 5
brightness = 128
tama_eye_open = True

# ------------------------
# Sprite Tamagotchi (16x16)
# ------------------------
mascotte_IDLE_1 = [
"1000001000000000","1100011000000000","1011101000000000","1000001000011000",
"1000001000100100","1100101000100010","1000001000011001","1000001000000101",
"1000011000000101","1100000111001001","0110000000110010","0010000000010100",
"0010000000011000","0010010010010000","0010010010010000","0011111111110000",
]
mascotte_IDLE_2 = [
"0100000100000000","1010001010000000","1001110010000000","1000000010001100",
"1000000010010010","1010010010010001","1000000010001001","1000000010000101",
"0100000110000101","0010000001000101","0010000000111001","0010000000010010",
"0010000000011100","0010010010010000","0010010010010000","0011111111110000",
]

# ------------------------
# Utils
# ------------------------
def cleanup():
    try:
        backlight.set_all(0,0,0); backlight.show()
        lcd.clear(); lcd.show()
    except: pass
atexit.register(cleanup)

def clear_screen():
    # Efface le buffer PIL
    draw.rectangle((0,0,width,height), fill=0)

def draw_image_to_lcd():
    pix = image.load()
    for y in range(height):
        for x in range(width):
            lcd.set_pixel(x,y,1 if pix[x,y] else 0)
    lcd.show()

def draw_bitmap_scaled(x,y,bitmap,scale=1):
    for ry,row in enumerate(bitmap):
        for rx,ch in enumerate(row):
            if ch=="1":
                draw.rectangle((x+rx*scale,y+ry*scale,x+(rx+1)*scale-1,y+(ry+1)*scale-1), fill=1)

def draw_icon_on_image(x_offset, y_offset, icon_rows, invert=False):
    for ry,row in enumerate(icon_rows):
        for rx,ch in enumerate(row):
            if ch!="1": continue
            px=x_offset+rx; py=y_offset+ry
            if 0<=px<width and 0<=py<height:
                draw.point((px,py), 0 if invert else 1)

def draw_footer(txt):
    # tronque si trop long
    max_w = width - 4
    t = txt
    while draw.textlength(t, font=font) > max_w and len(t) > 3:
        t = t[:-4] + "..."
    draw.text((2, height-9), t, font=font, fill=1)

# ------------------------
# Loading (efface aussi le LCD)
# ------------------------
def draw_loading_screen(title="Loading...", seconds=0.8):
    # Efface complètement l'affichage précédent
    clear_screen()
    lcd.clear(); lcd.show()

    steps=16
    delay=max(0.01, seconds/steps)
    draw.text((4,8), title, font=font, fill=1)
    bar_x, bar_y = 6, 30
    bar_w, bar_h = width-12, 8
    for s in range(steps+1):
        # re-clear la zone barre pour éviter traînées
        draw.rectangle((bar_x-1,bar_y-1,bar_x+bar_w+1,bar_y+bar_h+1), outline=1, fill=0)
        fill=int((s/steps)*bar_w)
        if fill>0:
            draw.rectangle((bar_x,bar_y,bar_x+fill,bar_y+bar_h), fill=1)
        draw_image_to_lcd()
        time.sleep(delay)

# ------------------------
# Écrans
# ------------------------
def draw_tamagotchi():
    clear_screen()
    sprite = mascotte_IDLE_1 if tama_eye_open else mascotte_IDLE_2
    scale = 3
    sx = (width-(16*scale))//2
    sy = (height-(16*scale))//2 - 4
    draw_bitmap_scaled(sx, sy, sprite, scale)
    draw_footer("BACK: Code de triche  +/-:Lum")
    draw_image_to_lcd()

def animate_tamagotchi():
    global tama_eye_open
    tama_eye_open = not tama_eye_open
    draw_tamagotchi()

def draw_unlock_prompt():
    clear_screen()
    # Écran vide avec texte centré
    msg = "Code de triche ?"
    w = draw.textlength(msg, font=font)
    draw.text(((width - w)//2, height//2 - 5), msg, font=font, fill=1)
    draw_image_to_lcd()

def draw_menu():
    clear_screen()
    # Header inversé
    draw.rectangle((0,0,width,9), fill=1)
    draw.text((4,1), time.strftime("%H:%M"), font=font, fill=0)
    draw.text((width-36,1), f"L:{brightness}", font=font, fill=0)

    # Liste
    entry_h = 12
    start_y = 14
    for idx,(name,_) in enumerate(MENU_ITEMS):
        y = start_y + idx*entry_h
        invert = (idx == current_index)
        if invert:
            draw.rectangle((18, y-1, width-2, y+10), fill=1)
        icon = ICONS.get(name, ["00000"]*8)
        draw_icon_on_image(2, y, icon, invert=invert)
        draw.text((20, y), name, font=font, fill=(0 if invert else 1))

    # (flèche supprimée pour éviter artefacts)
    draw_footer("BACK:Lock  OK:Lancer  +/-:Lum  U/D:Nav")
    draw_image_to_lcd()

def draw_output():
    clear_screen()
    draw.rectangle((0,0,width,9), fill=1)
    draw.text((4,1), time.strftime("%H:%M"), font=font, fill=0)
    draw.text((width-36,1), f"L:{brightness}", font=font, fill=0)

    top = 12
    for i in range(OUTPUT_LINES_PER_PAGE):
        idx = output_offset + i
        if idx >= len(output_lines): break
        draw.text((4, top + i*10), output_lines[idx], font=font, fill=1)

    draw_footer("BACK:Menu  +/-:Lum  U/D:Scroll")
    draw_image_to_lcd()

# ------------------------
# Runner (capture stdout/stderr)
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
        text = "Error: " + str(e)

    lines = []
    for line in text.splitlines():
        for i in range(0, len(line), 20):
            lines.append(line[i:i+20])
    if not lines:
        lines = ["<no output>"]
    return lines

# ------------------------
# Handler touches (0=Up,1=Down,2=Back,3=-,4=OK,5=+)
# ------------------------
def handler(ch, event):
    global current_index, mode, output_offset, brightness, output_lines, sequence, tama_eye_open
    if event != "press":
        return

    # ----- RÈGLE BACK GLOBALE -----
    if ch == 2:
        # Si on est déjà sur le menu => verrouille
        if mode == "menu":
            mode = "loading"
            draw_loading_screen("Verrouillage...", seconds=0.5)
            mode = "lock"
            draw_tamagotchi()
            return
        # Sinon, retour menu principal
        mode = "menu"
        draw_menu()
        return

    # Bloque les inputs pendant "loading"
    if mode == "loading":
        return

    # ----- LOCK -----
    if mode == "lock":
        if ch == 4:  # OK -> petit blink
            tama_eye_open = not tama_eye_open
            draw_tamagotchi(); return
        elif ch == 5:  # Lum +
            brightness = min(255, brightness+16)
            backlight.set_all(brightness,brightness,brightness); backlight.show()
            draw_tamagotchi(); return
        elif ch == 3:  # Lum -
            brightness = max(0, brightness-16)
            backlight.set_all(brightness,brightness,brightness); backlight.show()
            draw_tamagotchi(); return
        # Up/Down ignorés
        return

    # ----- UNLOCK (Code de triche) -----
    if mode == "unlock_confirm":
        if ch == 0: sequence.append('U')
        elif ch == 1: sequence.append('D')
        if len(sequence) > 3: sequence[:] = sequence[-3:]

        # On ne visualise jamais la séquence : écran identique
        draw_unlock_prompt()

        if sequence == ['U','D','U']:
            mode = "loading"
            draw_loading_screen("Ouverture...", seconds=0.8)
            mode = "menu"
            sequence.clear()
            draw_menu()
        return

    # ----- MENU -----
    if mode == "menu":
        if ch == 0:  # Up
            current_index = (current_index - 1) % len(MENU_ITEMS)
            draw_menu(); return
        elif ch == 1:  # Down
            current_index = (current_index + 1) % len(MENU_ITEMS)
            draw_menu(); return
        elif ch == 4:  # OK -> exécute
            name, path = MENU_ITEMS[current_index]
            mode = "loading"
            draw_loading_screen(f"Lancement: {name}", seconds=1.0)
            output_lines = run_script_capture(path)
            output_offset = 0
            mode = "output"
            draw_output()
            return
        elif ch == 5:  # Lum +
            brightness = min(255, brightness+16)
            backlight.set_all(brightness,brightness,brightness); backlight.show()
            draw_menu(); return
        elif ch == 3:  # Lum -
            brightness = max(0, brightness-16)
            backlight.set_all(brightness,brightness,brightness); backlight.show()
            draw_menu(); return
        return

    # ----- OUTPUT -----
    if mode == "output":
        if ch == 0:  # Up (scroll)
            output_offset = max(0, output_offset - 1)
            draw_output(); return
        elif ch == 1:  # Down (scroll)
            max_off = max(0, len(output_lines) - OUTPUT_LINES_PER_PAGE)
            output_offset = min(max_off, output_offset + 1)
            draw_output(); return
        elif ch == 5:  # Lum +
            brightness = min(255, brightness+16)
            backlight.set_all(brightness,brightness,brightness); backlight.show()
            draw_output(); return
        elif ch == 3:  # Lum -
            brightness = max(0, brightness-16)
            backlight.set_all(brightness,brightness,brightness); backlight.show()
            draw_output(); return
        return

# ------------------------
# Hook touches & backlight
# ------------------------
for i in range(6):
    try: touch.set_led(i, 0)
    except: pass
    try: touch.on(i, handler)
    except: pass
backlight.set_all(brightness,brightness,brightness)
backlight.show()

# ------------------------
# Main loop
# ------------------------
# Démarre en lock (tamagotchi)
draw_tamagotchi()

try:
    while True:
        if mode == "lock":
            animate_tamagotchi(); time.sleep(0.5)
        elif mode == "unlock_confirm":
            time.sleep(0.2)
        elif mode == "menu":
            time.sleep(0.2)
        elif mode == "output":
            time.sleep(0.2)
        elif mode == "loading":
            time.sleep(0.1)
        else:
            time.sleep(0.2)
except KeyboardInterrupt:
    cleanup(); sys.exit(0)
