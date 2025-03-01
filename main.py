import os
import sys
import time
import json
import cv2
from gpiozero import LED
import ephem
from datetime import datetime, timedelta    

try:
    import RPi.GPIO as GPIO
except ImportError:
    import VPi.GPIO as GPIO
    from gpiozero.pins.mock import MockFactory
    import gpiozero
    gpiozero.Device.pin_factory = MockFactory()


from datetime import datetime, timedelta
import pytz
import board
try:
    import busio
except ImportError:
    import VPi.busio as busio
    import VPi.board as board
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta
import ephem

# Device classes
from lepmon.devices.bh1750 import BH1750Sensor
from lepmon.devices.pct2075 import PCT2075Sensor
from lepmon.devices.ina226 import INA226Sensor
from lepmon.devices.bme280_sensor import BME280Sensor
from lepmon.devices.led import LEDDimmer
#from lepmon.devices.camera import AlviumCamera, ArducamCamera

# UI classes
from lepmon.ui.oled_display import OLEDDisplay
from lepmon.ui.button_input import ButtonInput
from lepmon.ui.menu_manager import MenuManager

# Utils
from lepmon.utils.logger import init_logger, write_log
from lepmon.utils.file_ops import create_csv_file, append_csv_row, copy_file_with_checksum
from lepmon.utils.time_ops import get_twilight_times
from lepmon.utils.error_handling import error_indicator

import lepmon.utils.file_ops as file_ops
# You might keep constants, pin assignments, file paths in a config/constants.py
# e.g. from lepmon.config.constants import *

class SepMonController:
    

    def __init__(self):
        """
        Main LepMon script that orchestrates initialization and the main loop.
        """

        ############################
        # 1) Initialize GPIO, i2c, logging, etc.
        ############################
        GPIO.setmode(GPIO.BCM)
        error_pin = 17
        GPIO.setup(error_pin, GPIO.OUT)

        log_file = "logfile.log"
        log_path = os.path.join(os.path.dirname(__file__), log_file)
        init_logger(log_path)
        write_log("Starting LepMon application...")

        ############################
        # 2) Initialize devices
        ############################
        # i2c bus
        self.i2c_bus = busio.I2C(board.SCL, board.SDA)

        # Sensors
        self.bh_sensor = BH1750Sensor(self.i2c_bus)
        self.pct_sensor = PCT2075Sensor(self.i2c_bus)
        self.ina_sensor = INA226Sensor(busnum=1)
        self.ina_sensor.initialize()

        self.bme_sensor = BME280Sensor()
        self.bme_sensor.initialize()

        # Camera
        # E.g. user chooses Alvium vs Arducam from config
        # camera = AlviumCamera("/home/Ento/Lepmon_Einstellungen/Kamera_Einstellungen.xml")
        # camera = ArducamCamera()
        self.camera_power_pin = LED(5)
        self.blue_led_pin = LED(6)
        self.blue_led_pin.off()
        
        # TODO: what is this for?
        self.GUI_pin = LED(22)    
        for _ in range(3):
            self.GUI_pin.on()
            time.sleep(.5)
            self.GUI_pin.off()
            time.sleep(.5)  
        
        # LED
        dimmer_pin = 13
        self.led_dimmer = LEDDimmer(dimmer_pin)

        ############################
        # 3) Initialize UI
        ############################
        self.oled = OLEDDisplay(i2c_port=1, address=0x3C)
        self.button_ok = ButtonInput(pin=7)
        self.button_right = ButtonInput(pin=8)
        self.menu_manager = MenuManager(self.oled, {"ok": self.button_ok})



    def focussing(
        self,
        exposure_start=150,
        laplacian_iterations=25
    ):
        """
        Manually focus the camera by maximizing the Laplacian-based sharpness value.
        Press `button_ok` to exit the focusing loop.
        Increase/Decrease exposure time with `button_up` / `self.button_down`.
        """

        # Turn camera power on
        self.camera_power_pin.on()

        # Initial display on the OLED
        self.oled.show_lines(
            ["fokussieren", "bis Anzeigewert", "Maximum erreicht"],
            coords=[(5, 5), (5, 25), (5, 45)]
        )

        # Small pause before starting
        time.sleep(9)

        fokus_errors = 0
        max_sharpness = 0
        current_exposure_ms = exposure_start

        # If you need a dimmer or LED for focusing, start it here as needed
        if self.led_dimmer:
            self.led_dimmer.start(100)  # e.g. set to 100% initially

        while self.button_ok.is_released():  # loop until user presses the 'ok' button
            self.blue_led_pin.on()  # visual indicator
            frame = None

            try:
                # Example camera usage:
                # Set exposure:
                # camera_object.set_exposure(current_exposure_ms)
                # Acquire frame:
                self.detector.set_exposure_time(current_exposure_ms)
                frame = self.detector.get_latest()  # should return a valid OpenCV image
                fokus_errors = 0
            except Exception:
                fokus_errors += 1

            if fokus_errors == 2:
                # If camera fails twice, show error and exit focusing
                error_indicator(1, 1, self.uart, error_pin=17)
                self.oled.show_lines(
                    ["Fehler Kamera", "überlastet", "Falle neu starten"],
                    coords=[(5, 5), (5, 25), (5, 45)]
                )
                time.sleep(5)
                return

            self.blue_led_pin.off()

            # If we have a valid frame, analyze it
            if frame is not None:
                # Convert to gray and compute Laplacian variance
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sharpness = round(cv2.Laplacian(gray, cv2.CV_64F).var(), 0)
                if sharpness > max_sharpness:
                    max_sharpness = sharpness
            else:
                sharpness = 0

            # Inner loop to check repeated button presses for adjusting exposure
            for _ in range(laplacian_iterations):
                if not self.button_ok.is_released():
                    break  # user pressed OK, exit focusing
                if not self.button_up.is_released(): # FIXME: button_up is not defined
                    # Increase exposure
                    current_exposure_ms = (
                        current_exposure_ms + 10
                        if current_exposure_ms > 20
                        else current_exposure_ms + 1
                    )
                if not self.button_down.is_released():
                    # Decrease exposure
                    current_exposure_ms = (
                        current_exposure_ms - 10
                        if current_exposure_ms > 20
                        else max(current_exposure_ms - 1, 1)
                    )

                # Show the user the current sharpness & exposure
                self.oled.show_lines([
                        f"Schärfewert: {sharpness}",
                        f"peak: {max_sharpness}",
                        f"Exposure: {current_exposure_ms} ms"
                    ],
                    coords=[(5, 5), (5, 25), (5, 45)]
                )
                time.sleep(0.1)
            # Enter drücken, um fokusieren zu verlassen
            if not self.button_ok.is_released():
                break

            # End of focusing
            time.sleep(0.25)
            
            self.GUI_pin.off()

        # End of focusing
        # Turn LED/pwm back to 0 if needed
        if self.led_dimmer:
            self.led_dimmer.stop()
        self.camera_power_pin.off()

        
    def set_system_time_interactive(self):
        current_datetime = datetime.now()
        date_time_str = current_datetime.strftime("%Y%m%d%H%M%S")
        date_time_list = [int(digit) for digit in date_time_str]

        current_position = 0
        selection_mode = 1
        try:
            while True:
                self.GUI_pin.on()
                if selection_mode < 3:
                    if selection_mode == 1:
                        # Date selection
                        if current_position < 4:
                            pointer = "_" * current_position
                        elif 4 <= current_position < 6:
                            pointer = "_" * 4 + "-" + "_" * (current_position - 4)
                        else:
                            pointer = "_" * 4 + "-" + "_" * 2 + "-" + "_" * (current_position - 6)
                        pointer += "x"

                        self.oled.show_lines(
                            [
                                "Datum einstellen",
                                f"{date_time_list[0]}{date_time_list[1]}{date_time_list[2]}{date_time_list[3]}-"
                                f"{date_time_list[4]}{date_time_list[5]}-"
                                f"{date_time_list[6]}{date_time_list[7]}",
                                pointer
                            ],
                            coords=[(5, 5), (5, 25), (5, 40)]
                        )
                    else:
                        # selection_mode == 2 -> time selection
                        if 8 <= current_position < 10:
                            pointer = "_" * (current_position - 8)
                        elif 10 <= current_position < 12:
                            pointer = "__:" + "_" * (current_position - 10)
                        else:
                            pointer = "__:__:" + "_" * (current_position - 12)
                        pointer += "x"

                        self.oled.show_lines(
                            [
                                "Zeit einstellen",
                                f"{date_time_list[8]}{date_time_list[9]}:"
                                f"{date_time_list[10]}{date_time_list[11]}:"
                                f"{date_time_list[12]}{date_time_list[13]}",
                                pointer
                            ],
                            coords=[(5, 5), (5, 25), (5, 40)]
                        )

                    if self.button_up.is_released:
                        date_time_list[current_position] = (date_time_list[current_position] + 1) % 10
                    elif self.button_down.is_released:
                        date_time_list[current_position] = (date_time_list[current_position] - 1) % 10
                    elif self.button_right.is_released:
                        if selection_mode == 1:
                            current_position = (current_position + 1) % 8
                        else:  # selection_mode == 2
                            if current_position != 13:
                                current_position = (current_position + 1) % 14
                            else:
                                current_position = 8
                    elif self.button_ok.is_released:
                        selection_mode += 1
                        current_position = 8
                        self.oled.show_lines([" "])  # Clear screen
                else:
                    self.GUI_pin.off()
                    break

                time.sleep(0.1)

            system_time_str = (
                f"{date_time_list[0]}{date_time_list[1]}{date_time_list[2]}{date_time_list[3]}-"
                f"{date_time_list[4]}{date_time_list[5]}-"
                f"{date_time_list[6]}{date_time_list[7]} "
                f"{date_time_list[8]}{date_time_list[9]}:"
                f"{date_time_list[10]}{date_time_list[11]}:"
                f"{date_time_list[12]}{date_time_list[13]}"
            )
            os.system("sudo timedatectl set-ntp false")
            os.system(f"sudo timedatectl set-time '{system_time_str}'")

            self.oled.show_lines(["Zeit aktualisiert"])
            start_time = time.time()

            while time.time() - start_time < 5:
                current_time = datetime.now().strftime("%H:%M:%S")
                self.oled.show_lines(["aktuelle Uhrzeit", current_time], coords=[(5, 5), (5, 25)])
                time.sleep(1)

            self.log_schreiben(f"{current_time}; Eingabe Menü vom Benutzer geöffnet")
            self.log_schreiben(f"{current_time}; Uhrzeit vom Nutzer neu gestellt")

        except:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.log_schreiben(f"{current_time}; Eingabe Menü vom Benutzer geöffnet")
            self.log_schreiben(f"{current_time}; Fehler 3: Uhrzeit konnte nicht neu gestellt werden")
            self.oled.show_lines(["Fehler 3", "Hardware Uhr"], coords=[(5, 5), (5, 25)])
            self.Fehlerindikator(3)
        
    
    def handle_coordinate_entry(self):
        coordinates_new = False
        # Loop to check if user wants to enter new coordinates
        for _ in range(40):
            # Equivalent to: if GPIO.input(PIN_EINGABE) is not GPIO.HIGH
            if not self.button_ok.is_pressed:
                self.GUI_pin.off()
                # Prompt user to enter coordinates
                self.oled.show_lines(["Coordinates", "Enter new"], coords=[(5, 5), (5, 25)])
                time.sleep(1)
                coordinates_new = True

                # Prompt user to select hemisphere (north/south)
                self.oled.show_lines(["Please select", "hemisphere"], coords=[(5, 5), (5, 25)])
                time.sleep(3)
                self.oled.show_lines(["Press UP = North", "Press DOWN = South"], coords=[(5, 5), (5, 25)])

                user_selected = False
                pol = ""
                north_south = ""
                while not user_selected:
                    self.GUI_pin.on()
                    if self.button_up.is_released:
                        pol = ""
                        north_south = "Nord"
                        user_selected = True
                        self.GUI_pin.off()
                    elif self.button_down.is_released:
                        pol = "-"
                        north_south = "Sued"
                        user_selected = True
                        self.GUI_pin.off()
                    else:
                        time.sleep(0.1)

                # Prompt user to select east/west
                self.oled.show_lines(["Press UP = East", "Press DOWN = West"], coords=[(5, 5), (5, 25)])
                user_selected = False
                block = ""
                east_west = ""
                while not user_selected:
                    self.GUI_pin.on()
                    if self.button_up.is_released:
                        block = ""
                        east_west = "Ost"
                        user_selected = True
                        self.GUI_pin.off()
                    elif self.button_down.is_released:
                        block = "-"
                        east_west = "West"
                        user_selected = True
                        self.GUI_pin.off()
                    else:
                        time.sleep(0.1)

                # Save hemisphere to file
                hemisphere_path = "/home/Ento/Lepmon_Einstellungen/Hemisphere.json"
                hemisphere_data = {
                    "Pol": north_south,
                    "Block": east_west
                }
                with open(hemisphere_path, "w") as json_file:
                    json.dump(hemisphere_data, json_file, indent=4)

                # Placeholder for GPS coordinate input function
                # e.g. self.enter_gps_coordinates():
                # Here, just pretend we got lat/long from the user
                latitude = "52.5200"
                longitude = "13.4050"

                # Clear screen
                self.oled.show_lines([" "])

                # Save new coordinates
                coordinates_path = "/home/Ento/Lepmon_Einstellungen/Koordinaten.json"
                coordinate_data = {
                    "latitude": latitude,
                    "longitude": longitude
                }
                with open(coordinates_path, "w") as json_file:
                    json.dump(coordinate_data, json_file, indent=4)

                # Show confirmation
                self.oled.show_lines(["GPS Coordinates", "saved"], coords=[(5, 5), (5, 25)])
                time.sleep(2)

            time.sleep(0.1)

        # If user did not change coordinates, update time and log
        self.GUI_pin.off()
        if not coordinates_new:
            self.update_time()
            local_time = time.strftime("%H:%M:%S")
            self.log_write(f"{local_time}; Geographic latitude unchanged")
            self.log_write(f"{local_time}; Geographic longitude unchanged")    

    def update_time(self): 
        self.UTC_now = datetime.now(pytz.utc)
        self.time_now = datetime.now()
        self.local_time = self.time_now.strftime("%Y-%m-%d %H:%M:%S")
        
        
    def berechne_zeitzone(self, lat,lng):
        lat = float(lat)
        lng = float(lng)
        tf = TimezoneFinder()
        
        # Finde die Zeitzone basierend auf den Koordinaten
        zeitzone_name = tf.timezone_at(lat=lat, lng=lng)
        
        if zeitzone_name is None:
            print("Keine Zeitzone gefunden für diese Koordinaten.")
            return None
        
        # Hole das aktuelle Datum und die Uhrzeit in der gefundenen Zeitzone
        Zeitzone = pytz.timezone(zeitzone_name)
        #lokale_zeit = datetime.now(Zeitzone)
        #print(Zeitzone)
        return Zeitzone


    def get_twilight_times_func(self, lat, lng, date, Dämmerungspuffer):
        Zeitzone = self.berechne_zeitzone(lat, lng)
        observer = ephem.Observer()
        observer.lat = str(lat)
        observer.lon = str(lng)
        date_utc = date.astimezone(pytz.utc)

        sunset = ephem.localtime(observer.next_setting(ephem.Sun(), start=date_utc))
        self.Abenddämmerung = ephem.localtime(observer.next_setting(ephem.Sun(), use_center=True, start=date_utc))

        Abenddämmerung_local = self.Abenddämmerung.astimezone(self.Zeitzone)
        self.nacht_beginn_zeit = (Abenddämmerung_local - Dämmerungspuffer).replace(tzinfo=None)

        Abenddämmerung_formatted = Abenddämmerung_local.strftime("%Y-%m-%d  %H:%M:%S")
        Abenddämmerung_short = Abenddämmerung_local.strftime("%H:%M:%S")

        next_day = date + timedelta(days=1)
        next_day_utc = next_day.astimezone(ephem.UTC)

        sunrise = ephem.localtime(observer.previous_rising(ephem.Sun(), start=next_day_utc))
        Morgendämmerung = ephem.localtime(observer.previous_rising(ephem.Sun(), use_center=True, start=next_day_utc))

        Morgendämmerung_local = self.Morgendämmerung.astimezone(self.Zeitzone)
        nacht_ende_zeit = (Morgendämmerung_local + Dämmerungspuffer).replace(tzinfo=None)

        Morgendämmerung_formatted = Morgendämmerung_local.strftime("%Y-%m-%d  %H:%M:%S")
        Morgendämmerung_short = Morgendämmerung_local.strftime("%H:%M:%S")

        # return         write_log_func(f"begins: {times_res.abenddämmerung}, ends: {times_res.morgendämmerung}, ...")
        return Abenddämmerung_local, Morgendämmerung_local
    
    def get_usb_path(self):
            """
            Determines the path of the USB stick
            """
            username = os.getenv("USER")
            media_path = f"/media/{username}"
            if os.path.exists(media_path):
                for item in os.listdir(media_path):
                    potential_path = os.path.join(media_path, item)
                    if os.path.ismount(potential_path):
                        return potential_path
            return None       
             
    def read_lux(self):
        """
        Read the current Lux value from the BH1750 sensor
        """
        try:
            lux = self.bh_sensor.read_lux()
            return lux
        except Exception as e:
            print(f"Error reading Lux: {e}")
            return None
        
    def run_main_program(
        self
    ):
        '''
        ,
        uv_led_pwm,        # e.g. PWM for UV LED on pin 26
        sensor_data_class, # e.g. class that reads sensors: SensorData.read_sensor_data()
        read_coordinates_func,      # function to read lat, lng, hemisphere, etc.
        read_json_func,             # function to read JSON from a file
        write_log_func,             # function to write to log
        '''
        """
        Translated and modularized main LepMon logic.
        """
        # Example local references for clarity
        # (You would typically store these in your config/constants or pass them differently)
        # and define any needed global-like variables.
        # The user might already have these in separate config files:
        koordinaten_file_path = "./Lepmon_Einstellungen/Koordinaten.json"
        erw_einstellungen_pfad = "./Lepmon_Einstellungen/Fallenmodus.json"
        kamera_einstellungen_path = "./Lepmon_Einstellungen/Kamera_Einstellungen.xml"
        halbkugel_pfad = "./Lepmon_Einstellungen/Hemisphere.json"
        einstellungen_pfad = "./Lepmon_Einstellungen/LepmonCode.json"
        
        try: 
            usb_path = self.get_usb_path()
        except Exception as e:
            print(f"USB path error: {e}")
            # fallback local path #FIXME: This is unclear
            usb_path = "./"
        # enforce USB path for now 
        usb_path = "./"
        # Example pin initial states or constants
        # (Assuming these are already done outside or by the caller)
        # e.g. GPIO.setmode(GPIO.BCM) etc.

        # Load general project data
        with open(einstellungen_pfad) as f:
            data = json.load(f)
        project_name = data["projekt_name"]
        sensor_id = data["sensor_id"]
        bundesland = data["bundesland"]
        stadt_code = data["stadtcode"]

        # Load extended mode settings
        with open(erw_einstellungen_pfad) as f:
            mode_setup = json.load(f)
        blitz_change_time = float(mode_setup["Erweiterte_Einstellungen"]["Blitzaenderungszeit"])
        dawn_buffer_minutes = int(mode_setup["Erweiterte_Einstellungen"]["Daemmerungspuffer"])
        dawn_buffer_delta = timedelta(minutes=dawn_buffer_minutes)
        dawn_threshold_lux = int(mode_setup["Erweiterte_Einstellungen"]["Daemmerung"])  # threshold lux
        capture_interval = int(mode_setup["Erweiterte_Einstellungen"]["Intervall_zwischen_Photos"])  # minutes
        camera_type = str(mode_setup["Erweiterte_Einstellungen"]["Kameratyp"])
        
        Dämmerungspuffer = int(mode_setup["Erweiterte_Einstellungen"]["Daemmerungspuffer"])
        Dämmerungspuffer = timedelta(minutes=Dämmerungspuffer)
        # e.g. utc_timezone = pytz.utc

        continuity_mode = mode_setup["Fang_mit_Pause"]
        if continuity_mode:
            uv_on_duration = int(mode_setup["Anlockphase"])
            uv_off_duration = int(mode_setup["Pause"])
            uv_on_counter = 0
            uv_off_counter = 0
            # Simplified logic: multiples for sub-interval usage
            uv_on_sub = capture_interval / capture_interval * uv_on_duration
            uv_off_sub = capture_interval / capture_interval * uv_off_duration

        # Read initial coordinates & hemisphere # TODO: This is unclear
        lat, lng, hemisphere_data = file_ops.read_coordinates_func(
            koordinaten_file_path, halbkugel_pfad
        )

        # Show prompt to open menu
        time.sleep(1)
        self.GUI_pin.on()
        self.oled.show_lines(["Menü öffnen:", "Bitte rechte Taste", "drücken"])
        time.sleep(2)  # e.g. show for 2s

        # 20 Sekunden lang auf Tastendruck warten
        # Wait e.g. 2 loops * 0.1 = 0.2s or user can change
        # (In original code it was 20s. Adjust as needed.)
        # TODO: This is unclear to me!
        pressed_menu = False
        for _ in range(2):
            if not self.button_ok.is_released():
                pressed_menu = True
                break
            time.sleep(0.1)

        if pressed_menu:
            # Entering the user menu
            self.GUI_pin.off()
            self.oled.show_lines(["Eingabe Menü", "x"], coords=[(5, 5), (45, 5)])
            # Possibly focusing the camera
            # We'll do short loop to check if "button_right" was pressed
            # in original code, user had 100 loops ~ 5 seconds
            # for demonstration
            for _ in range(100):
                if not self.button_right.is_released():
                    # If user wants to focus camera
                    self.focussing()
                    self.camera_power_pin.off()
                    break
                time.sleep(0.05)

            # Re-init PWM start
            self.led_dimmer.start(0)

            # Check USB
            if file_ops.check_usb_connection(usb_path):
                self.oled.show_lines(["USB Stick", "richtig verbunden"])
            else:
                self.oled.show_lines(["Fehler 4", "USB nicht gefunden", "Falle neu starten"])
                self.error_indicator(4)
                time.sleep(4)
                sys.exit(4)

            # Show internal time and possibly let user adjust it
            for i in range(5):
                now_local = datetime.now()
                current_time_str = now_local.strftime("%H:%M:%S")
                self.oled.show_lines(["aktuelle Uhrzeit", current_time_str])
                time.sleep(1)

            # Let user choose to set time
            self.GUI_pin.on()
            self.oled.show_lines(["Uhrzeit mit ", "rechter Taste", "neu stellen"])
            time.sleep(2)
            user_set_time = False

            # Wait for some time to see if user wants to set time
            for _ in range(40):
                if not self.button_ok.is_released():
                    self.GUI_pin.off()
                    self.oled.show_lines(["Zeit und Datum", "eingeben"])
                    time.sleep(1)
                    user_set_time = True
                    self.update_time()  # user method to set date/time
                    break
                time.sleep(0.1)

            if not user_set_time:
                now_local = datetime.now()
                write_log_func(f"{now_local.strftime('%H:%M:%S')}; User menu opened but time was not changed")
            # TODO: Corresponds to line:             if GPIO.input(PIN_EINGABE) is not GPIO.HIGH:
            # Coordinates check
            # Show current lat/lng
            self.GUI_pin.off()
            
            # The rest of the logic to prompt user to re-enter coordinates, hemisphere, etc.
            # calls your read/write JSON functions, Hemisphere building, etc.
            # We'll just do a short placeholder:
            
            # Show current coordinates
            self.oled.show_lines(
                [
                    "Koordinaten",
                    f"Lat: {lat}",
                    f"Long: {lng}"
                ],
                coords=[(5, 5), (5, 25), (5, 45)]
            )
            time.sleep(5)
            coordinates_new = False
            self.GUI_pin.on()

            # Prompt user to set coordinates with right button
            self.oled.show_lines(
                [
                    "Koordinaten mit",
                    "rechter Taste",
                    "neu stellen"
                ],
                coords=[(5, 5), (5, 25), (5, 45)]
            )

            # Wait for user to press right button
            self.handle_coordinate_entry() # TODO: Check coordinate_new state internalyl 

            # Cycle UV LED for testing? FIME: What is this? - fade in and out?
            uv_led_pwm.start(0)
            for duty_cycle in range(0, 99):
                uv_led_pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(blitz_change_time / 100)
                uv_led_pwm.ChangeDutyCycle(100)
            
            # Test camera
            fileName = f"{project_name}{sensor_id}-{bundesland}-{stadt_code}__test.jpg"
            filePath = os.path.join(usb_path, fileName)
                        
            self.camera_power_pin.on()
            time.sleep(1)
            self.led_dimmer.dim_up(blitz_change_time)
            # FIXME: what is this: => power = messe_strom()
            '''
                frame = cam.get_frame(timeout_ms=864000000).as_opencv_image()
                 dim_down(Blitz_Änderung_zeit)
                 #VIS_LED.off()
                 cv2.imwrite(dateipfad, frame)
                 log_schreiben(f"{lokale_Zeit}; Bild gespeichert: {dateiname}")
                 image_message = f"Lepmon#{sensor_id} Bild gespeichert: {dateiname}"
                 try:
                    uart.write(image_message.encode('utf-8') + b'\n')
                 except Exception as e:
                      print(f"Fehler beim Lora senden: {e}")
                      pass   

            '''
            # use  dummy for now 
            import numpy as np
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(filePath, frame)
            self.led_dimmer.dim_down(blitz_change_time)
            # Show user the image
            self.oled.show_image(filePath)
            # write log message
            now_local = datetime.now()
            write_log_func(f"{now_local.strftime('%H:%M:%S')}; Image saved: {fileName}")
            image_message = f"Lepmon#{sensor_id} Bild gespeichert: {fileName}"
            try:
                uart.write(image_message.encode('utf-8') + b'\n')
            except Exception as e:
                print(f"Fehler beim Lora senden: {e}")
                pass
            
            
            ## END HERE 
            
            
            
            # (Pseudo code for camera capture test)
            # if camera_type == "Allied Vision Alvium":
            #     ...
            # elif camera_type == "Arducam Hawkeye":
            #     ...
            # else: ...
            # uv_led_pwm start(100 -> down)...
            
            # take an image using the ImSwitch API
            
            # e.g. final sensor test
            sensor_data = sensor_data_class.read_sensor_data()
            # Show user the sensor data
            # If there's an exception => error_indicator_func( some_error_code )
            # ...




            # Check USB space
            try:
                disk_data = file_ops.get_disk_space(usb_path)
                if disk_data:
                    total_gb, used_gb, free_gb, used_prc, free_prc = disk_data
                else:
                    log_schreiben(f"Fehler beim Abrufen des Speicherplatzes: {e}")
                    # show or log results
            except:
                error_indicator_func(4, sensor_id, self.uart, error_pin=17)

                # ...
                sys.exit(4)

            # final user message about test done
            time.sleep(5)

        else:
            # No user press
            self.GUI_pin.off()
            now_local = datetime.now()
            try:
                write_log_func(f"{now_local.strftime('%H:%M:%S')}; 20 seconds passed, no user input.")
            except:
                pass

        # Re-read coordinates if user changed them
        lat, lng, hemisphere_data = read_coordinates_func(koordinaten_file_path, halbkugel_pfad)

        # Prepare or reset data for nightly capture
        sensor_data_dict = {}

        # Start of the main night logic
        now_local = datetime.now()
        write_log_func(f"{now_local.strftime('%H:%M:%S')}; {now_local.strftime('%Y-%m-%d')}")
        write_log_func(f"{now_local.strftime('%H:%M:%S')}; latitude: {lat}")
        write_log_func(f"{now_local.strftime('%H:%M:%S')}; longitude: {lng}")

        # Example: call get_twilight_times
        Start_Datum = datetime.now()
        times_res = self.get_twilight_times_func(lat, lng, Start_Datum, Dämmerungspuffer)
        # Suppose times_res has Abenddämmerung_formatted, Morgendämmerung_formatted, night_begin, night_end etc.
        # you log them:
        write_log_func(f"begins: {times_res.abenddämmerung}, ends: {times_res.morgendämmerung}, ...")

        # Example of checking disk space
        disk_data = file_ops.get_disk_space(usb_path)
        if disk_data:
            total_gb, used_gb, free_gb, used_prc, free_prc = disk_data
            write_log_func(f"Total: {total_gb:.2f} GB, used: {used_prc:.2f}%, free: {free_prc:.2f}%")
        else:
            write_log_func("Unable to read USB disk space.")

        # Possibly copy camera settings to night folder or so
        # ...

        # read current LUX
        lux_value = self.read_lux()

        # Check day or night timing and proceed
        # e.g. if night hasn't started, sleep until then
        # if times_res.night_end <= now_local < times_res.night_begin:
        #     # Sleep logic ...
        # else:
        #     # proceed with capturing

        # Start the main loop
        capturing_started = False

        try:
            while True:
                now_local = datetime.now()
                lux_value = self.read_lux()

                # Example condition from your code:
                # if ( lux_value <= dawn_threshold_lux and not night_end <= ... ) or ...
                # or if capturing hasn't started, do something.

                # If continuity_mode => check uv_on_counter, uv_off_counter, etc.

                # capture_data_func(...)   # e.g. create CSV, store images, etc.
                # create_or_update_csv_func(...)
                # schedule next capture, etc.

                time.sleep(1)  # minimal

        except KeyboardInterrupt:
            now_str = datetime.now().strftime("%H:%M:%S")
            write_log_func(f"{now_str}; Program aborted by user.")
        finally:
            # Cleanup
            self.led_dimmer.stop()
            uv_led_pwm.stop()
            self.reboot()

    def reboot(self):
        """
        Reboots the Raspberry Pi.
        """
        # os.system("sudo reboot")


if __name__ == "__main__":
    mSepMon = SepMonController()
    mSepMon.run_main_program()
    
    #mSepMon.run_main_program()
    