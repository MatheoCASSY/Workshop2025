#!/usr/bin/env python3
# flipper_hacking.py
# Menu Flipper-like pour GFX HAT
# - icônes dessinées dans l'image PIL
# - sélection bien visible (inversion)
# - exécution des scripts et affichage de la sortie sur l'écran (avec scroll)

import time
import sys
import atexit
import subprocess
from os.path import expanduser
from gfxhat import lcd, backlight, touch, fonts
from PIL import Image, ImageFont, ImageDraw

# --- Configuration / chemins ---
HOME = expanduser("~")
SCRIPTS_DIR = HOME + "/projet/scripts"
# menu (nom affiché, script relatif)
MENU_ITEMS = [
    ("Wi-Fi Scan", SCRIPTS_DIR + "/wifi_scan.py"),
    ("Port Scan", SCRIPTS_DIR + "/port_scan.py"),
    ("Keylogger Sim", SCRIPTS_DIR + "/keylogger_sim.py"),
    ("NFC Sim", SCRIPTS_DIR + "/nfc_sim.py"),
    ("Exit", SCRIPTS_DIR + "/exit_script.py"),
]

# --- initialisation écran / police ---
width, height = lcd.dimensions()
# util: police fournie par gfxhat fonts (Bitbuntu)
try:
    font = ImageFont.truetype(fonts.BitbuntuFull, 10)
except Exception:
    font = ImageFont.load_default()

# image PIL en 1-bit (mode '1') pour simplicité
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# --- icônes monochromes (chaque ligne est une chaîne de '0'/'1') ---
# Icônes de largeur variable (ici ~5x8) — on les dessinera avec draw.point
ICONS = {
    "Wi-Fi Scan": [
        "00100",
        "01010",
        "10001",
        "00000",
        "00100",
        "00000",
        "00100",
        "00000"
    ],
    "Port Scan": [
        "11111",
        "10001",
        "10101",
        "10001",
        "11111",
        "00000",
        "00000",
        "00000"
    ],
    "Keylogger Sim": [
        "01010",
        "10101",
        "01010",
        "10101",
        "01010",
        "00000",
        "01010",
        "00000"
    ],
    "NFC Sim": [
        "00100",
        "01010",
        "00100",
        "01010",
        "00100",
        "00000",
        "00100",
        "00000"
    ],
    "Exit": [
        "11111",
        "10001",
        "10101",
        "10001",
        "11111",
        "00000",
        "00000",
        "00000"
    ]
}

# --- état du menu / affichage ---
current_index = 0
trigger_action = False

# mode d'affichage : "menu" ou "output"
mode = "menu"
output_lines = []     # liste de lignes (texte) à afficher
output_offset = 0     # index de la première ligne affichée
OUTPUT_LINES_PER_PAGE = 5  # ajustable selon taille police

# --- helper : dessine une icone PIL à x_offset,y_offset ---
def draw_icon_on_image(x_offset, y_offset, icon):
    # icon : liste de strings '0'/'1'
    for ry, row in enumerate(icon):
        for rx, ch in enumerate(row):
            if ch == "1":
                px = x_offset + rx
                py = y_offset + ry
                if 0 <= px < width and 0 <= py < height:
                    draw.point((px, py), 1)  # allume point noir (1)

# --- exécution d'un script et capture de sortie (retourne liste de lignes) ---
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
    # découper en lignes et limiter longueur par ligne si besoin
    lines = []
    for line in text.splitlines():
        # coupe les lignes trop longues pour l'écran (~18-20 chars selon police)
        max_chars = 20
        if len(line) <= max_chars:
            lines.append(line)
        else:
            # découpe propre
            for i in range(0, len(line), max_chars):
                lines.append(line[i:i+max_chars])
    if not lines:
        lines = ["<no output>"]
    return lines

# --- callback tactile ---
def handler(ch, event):
    global current_index, trigger_action, mode, output_offset
    if event != "press":
        return
    # si on est en mode output, gérer scroll / retour
    if mode == "output":
        if ch == 0:  # up -> scroll up
            output_offset = max(0, output_offset - 1)
        elif ch == 1:  # down -> scroll down
            # limite
            max_off = max(0, len(output_lines) - OUTPUT_LINES_PER_PAGE)
            output_offset = min(max_off, output_offset + 1)
        elif ch == 5:  # back -> retour menu
            mode = "menu"
        return

    # mode menu
    if ch == 0:  # up
        current_index -= 1
    elif ch == 1:  # down
        current_index += 1
    elif ch == 4:  # ok
        trigger_action = True
    current_index %= len(MENU_ITEMS)

# attacher callbacks et config LED/backlight initiale
for i in range(6):
    try:
        touch.set_led(i, 0)
    except Exception:
        pass
    try:
        backlight.set_pixel(i, 255, 255, 255)
    except Exception:
        pass
    try:
        touch.on(i, handler)
    except Exception:
        # si touch.on fail -> on ne crash pas (mais alors le HAT n'est pas utilisable)
        pass
backlight.show()

# cleanup
def cleanup():
    backlight.set_all(0,0,0)
    backlight.show()
    lcd.clear()
    lcd.show()
atexit.register(cleanup)

# --- fonction redraw unique (gère menu et affichage de sortie) ---
def redraw():
    # nettoie l'image PIL
    draw.rectangle((0,0,width,height), fill=0)  # fond noir (0 = éteint)
    # bandeau supérieur (inversé : fond blanc, texte noir)
    draw.rectangle((0,0,width,9), fill=1)
    draw.text((4,1), time.strftime("%H:%M"), font=font, fill=0)

    if mode == "menu":
        # dessiner menu
        # on affiche les éléments centrés verticalement, avec zone de 12px par option
        start_y = (height // 2) - 4
        offset_top = 0
        # calcul offset pour centrer la sélection
        for i in range(current_index):
            offset_top += 12

        for idx, (name, path) in enumerate(MENU_ITEMS):
            y = (idx * 12) + start_y - offset_top
            # icone à gauche (place à x=4)
            icon = ICONS.get(name, ["00000"]*8)
            # si sélection : dessiner rectangle rempli blanc (1) puis texte noir (0)
            if idx == current_index:
                # rectangle rempli = inversion
                draw.rectangle(((20-4, y-1), (width, y+10)), fill=1)
                # dessiner l'icône en noir (0) on la peint en 0 by drawing filled rect then clearing points:
                # easiest: draw icon as black by drawing small rectangle over (since background white)
                # but draw_icon_on_image draws points=1 (black) — we want black on white; since our image mode is 1,
                # 1 is white (on) and 0 is black (off)? To be consistent: earlier we filled rectangle with 1 to make white,
                # and text with fill=0 to make black. So draw_icon_on_image must draw 0 for icon when selected.
                # We'll draw icon manually here:
                for ry, row in enumerate(icon):
                    for rx, c in enumerate(row):
                        px = 2 + rx
                        py = y + ry
                        if 0 <= px < width and 0 <= py < height:
                            if c == "1":
                                # set black pixel on white background = 0
                                draw.point((px, py), 0)
                # texte en noir
                draw.text((20, y), name, font=font, fill=0)
            else:
                # non sélection : fond noir, texte blanc
                # dessine icône en blanc (1)
                for ry, row in enumerate(icon):
                    for rx, c in enumerate(row):
                        px = 2 + rx
                        py = y + ry
                        if 0 <= px < width and 0 <= py < height:
                            if c == "1":
                                draw.point((px, py), 1)
                draw.text((20, y), name, font=font, fill=1)

        # chevron à gauche
        w, h = font.getsize(">")
        draw.text((0, (height - h) // 2), ">", font=font, fill=1)

    elif mode == "output":
        # affichage de la sortie capturée (titre et lignes texte)
        title = "Output"
        draw.text((4, 1), time.strftime("%H:%M"), font=font, fill=0)  # sur bandeau, time noir on white
        # zone texte
        top = 12
        # dessiner plusieurs lignes à partir de output_offset
        for i in range(OUTPUT_LINES_PER_PAGE):
            idx = output_offset + i
            if idx >= len(output_lines):
                break
            line = output_lines[idx]
            draw.text((4, top + i * 10), line, font=font, fill=1)

        # petit hint bas
        hint = "<BACK pour revenir>"
        draw.text((4, height - 9), hint, font=font, fill=1)

    # Convertir PIL -> lcd (pixel par pixel)
    pixels = image.load()
    for yy in range(height):
        for xx in range(width):
            # PIL mode '1' -> pixels[xx,yy] is 0 (off) or 255? For '1' returns 0/255. Use truthiness.
            val = 1 if pixels[xx, yy] else 0
            lcd.set_pixel(xx, yy, val)
    lcd.show()

# initial draw
redraw()

# --- boucle principale gestion trigger_action ---
try:
    while True:
        if trigger_action and mode == "menu":
            # exécuter l'élément choisi ; si Exit, quitter proprement
            name, path = MENU_ITEMS[current_index]
            # special Exit handler: si Exit, lance script qui fait sys.exit ou on quitte localement
            if name.lower().startswith("exit"):
                # tente d'exécuter le script exit (pour compatibilité), sinon quitte
                try:
                    subprocess.run(["python3", path])
                except Exception:
                    pass
                cleanup()
                sys.exit(0)

            # exécuter et capturer sortie
            output_lines = run_script_capture(path)
            output_offset = 0
            mode = "output"
            trigger_action = False
            # redraw immédiat
            redraw()
        else:
            # normale: juste redraw périodique (pour l'heure + leds)
            redraw()
            time.sleep(1.0 / 10.0)

except KeyboardInterrupt:
    cleanup()
