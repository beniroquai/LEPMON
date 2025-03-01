# Bibliotheken laden
import serial
from gpiozero import LED
import time
import adafruit_ds3231
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106, ssd1306
from PIL import ImageFont, ImageDraw, Image
import json

#
print("Skript LED_001")
#
##
with open('/home/Ento/Lepmon_Einstellungen/LepmonCode.json') as f:
    data = json.load(f)
sensor_id = data["sensor_id"]
print(sensor_id)
##
gelb = LED(22)

Display = i2c(port=1, address=0x3C)
oled = sh1106(Display)

oled_font = ImageFont.truetype('FreeSans.ttf', 14)

try:
    uart = serial.Serial("/dev/serial0", 9600, timeout=1)
    print("Lora Sender initialisiert")
except Exception as e:
    print(f"Warnung: Lora Sender nicht initialisiert: {e}")
    pass

with canvas(oled) as draw:
    draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
    draw.text((5, 5), "Willkommen...", font = oled_font, fill = "white")
    draw.text((5, 30), "Laden... 1/3", font = oled_font, fill = "white")

start_message =f"Lepmon#{sensor_id} Falle eingeschaltet"

try:
    uart.write(start_message.encode('utf-8') + b'\n') 
except:
    print("Lora Message nicht gesendet")
# LED einschalten
gelb.on()
time.sleep(.5)
gelb.off()
time.sleep(.5)

