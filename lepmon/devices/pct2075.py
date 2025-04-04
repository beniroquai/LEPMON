
try:
    import adafruit_pct2075
except ImportError:
    import lepmon.devices.MockPCT2075 as adafruit_pct2075

class PCT2075Sensor:
    def __init__(self, i2c_bus):
        try:
            self.sensor = adafruit_pct2075.PCT2075(i2c_bus)
        except Exception as e:
            self.sensor = None
            print(f"Error initializing PCT2075 sensor: {e}")
            return

    def read_temperature(self):
        if self.sensor:
            try:
                return self.sensor.temperature
            except Exception as e:
                return None