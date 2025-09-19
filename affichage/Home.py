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
# Paths / Menu items
# ------------------------
HOME = expanduser("~")
SCRIPTS_DIR = HOME + "/projet/scripts"
MENU_ITEMS = [
    ("Wi-Fi Scan", SCRIPTS_DIR + "/wifi_scan.py"),
    ("Port Scan", SCRIPTS_DIR + "/port_scan.py"),
    ("Keylogger Sim", SCRIPTS_DIR + "/keylogger_sim.py"),
    ("NFC Sim", SCRIPTS_DIR + "/nfc_sim.py"),
    ("Exit", SCRIPTS_DIR + "/exit_script.py")
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
# Icônes menu (petits dessins)
# ------------------------
ICONS = {
    "Wi-Fi Scan": ["00100","01010","10001","00000","00100","00000","00100","00000"],
    "Port Scan":  ["11111","10001","10101","10001","11111","00000","00000","00000"],
    "Keylogger Sim": ["01010","10101","01010","10101","01010","00000","01010","00000"],
    "NFC Sim":    ["00100","01010","00100","01010","00100","00000","00100","00000"]
}

# ------------------------
# États
# ------------------------
current_index = 0
mode = "lock"  # lock / unlock_confirm / menu / output / loading
sequence = []
output_lines = []
output_offset = 0
OUTPUT_LINES_PER_PAGE = 5
brightness = 128
tama_eye_open = True

# ------------------------
# Sprite 16x16 (2 frames)
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
# Nettoyage à la sortie
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
# Helpers affichage
# ------------------------
def lcd_display():
    pix = image.load()
    for y in range(height):
        for x in range(width):
            lcd.set_pixel(x, y, 1 if pix[x, y] else 0)
    lcd.show()

def clear_screen():
    draw.rectangle((0,0,width,height), fill=0)

def draw_bitmap_scaled(x_offset, y_offset, bitmap_rows, scale=1, invert=False):
    for ry, row in enumerate(bitmap_rows):
        for rx, ch in enumerate(row):
            if ch != '1': continue
            x0 = x_offset + rx*scale
            y0 = y_offset + ry*scale
            x1 = x0 + scale - 1
            y1 = y0 + scale - 1
            # clamp drawing to screen bounds
            if x1 < 0 or y1 < 0 or x0 >= width or y0 >= height:
                continue
            draw.rectangle((x0, y0, min(x1, width-1), min(y1, height-1)), fill=(0 if invert else 1))

def draw_footer(text):
    footer_y = height - 9
    # tronque si trop long
    t = text
    max_w = width - 4
    while draw.textlength(t, font=font) > max_w and len(t) > 3:
        t = t[:-3] + "..."
    draw.text((2, footer_y), t, font=font, fill=1)

# ------------------------
# Tamagotchi (lock screen sans stats affichées)
# ------------------------
def draw_tamagotchi():
    clear_screen()
    # Calcule la taille max pour centrer le sprite
    base = 16
    # espace haut/bas pour footer
    reserved = 10 + 10  # marge haute pour potentiel header + footer
    scale_w = max(1, width // base)
    scale_h = max(1, (height - reserved) // base)
    scale = max(1, min(scale_w, scale_h))
    sprite = mascotte_IDLE_1 if tama_eye_open else mascotte_IDLE_2
    sprite_w = base * scale
    sprite_h = base * scale
    sx = (width - sprite_w) // 2
    sy = (height - sprite_h) // 2 - 4
    draw_bitmap_scaled(sx, sy, sprite, scale=scale)
    # footer discret
    draw_footer("BACK:Unlock  +/-:Lum")
    lcd_display()

def animate_tamagotchi():
    global tama_eye_open
    tama_eye_open = not tama_eye_open
    draw_tamagotchi()

# ------------------------
# Menu principal
# ------------------------
def draw_menu():
    clear_screen()
    # header simple (heure + luminosité)
    draw.rectangle((0,0,width,10), fill=1)
    draw.text((4,1), time.strftime("%H:%M"), font=font, fill=0)
    draw.text((width-36,1), f"L:{brightness}", font=font, fill=0)

    # liste centrée verticalement (espacement sûr pour 128x64)
    entry_h = 12
    max_area_h = height - 18
    visible_count = min(len(MENU_ITEMS), max_area_h // entry_h)
    start_y = 10 + ((max_area_h - (visible_count * entry_h)) // 2)

    # rendre la sélection visible (scroll si besoin)
    first_visible = max(0, min(current_index - visible_count//2, len(MENU_ITEMS)-visible_count))
    for v in range(visible_count):
        idx = first_visible + v
        if idx >= len(MENU_ITEMS): break
        name, _ = MENU_ITEMS[idx]
        y = start_y + v*entry_h
        invert = (idx == current_index)
        if invert:
            draw.rectangle((0,y,width,y+11), fill=1)
            draw.text((6,y), name, font=font, fill=0)
        else:
            draw.text((6,y), name, font=font, fill=1)

    draw_footer("BACK:Lock  OK:Run  +/-:Lum")
    lcd_display()

# ------------------------
# Affichage output (résultats)
# ------------------------
def draw_output():
    clear_screen()
    draw.rectangle((0,0,width,10), fill=1)
    draw.text((4,1), time.strftime("%H:%M"), font=font, fill=0)
    draw.text((width-36,1), f"L:{brightness}", font=font, fill=0)
    top = 12
    for i in range(OUTPUT_LINES_PER_PAGE):
        idx = output_offset + i
        if idx >= len(output_lines): break
        draw.text((4, top + i*10), output_lines[idx], font=font, fill=1)
    draw_footer("<BACK menu>  +/- Lum  U/D Scroll")
    lcd_display()

# ------------------------
# Loading (barre)
# ------------------------
def draw_loading_screen(title="Loading...", seconds=1.0):
    steps = 12
    delay = max(0.01, seconds / steps)
    clear_screen()
    draw.text((4,8), title, font=font, fill=1)
    bar_x, bar_y = 8, 34
    bar_w, bar_h = width - 16, 6
    for s in range(steps+1):
        draw.rectangle((bar_x-1,bar_y-1,bar_x+bar_w+1,bar_y+bar_h+1), outline=1, fill=0)
        fill_w = int((s/steps) * bar_w)
        if fill_w > 0:
            draw.rectangle((bar_x, bar_y, bar_x+fill_w, bar_y+bar_h), fill=1)
        lcd_display()
        time.sleep(delay)

# ------------------------
# Exécuteur capture stdout/stderr
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
    max_chars = 20
    for line in text.splitlines():
        for i in range(0, len(line), max_chars):
            lines.append(line[i:i+max_chars])
    if not lines:
        lines = ["<no output>"]
    return lines

# ------------------------
# Touch handler (0=Up,1=Down,2=Back,3=-,4=OK,5=+)
# ------------------------
def handler(ch, event):
    global current_index, mode, output_offset, brightness, output_lines, sequence

    if event != "press": return

    # si on affiche les résultats
    if mode == "output":
        if ch == 0:
            output_offset = max(0, output_offset - 1); draw_output(); return
        elif ch == 1:
            max_off = max(0, len(output_lines) - OUTPUT_LINES_PER_PAGE)
            output_offset = min(max_off, output_offset + 1); draw_output(); return
        elif ch == 2:
            mode = "menu"; draw_menu(); return
        elif ch == 5:
            brightness = min(255, brightness + 16); backlight.set_all(brightness, brightness, brightness); backlight.show(); draw_output(); return
        elif ch == 3:
            brightness = max(0, brightness - 16); backlight.set_all(brightness, brightness, brightness); backlight.show(); draw_output(); return

    # bloquer les entrées pendant loading
    if mode == "loading": return

    # ---- lock / écran de code de triche (sans afficher le mdp) ----
    if mode in ("lock", "unlock_confirm"):
        if ch == 2:  # BACK -> passer à l'invite de code sans afficher la séquence
            mode = "loading"
            draw_loading_screen("Chargement...", seconds=0.6)
            mode = "unlock_confirm"
            clear_screen()
            # Nouveau texte demandé : "Code de triche ?"
            draw.text((8, height//2 - 12), "Code de triche ?", font=font, fill=1)
            # footer discret indiquant la manière d'entrer (sans montrer le mdp)
            draw_footer("U/D pour saisir  BACK:Retour")
            lcd_display()
            sequence = []
            return

        # interactions rapides sur lock: cliquetis, animation
        if ch == 4:
            # simple interaction visuelle : cligne
            animate_tamagotchi(); return
        elif ch == 5:
            # luminosité up depuis lock
            brightness = min(255, brightness+16)
            backlight.set_all(brightness, brightness, brightness); backlight.show(); draw_tamagotchi(); return
        elif ch == 3:
            brightness = max(0, brightness-16)
            backlight.set_all(brightness, brightness, brightness); backlight.show(); draw_tamagotchi(); return

        # pendant la saisie du code : on **n'affiche jamais la séquence**
        if mode == "unlock_confirm":
            if ch == 0:
                sequence.append('U')
            elif ch == 1:
                sequence.append('D')
            # ne garder que les 3 derniers
            if len(sequence) > 3:
                sequence = sequence[-3:]

            # feedback minimal : on réaffiche juste l'invite (pas de mdp)
            clear_screen()
            draw.text((8, height//2 - 12), "Code de triche ?", font=font, fill=1)
            draw_footer("U/D pour saisir  BACK:Retour")
            lcd_display()

            # si la séquence est correcte -> ouvrir le menu
            if len(sequence) == 3 and sequence == ['U','D','U']:
                mode = "loading"
                draw_loading_screen("Ouverture...", seconds=0.8)
                mode = "menu"
                sequence = []
                draw_menu()
            return

        # si on est resté en lock (autres touches), on réaffiche le tama
        if mode == "lock":
            draw_tamagotchi()
        return

    # ---- interactions menu ----
    if mode == "menu":
        if ch == 0:
            current_index = (current_index - 1) % len(MENU_ITEMS); draw_menu(); return
        elif ch == 1:
            current_index = (current_index + 1) % len(MENU_ITEMS); draw_menu(); return
        elif ch == 4:
            name, path = MENU_ITEMS[current_index]
            if name.lower().startswith("exit"):
                try:
                    subprocess.run(["python3", path])
                except Exception:
                    pass
                cleanup(); sys.exit(0)
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
            draw_loading_screen("Verrouillage...", seconds=0.5)
            mode = "lock"
            draw_tamagotchi()
            return
        elif ch == 5:
            brightness = min(255, brightness + 16); backlight.set_all(brightness, brightness, brightness); backlight.show(); draw_menu(); return
        elif ch == 3:
            brightness = max(0, brightness - 16); backlight.set_all(brightness, brightness, brightness); backlight.show(); draw_menu(); return

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
            # menu redessiné par handler quand nécessaire
            time.sleep(0.2)
        elif mode == "output":
            time.sleep(0.2)
        elif mode == "unlock_confirm":
            time.sleep(0.2)
        elif mode == "loading":
            time.sleep(0.1)
        else:
            time.sleep(0.2)
except KeyboardInterrupt:
    cleanup()
    sys.exit(0)
