import logging
try:
    from ina226 import INA226
except ImportError:
    from lepmon.devices.MockINA226 import MockINA226 as INA226

class INA226Sensor:
    def __init__(self, busnum=1, max_expected_amps=10):
        self.busnum = busnum
        self.sensor = None
        self.max_expected_amps = max_expected_amps

    def initialize(self):
        try:
            self.sensor = INA226(
                busnum=self.busnum, 
                max_expected_amps=self.max_expected_amps,
                log_level=logging.INFO
            )
            self.sensor.configure()
            self.sensor.set_low_battery(5)
        except Exception as e:
            print(e)
            # handle or log error

    def read_power_values(self):
        if not self.sensor:
            return None, None, None, None
        try:
            bus_voltage = self.sensor.voltage()
            shunt_voltage = self.sensor.shunt_voltage()
            current = self.sensor.current()
            power = self.sensor.power()
            return bus_voltage, shunt_voltage, current, power
        except Exception as e:
            return None, None, None, None
