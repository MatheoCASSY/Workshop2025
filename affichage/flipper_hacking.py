#!/usr/bin/env python3

import time, sys, atexit
from gfxhat import lcd, backlight, touch, fonts
from PIL import Image, ImageFont, ImageDraw

# ------------------------
# Setup
# ------------------------
width, height = lcd.dimensions()
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
try:
    font = ImageFont.truetype(fonts.BitbuntuFull, 10)
except:
    font = ImageFont.load_default()

brightness = 128
backlight.set_all(brightness, brightness, brightness)
backlight.show()

# ------------------------
# Tamagotchi State
# ------------------------
tama_hunger = 5
tama_happiness = 5
tama_cleanliness = 5
tama_eye_open = True
tama_mouth_open = False

# ------------------------
# UI State
# ------------------------
mode = "lock"        # lock / unlock_confirm / menu / output
sequence = []        # pour la combinaison haut-bas-haut
trigger_action = False
current_index = 0
OUTPUT_LINES_PER_PAGE = 5
output_lines = []
output_offset = 0

MENU_ITEMS = [
    ("Wi-Fi Scan", None),
    ("Port Scan", None),
    ("Keylogger Sim", None),
    ("NFC Sim", None),
    ("Exit", None)
]

# ------------------------
# Helpers
# ------------------------
def cleanup():
    backlight.set_all(0,0,0)
    backlight.show()
    lcd.clear()
    lcd.show()
atexit.register(cleanup)

def draw_image():
    pix = image.load()
    for y in range(height):
        for x in range(width):
            lcd.set_pixel(x, y, 1 if pix[x,y] else 0)
    lcd.show()

# ------------------------
# Tamagotchi Drawing
# ------------------------
def draw_tamagotchi():
    global tama_eye_open, tama_mouth_open
    draw.rectangle((0,0,width,height), fill=0)
    draw.text((2,0), f"H:{tama_hunger} P:{tama_happiness} C:{tama_cleanliness}", font=font, fill=1)
    # Corps simple
    draw.ellipse((40,20,60,40), fill=1)
    # Yeux
    if tama_eye_open:
        draw.point((45,25), fill=0)
        draw.point((55,25), fill=0)
    else:
        draw.line((45,25,46,25), fill=0)
        draw.line((55,25,56,25), fill=0)
    # Bouche
    if tama_mouth_open:
        draw.line((45,35,55,35), fill=0)
    else:
        draw.line((45,36,55,36), fill=0)
    draw.text((2, height-9), "OK=Action  +/- : Feed/Play", font=font, fill=1)
    draw_image()

def animate_tamagotchi():
    global tama_eye_open, tama_mouth_open
    # Clignement
    tama_eye_open = not tama_eye_open
    # Bouche qui bouge
    tama_mouth_open = not tama_mouth_open
    draw_tamagotchi()

# ------------------------
# Menu Drawing
# ------------------------
def draw_menu():
    draw.rectangle((0,0,width,height), fill=0)
    draw.text((4,1), "Menu", font=font, fill=1)
    start_y = 12
    for idx, (name, _) in enumerate(MENU_ITEMS):
        invert = (idx == current_index)
        if invert:
            draw.rectangle((0, start_y+idx*12, width, start_y+idx*12+10), fill=1)
            draw.text((4, start_y+idx*12), name, font=font, fill=0)
        else:
            draw.text((4, start_y+idx*12), name, font=font, fill=1)
    draw_image()

# ------------------------
# Touch Handler
# ------------------------
def touch_handler(ch, event):
    global mode, sequence, trigger_action, current_index
    global tama_hunger, tama_happiness, tama_cleanliness

    if event != "press": return

    if mode == "lock":
        if ch == 0:  # Up
            sequence.append('U')
            draw.rectangle((0,0,width,height), fill=0)
            draw.text((10, height//2-5), "Déverrouiller l'appareil ?", font=font, fill=1)
            draw_image()
        elif ch == 1:  # Down
            sequence.append('D')
        elif ch == 4:  # OK : interaction avec Tamagotchi
            tama_hunger = max(0, tama_hunger-1)
            tama_happiness = min(10, tama_happiness+1)
            draw_tamagotchi()
        elif ch == 5:  # + nourrir
            tama_hunger = max(0, tama_hunger-1)
            draw_tamagotchi()
        elif ch == 3:  # - jouer
            tama_happiness = min(10, tama_happiness+1)
            draw_tamagotchi()

        # Check sequence: Up -> Down -> Up
        if sequence[-3:] == ['U','D','U']:
            mode = "menu"
            sequence.clear()
            draw_menu()
        return

    if mode == "menu":
        if ch == 0:  # Up
            current_index = (current_index-1)%len(MENU_ITEMS)
            draw_menu()
        elif ch == 1:  # Down
            current_index = (current_index+1)%len(MENU_ITEMS)
            draw_menu()
        elif ch == 4:  # OK
            name, _ = MENU_ITEMS[current_index]
            if name == "Exit":
                mode = "lock"
                # reset Tamagotchi
                tama_hunger = 5
                tama_happiness = 5
                tama_cleanliness = 5
                draw_tamagotchi()
            else:
                # placeholder pour action des scripts
                draw.rectangle((0,0,width,height), fill=0)
                draw.text((4,10), f"Exécution {name}", font=font, fill=1)
                draw_image()
        elif ch == 2:  # Back
            mode = "lock"
            draw_tamagotchi()

for i in range(6):
    try: touch.on(i, touch_handler)
    except: pass

# ------------------------
# Main Loop
# ------------------------
draw_tamagotchi()

try:
    while True:
        if mode == "lock":
            animate_tamagotchi()
        time.sleep(0.5)
except KeyboardInterrupt:
    cleanup()
    sys.exit(0)
