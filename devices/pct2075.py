import adafruit_pct2075

class PCT2075Sensor:
    def __init__(self, i2c_bus):
        self.sensor = adafruit_pct2075.PCT2075(i2c_bus)

    def read_temperature(self):
        try:
            return self.sensor.temperature
        except Exception as e:
            return None