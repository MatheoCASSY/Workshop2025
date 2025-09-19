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
except:
    font = ImageFont.load_default()
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# ------------------------
# Icônes menu
# ------------------------
ICONS = {
    "Wi-Fi Scan": ["00100","01010","10001","00000","00100","00000","00100","00000"],
    "Port Scan":  ["11111","10001","10101","10001","11111","00000","00000","00000"],
    "Keylogger Sim": ["01010","10101","01010","10101","01010","00000","01010","00000"],
    "NFC Sim":    ["00100","01010","00100","01010","00100","00000","00100","00000"],
    "Exit":       ["11111","10001","11111","10000","11111","00000","00000","00000"]
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
# Sprite Tamagotchi
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
# Utils dessin
# ------------------------
def cleanup():
    try:
        backlight.set_all(0,0,0); backlight.show()
        lcd.clear(); lcd.show()
    except: pass
atexit.register(cleanup)

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
                draw.rectangle((x+rx*scale,y+ry*scale,x+(rx+1)*scale-1,y+(ry+1)*scale-1),fill=1)

def draw_footer(txt):
    draw.text((2,height-9),txt,font=font,fill=1)

def draw_text_centered(txt):
    w=draw.textlength(txt,font=font)
    draw.text(((width-w)//2,height//2-5),txt,font=font,fill=1)

# ------------------------
# Loading screen
# ------------------------
def draw_loading_screen(title="Loading...",seconds=0.8):
    steps=16; delay=seconds/steps
    draw.rectangle((0,0,width,height),fill=0)
    draw.text((4,8),title,font=font,fill=1)
    bar_x,bar_y=6,30; bar_w=width-12; bar_h=8
    for s in range(steps+1):
        draw.rectangle((bar_x-1,bar_y-1,bar_x+bar_w+1,bar_y+bar_h+1),outline=1)
        fill=int((s/steps)*bar_w)
        if fill>0: draw.rectangle((bar_x,bar_y,bar_x+fill,bar_y+bar_h),fill=1)
        draw_image_to_lcd(); time.sleep(delay)

# ------------------------
# Écran lock (Tamagotchi)
# ------------------------
def draw_tamagotchi():
    draw.rectangle((0,0,width,height),fill=0)
    sprite=mascotte_IDLE_1 if tama_eye_open else mascotte_IDLE_2
    scale=3
    sx=(width-(16*scale))//2; sy=(height-(16*scale))//2-4
    draw_bitmap_scaled(sx,sy,sprite,scale)
    draw_footer("BACK: Code de triche  +/-:Lum")
    draw_image_to_lcd()

def animate_tamagotchi():
    global tama_eye_open
    tama_eye_open=not tama_eye_open
    draw_tamagotchi()

def draw_unlock_prompt():
    draw.rectangle((0,0,width,height),fill=0)
    draw_text_centered("Code de triche ?")
    draw_image_to_lcd()

# ------------------------
# Menu style Flipper Zero
# ------------------------
def draw_menu():
    draw.rectangle((0,0,width,height),fill=0)
    draw.rectangle((0,0,width,9),fill=1)
    draw.text((4,1),time.strftime("%H:%M"),font=font,fill=0)
    draw.text((width-36,1),f"L:{brightness}",font=font,fill=0)
    entry_h=12
    start_y=14
    for idx,(name,_) in enumerate(MENU_ITEMS):
        y=start_y+idx*entry_h
        invert=(idx==current_index)
        if invert: draw.rectangle((18,y-1,width-2,y+10),fill=1)
        icon=ICONS.get(name,["00000"]*8)
        for ry,row in enumerate(icon):
            for rx,ch in enumerate(row):
                if ch=="1": draw.point((2+rx,y+ry),0 if invert else 1)
        draw.text((20,y),name,font=font,fill=0 if invert else 1)
    draw.text((0,(height-font.getbbox('>')[3])//2),">",font=font,fill=1)
    draw_footer("BACK:Lock  OK:Lancer  +/-:Lum  U/D:Nav")
    draw_image_to_lcd()

# ------------------------
# Output screen
# ------------------------
def draw_output():
    draw.rectangle((0,0,width,height),fill=0)
    draw.rectangle((0,0,width,9),fill=1)
    draw.text((4,1),time.strftime("%H:%M"),font=font,fill=0)
    top=12
    for i in range(OUTPUT_LINES_PER_PAGE):
        idx=output_offset+i
        if idx>=len(output_lines): break
        draw.text((4,top+i*10),output_lines[idx],font=font,fill=1)
    draw_footer("BACK:Menu  +/-:Lum  U/D:Scroll")
    draw_image_to_lcd()

# ------------------------
# Run script + capture
# ------------------------
def run_script_capture(path):
    try:
        proc=subprocess.run(["python3",path],capture_output=True,text=True,timeout=30)
        out=proc.stdout or ""; err=proc.stderr or ""
        text=out+("\nERR:\n"+err if err else "")
    except Exception as e:
        text="Error: "+str(e)
    lines=[]
    for line in text.splitlines():
        for i in range(0,len(line),20):
            lines.append(line[i:i+20])
    return lines or ["<no output>"]

# ------------------------
# Handler touches
# ------------------------
def handler(ch,event):
    global mode,sequence,current_index,tama_eye_open,brightness,output_lines,output_offset
    if event!="press": return

    # ---- LOCK ----
    if mode=="lock":
        if ch==2:
            draw_loading_screen("Chargement...",0.8)
            mode="unlock_confirm"; sequence=[]; draw_unlock_prompt(); return
        elif ch==4:
            tama_eye_open=not tama_eye_open; draw_tamagotchi(); return
        elif ch==5:
            brightness=min(255,brightness+16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_tamagotchi(); return
        elif ch==3:
            brightness=max(0,brightness-16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_tamagotchi(); return

    # ---- UNLOCK ----
    elif mode=="unlock_confirm":
        if ch==0: sequence.append("U")
        elif ch==1: sequence.append("D")
        if len(sequence)>3: sequence=sequence[-3:]
        draw_unlock_prompt()
        if sequence==["U","D","U"]:
            draw_loading_screen("Ouverture...",0.8)
            mode="menu"; draw_menu(); return

    # ---- MENU ----
    elif mode=="menu":
        if ch==2:
            draw_loading_screen("Verrouillage...",0.6)
            mode="lock"; draw_tamagotchi(); return
        elif ch==0:
            current_index=(current_index-1)%len(MENU_ITEMS); draw_menu(); return
        elif ch==1:
            current_index=(current_index+1)%len(MENU_ITEMS); draw_menu(); return
        elif ch==4:
            name,path=MENU_ITEMS[current_index]
            if name=="Exit": cleanup(); sys.exit(0)
            draw_loading_screen(f"Lancement: {name}",1.0)
            output_lines=run_script_capture(path); output_offset=0
            mode="output"; draw_output(); return
        elif ch==5:
            brightness=min(255,brightness+16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_menu(); return
        elif ch==3:
            brightness=max(0,brightness-16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_menu(); return

    # ---- OUTPUT ----
    elif mode=="output":
        if ch==2: mode="menu"; draw_menu(); return
        elif ch==0: output_offset=max(0,output_offset-1); draw_output(); return
        elif ch==1: output_offset=min(len(output_lines)-OUTPUT_LINES_PER_PAGE,max(0,output_offset+1)); draw_output(); return
        elif ch==5: brightness=min(255,brightness+16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_output(); return
        elif ch==3: brightness=max(0,brightness-16); backlight.set_all(brightness,brightness,brightness); backlight.show(); draw_output(); return

# ------------------------
# Init
# ------------------------
for i in range(6):
    try: touch.on(i,handler)
    except: pass
backlight.set_all(brightness,brightness,brightness); backlight.show()

# ------------------------
# Main loop
# ------------------------
draw_tamagotchi()
try:
    while True:
        if mode=="lock": animate_tamagotchi(); time.sleep(0.5)
        elif mode in ("menu","output","unlock_confirm"): time.sleep(0.2)
        elif mode=="loading": time.sleep(0.1)
except KeyboardInterrupt:
    cleanup(); sys.exit(0)
