import bme280
import smbus2

class BME280Sensor:
    def __init__(self, i2c_port=1, address=0x76):
        self.port = i2c_port
        self.address = address
        self.bus = smbus2.SMBus(self.port)
        self.calibration_params = None

    def initialize(self):
        self.calibration_params = bme280.load_calibration_params(self.bus, self.address)

    def read_environmental_data(self):
        """
        Returns tuple: (temperature, pressure, humidity)
        """
        try:
            data = bme280.sample(self.bus, self.address, self.calibration_params)
            return data.temperature, data.pressure, data.humidity
        except Exception:
            return None, None, None
