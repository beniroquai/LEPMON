from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import ImageFont

class OLEDDisplay:
    def __init__(self, i2c_port=1, address=0x3C, font_path='FreeSans.ttf'):
        try:
            self.serial = i2c(port=i2c_port, address=address)
        except Exception as e:
            print(e)   
            self.serial = None
            return
        self.device = sh1106(self.serial)
        self.oled_font = ImageFont.truetype(font_path, 14)
        self.oled_font_large = ImageFont.truetype(font_path, 17)

    def show_message(self, lines, coords=None):
        """
        lines: list of strings to show on different lines
        coords: list of (x,y) positions for each line or None
        """
        if not self.serial:
            return
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")
            for i, text in enumerate(lines):
                if coords and i < len(coords):
                    x, y = coords[i]
                else:
                    x, y = 5, 5 + 20*i
                draw.text((x, y), text, font=self.oled_font, fill="white")
