# Bibliotheken laden
from gpiozero import LED
import time 
import adafruit_ds3231
import json
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106, ssd1306
from PIL import ImageFont, ImageDraw, Image
import os
import serial

#
print("Skript LED_003")
#

# Initialisierung von GPIO17 als LED (Ausgang)
led = LED(17)
Display = i2c(port=1, address=0x3C)
oled = sh1106(Display)

oled_font = ImageFont.truetype('FreeSans.ttf', 14)


try:
    uart = serial.Serial("/dev/serial0", 9600, timeout=1)
    print("Lora Sender initialisiert")
except Exception as e:
    print(f"Warnung: Lora Sender nicht initialisiert: {e}")
    pass


with open('/home/Ento/Lepmon_Einstellungen/LepmonCode.json') as f:
    data = json.load(f)
sensor_id = data["sensor_id"]

#Fehlercode lesen
try:
    with open("/home/Ento/Lepmon_skript/FehlerNummer.json", "r") as json_file:
        data = json.load(json_file)
        Fehler =  data.get("Fehler_code",None)
        os.remove("/home/Ento/Lepmon_skript/FehlerNummer.json") 

except:
    Fehler = "unbekannt"
    
try:
    with open("/home/Ento/Lepmon_skript/error_messages.json", "r") as msg:
        error_messages = json.load(msg)

except:
    error_messages = {}

text = error_messages.get(str(Fehler),["  Unbekannter","      Fehler",""])

with canvas(oled) as draw:
        draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
        draw.text((15, 5), f"{text[0]}", font = oled_font, fill = "white")
        draw.text((15, 25), f"{text[1]}", font = oled_font, fill = "white")
        draw.text((15, 45), f"{text[2]}", font = oled_font, fill = "white")
        
Fehler_message = "\n".join([
        f"Lepmon#{sensor_id}",
        f" Falle hat einen kritischen Fehler:",
        f"",
        f"{text[0]}",
        f"{text[1]}",
        f"{text[2]}"
        ])

try:
    uart.write(Fehler_message.encode('utf-8') + b'\n') 
except Exception as e: 
    print(f"Lora Message nicht gesendet: {e}")
    
    
for i in range(40):
    led.on()
    time.sleep(.1875)
    led.off()
    time.sleep(.125)
    led.on()
    time.sleep(.1875)
    led.off()    
    time.sleep(1)
    
    
with canvas(oled) as draw:
        draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
        draw.text((15, 25), "Starte neu...", font = oled_font, fill = "white")
Fehler_message =  f"Lepmon#{sensor_id}: Falle startet neu"

try:
    uart.write(Fehler_message.encode('utf-8') + b'\n') 
except:
    print("Lora Message nicht gesendet")
    

time.sleep(5)

with canvas(oled) as draw:
        draw.rectangle(oled.bounding_box, outline = "white", fill = "white")
                
os.system('sudo reboot')
