try:
    import adafruit_bh1750
except ImportError:
    import lepmon.devices.MockBH1750 as adafruit_bh1750

class BH1750Sensor:
    def __init__(self, i2c_bus):
        self.sensor = adafruit_bh1750.BH1750(i2c_bus)

    def read_lux(self):
        try:
            return self.sensor.lux
        except Exception as e:
            # you can log or raise an exception
            return None