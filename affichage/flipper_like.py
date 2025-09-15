#!/usr/bin/env python3
# flipper_like_callbacks.py
# Menu style Flipper Zero pour GFX HAT avec callbacks tactiles

import time
import sys
import atexit
from gfxhat import touch, lcd, backlight, fonts
from PIL import Image, ImageFont, ImageDraw

width, height = lcd.dimensions()

# Police pixel Flipper style
try:
    font = ImageFont.truetype(fonts.BitbuntuFull, 10)
except:
    font = ImageFont.load_default()

image = Image.new('P', (width, height))
draw = ImageDraw.Draw(image)

# --- menu ---
class MenuOption:
    def __init__(self, name, action=None, args=()):
        self.name = name
        self.action = action
        self.args = args

    def trigger(self):
        if self.action:
            self.action(*self.args)

# Exemple d’actions : changer backlight ou rien
def set_backlight(r, g, b):
    backlight.set_all(r, g, b)
    backlight.show()

menu_options = [
    MenuOption("Applications"),
    MenuOption("Radio"),
    MenuOption("Infrared"),
    MenuOption("NFC"),
    MenuOption("Settings"),
    MenuOption("Exit", sys.exit, (0,))
]

current_menu_option = 0
trigger_action = False

# --- callback des boutons ---
def handler(ch, event):
    global current_menu_option, trigger_action
    if event != "press":
        return
    if ch == 0:  # bouton haut
        current_menu_option -= 1
    elif ch == 1:  # bouton bas
        current_menu_option += 1
    elif ch == 4:  # ok
        trigger_action = True
    current_menu_option %= len(menu_options)

# Attacher les callbacks
for i in range(6):
    touch.set_led(i, 0)
    backlight.set_pixel(i, 255, 255, 255)
    touch.on(i, handler)

backlight.show()

# --- cleanup ---
def cleanup():
    backlight.set_all(0, 0, 0)
    backlight.show()
    lcd.clear()
    lcd.show()

atexit.register(cleanup)

# --- boucle principale ---
try:
    while True:
        image.paste(0, (0, 0, width, height))
        offset_top = 0

        if trigger_action:
            menu_options[current_menu_option].trigger()
            trigger_action = False

        # Calcul de l’offset pour centrer le menu
        for i in range(current_menu_option):
            offset_top += 12

        # Dessin du menu
        for idx, option in enumerate(menu_options):
            x = 10
            y = (idx * 12) + (height // 2) - 4 - offset_top
            if idx == current_menu_option:
                draw.rectangle(((x-2, y-1), (width, y+10)), 1)
            draw.text((x, y), option.name, 0 if idx == current_menu_option else 1, font)

        # Petit chevron
        w, h = font.getsize(">")
        draw.text((0, (height - h) // 2), ">", 1, font)

        # Bandeau supérieur : heure
        draw.rectangle((0,0,width,9), fill=1)
        draw.text((4,1), time.strftime("%H:%M"), font=font, fill=0)

        # Convertir Image → lcd
        pixels = image.load()
        for y in range(height):
            for x in range(width):
                lcd.set_pixel(x, y, pixels[x,y])

        lcd.show()
        time.sleep(1.0/30)

except KeyboardInterrupt:
    cleanup()
