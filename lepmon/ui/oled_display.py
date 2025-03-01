from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import ImageFont, Image

class OLEDDisplay:
    def __init__(self, i2c_port=1, address=0x3C, font_path='FreeSans.ttf', font_size=14, font_size_large=17,
                 logo_path='/home/Ento/Lepmon_skript/logo_small.png'):
        try:
            self.serial = i2c(port=i2c_port, address=address)
            self.device = sh1106(self.serial)
        except Exception as e:
            print("OLED init error:", e)
            self.serial = None
            self.device = None
            return
        
        self.oled_font = ImageFont.truetype(font_path, font_size)
        self.oled_font_large = ImageFont.truetype(font_path, font_size_large)
        self.logo = None
        try:
            self.logo = Image.open(logo_path).convert("1")
        except Exception as e:
            # Wenn das Logo nicht verfügbar ist, wird es ignoriert
            pass

    def clear(self):
        if not self.device:
            return
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="black", fill="black")
    
    def show_lines(self, lines, coords=None, large=False, invert=False, show_logo=False, logo_coords=(70, 30)):
        """
        lines: list of strings to display
        coords: list of (x,y) positions for each line or None for default layout
        large: if True, use the larger font
        invert: if True, invert the background (white) and text (black)
        show_logo: if True, draw the loaded logo at logo_coords
        """
        if not self.device:
            # Falls kein echtes Display vorhanden ist, nur als Fallback printen
            for line in lines:
                print("OLED:", line)
            return
        
        with canvas(self.device) as draw:
            fill_color = "black"
            text_color = "white"
            outline_color = "white"
            if invert:
                fill_color = "white"
                text_color = "black"
                outline_color = "black"

            draw.rectangle(self.device.bounding_box, outline=outline_color, fill=fill_color)
            for i, text in enumerate(lines):
                x = coords[i][0] if coords and i < len(coords) else 5
                y = coords[i][1] if coords and i < len(coords) else 5 + 20*i
                font = self.oled_font_large if large else self.oled_font
                draw.text((x, y), text, font=font, fill=text_color)
            
            if show_logo and self.logo is not None:
                draw.bitmap(logo_coords, self.logo, fill=1)

    def show_welcome_loading(self):
        lines = ["Willkommen...", "Laden... 3/3"]
        self.show_lines(lines)

    def show_welcome_logo(self):
        lines = ["Willkommen bei", "LepMon"]
        # zweite Zeile etwas tiefer (Coord)
        coords = [(5, 5), (5, 35)]
        self.show_lines(lines, coords=coords, large=True, show_logo=True)

    def show_usb_ok(self):
        lines = ["USB Stick", "richtig verbunden"]
        self.show_lines(lines)

    def show_usb_error(self):
        lines = ["Fehler 4", "USB nicht gefunden", "Falle neu starten"]
        coords = [(5, 5), (5, 25), (5, 45)]
        self.show_lines(lines, coords=coords)

    def show_menu_prompt(self):
        lines = ["Menü öffnen:", "Bitte rechte Taste", "drücken"]
        self.show_lines(lines)

    def show_menu_entered(self):
        lines = ["Eingabe Menü", "x"]
        coords = [(5, 5), (45, 5)]
        self.show_lines(lines, coords=coords)

    def show_current_time(self, time_str):
        lines = ["aktuelle Uhrzeit", time_str]
        coords = [(5, 5), (5, 25)]
        self.show_lines(lines, coords=coords)

    def show_set_time_prompt(self):
        lines = ["Uhrzeit mit ", "rechter Taste", "neu stellen"]
        coords = [(5, 5), (5, 25), (5, 45)]
        self.show_lines(lines, coords=coords)

    def show_setting_time(self):
        lines = ["Zeit und Datum", "eingeben"]
        coords = [(5, 5), (5, 25)]
        self.show_lines(lines, coords=coords)

    def show_time_updated(self):
        lines = ["Zeit aktualisiert"]
        self.show_lines(lines)

    def show_camera_test_init(self):
        lines = ["Kamera Test", "initialisieren..."]
        self.show_lines(lines)

    def show_camera_test_done(self):
        lines = ["Kamera Test", "erfolgreich beendet"]
        self.show_lines(lines)

    def show_camera_error(self):
        lines = ["Fehler 5", "Kamera", "Falle neu starten"]
        coords = [(5, 5), (5, 25), (5, 45)]
        self.show_lines(lines, coords=coords)

    def show_write_ok(self):
        lines = ["Speicherzugriff", "erfolgreich"]
        self.show_lines(lines)

    def show_sun_times(self, label, time_str):
        lines = [label, time_str]
        self.show_lines(lines)

    def show_storage_total(self, total_gb, used_percent):
        lines = ["Speicher gesamt:", "{:.1f} GB".format(total_gb)]
        self.show_lines(lines)

    def show_storage_used(self, used_gb, used_percent):
        lines = ["Speicher belegt:", "{:.1f} GB {:.1f} %".format(used_gb, used_percent)]
        self.show_lines(lines)

    def show_storage_free(self, free_gb, free_percent):
        lines = ["Speicher frei:", "{:.1f} GB {:.1f} %".format(free_gb, free_percent)]
        self.show_lines(lines)

    def show_test_finished(self):
        lines = ["Testlauf beendet", "Bitte Deckel", "schließen"]
        coords = [(5,5), (5,25), (5,45)]
        self.show_lines(lines, coords=coords)

    def show_innentemperatur(self, temp):
        lines = ["Innentemperatur", f"{temp} C"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_innensensor_error(self):
        lines = ["Fehler 1", "Innensensor"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_umgebungslicht(self, lux_value):
        lines = ["Umgebungslicht", f"{lux_value} Lux"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_lichtsensor_error(self):
        lines = ["Fehler 2", "Lichtsensor", "-sensor"]
        coords = [(5,5), (5,25), (5,45)]
        self.show_lines(lines, coords=coords)

    def show_außentemperatur(self, temp):
        lines = ["Aussentemperatur", f"{temp} C"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_luftdruck(self, pressure):
        lines = ["Luftdruck", f"{pressure} hPa"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_luftfeuchte(self, humidity):
        lines = ["Luftfeuchte", f"{humidity} %"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_aussensensor_error(self):
        lines = ["Fehler 9:", "Außensensor"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_hemisphere_prompt_nord_sued(self):
        lines = ["Knopf oben = Nord", "Knopf unten = Süd"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_hemisphere_prompt_ost_west(self):
        lines = ["Knopf oben = Ost", "Knopf unten = West"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_gps_saved(self):
        lines = ["GPS Koordinaten", "gespeichert"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_camera_test_title(self):
        self.show_lines(["Kamera Test"])

    def show_camera_shot(self):
        lines = ["Kamera Test", "Aufnahme"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_coordinates(self, lat, lng):
        lines = ["Koordinaten", f"Lat: {lat}", f"Long: {lng}"]
        coords = [(5,5), (5,25), (5,45)]
        self.show_lines(lines, coords=coords)

    def show_coordinate_prompt(self):
        lines = ["Koordinaten mit ", "rechter Taste", "neu stellen"]
        coords = [(5,5), (5,25), (5,45)]
        self.show_lines(lines, coords=coords)

    def show_enter_coords(self):
        lines = ["Koordinaten", "eingeben"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)

    def show_uhren_error(self):
        lines = ["Fehler 3", "Hardware Uhr"]
        coords = [(5,5), (5,25)]
        self.show_lines(lines, coords=coords)
