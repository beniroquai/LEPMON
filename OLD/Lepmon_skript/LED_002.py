# Bibliotheken laden
from gpiozero import LED
import time
import adafruit_ds3231
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106, ssd1306
from PIL import ImageFont, ImageDraw, Image

#
print("Skript LED_002")
#
# Initialisierung von GPIO17 als LED (Ausgang)
gelb = LED(22)


gelb.off()
serial = i2c(port=1, address=0x3C)
oled = sh1106(serial)

oled_font = ImageFont.truetype('FreeSans.ttf', 14)

with canvas(oled) as draw:
    draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
    draw.text((5, 5), "Willkommen...", font = oled_font, fill = "white")
    draw.text((5, 30), "Laden... 2/3", font = oled_font, fill = "white")

gelb.on()
time.sleep(.5)
gelb.off()
time.sleep(.5)
gelb.on()
time.sleep(.5)
gelb.off()