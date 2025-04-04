try:
    import bme280
    import smbus2
except ImportError:
    import lepmon.devices.MockBME280 as bme280
    import lepmon.devices.MockSMBus as smbus2

class BME280Sensor:
    def __init__(self, i2c_port=1, address=0x76):
        self.port = i2c_port
        self.address = address
        self.bus = smbus2.SMBus(self.port)
        self.calibration_params = None

    def initialize(self):
        try:
            self.calibration_params = bme280.load_calibration_params(self.bus, self.address)
            return True
        except Exception as e:
            self.calibration_params = None
            print(f"Error initializing BME280 sensor: {e}")
            return False

    def read_environmental_data(self):
        """
        Returns tuple: (temperature, pressure, humidity)
        """
        try:
            data = bme280.sample(self.bus, self.address, self.calibration_params)
            return data.temperature, data.pressure, data.humidity
        except Exception:
            return None, None, None
