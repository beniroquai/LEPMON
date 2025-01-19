import os
import sys
import time
import json
try:
    import RPi.GPIO as GPIO
except ImportError:
    import VPi.GPIO as GPIO
from datetime import datetime
import pytz
import board
try:
    import busio
except ImportError:
    import VPi.busio as busio
    import VPi.board as board
    

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

# You might keep constants, pin assignments, file paths in a config/constants.py
# e.g. from lepmon.config.constants import *


def main():
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
    i2c_bus = busio.I2C(board.SCL, board.SDA)

    # Sensors
    bh_sensor = BH1750Sensor(i2c_bus)
    pct_sensor = PCT2075Sensor(i2c_bus)
    ina_sensor = INA226Sensor(busnum=1)
    ina_sensor.initialize()

    bme_sensor = BME280Sensor()
    bme_sensor.initialize()

    # Camera
    # E.g. user chooses Alvium vs Arducam from config
    # camera = AlviumCamera("/home/Ento/Lepmon_Einstellungen/Kamera_Einstellungen.xml")
    # camera = ArducamCamera()

    # LED
    dimmer_pin = 13
    led_dimmer = LEDDimmer(dimmer_pin)

    ############################
    # 3) Initialize UI
    ############################
    oled = OLEDDisplay(i2c_port=1, address=0x3C)
    button_ok = ButtonInput(pin=7)
    menu_manager = MenuManager(oled, {"ok": button_ok})

    ############################
    # 4) Main loop
    ############################
    try:
        while True:
            # Example reading from sensors
            lux = bh_sensor.read_lux()
            in_temp = pct_sensor.read_temperature()
            bus_voltage, shunt_voltage, current, power = ina_sensor.read_power_values()
            out_temp, pressure, humidity = bme_sensor.read_environmental_data()

            # Possibly show some data on OLED
            oled.show_message([
                f"LUX: {lux:.1f}" if lux else "LUX: --",
                f"Cabin Temp: {in_temp:.1f}C" if in_temp else "Cabin Temp: --"
            ])

            # ... run your nighttime logic, check if time is in the “capture window”
            # ... call camera.capture_image(...) etc.

            time.sleep(60)  # Wait 1 minute

    except KeyboardInterrupt:
        pass
    except Exception as e:
        write_log(f"Unexpected error: {e}", level="error")
    finally:
        GPIO.cleanup()
        write_log("LepMon application shutting down.")

if __name__ == "__main__":
    main()