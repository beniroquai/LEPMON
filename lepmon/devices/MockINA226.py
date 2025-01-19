class MockINA226:
    """Mock class for the INA226 sensor, simulating interactions without hardware dependencies."""
    def __init__(self, i2c_bus, address=0x40):
        self.i2c_bus = i2c_bus
        self.address = address
        self.calibration = 0
        self.current_lsb = 0
        self.power_lsb = 0
        print(f"MockINA226 initialized on bus {self.i2c_bus} with address {hex(self.address)}")

    def configure(self, averaging_count, bus_conversion_time, shunt_conversion_time, mode):
        print(
            f"Configured with averaging_count={averaging_count}, bus_conversion_time={bus_conversion_time}, "
            f"shunt_conversion_time={shunt_conversion_time}, mode={mode}"
        )

    def calibrate(self, shunt_resistance, max_expected_current):
        print(
            f"Calibrated with shunt_resistance={shunt_resistance}, max_expected_current={max_expected_current}"
        )
        self.calibration = 1
        self.current_lsb = max_expected_current / 32768.0
        self.power_lsb = self.current_lsb * 25

    def read_voltage(self):
        print("Simulating voltage read")
        return 3.3

    def read_current(self):
        print("Simulating current read")
        return 0.01

    def read_power(self):
        print("Simulating power read")
        return 0.033


class INA226Sensor:
    """Wrapper class for the INA226 sensor, integrating with the mock implementation."""
    def __init__(self, i2c_bus, address=0x40):
        self.sensor = MockINA226(i2c_bus, address)

    def configure_sensor(self, averaging_count, bus_conversion_time, shunt_conversion_time, mode):
        self.sensor.configure(averaging_count, bus_conversion_time, shunt_conversion_time, mode)

    def calibrate_sensor(self, shunt_resistance, max_expected_current):
        self.sensor.calibrate(shunt_resistance, max_expected_current)

    def get_voltage(self):
        return self.sensor.read_voltage()

    def get_current(self):
        return self.sensor.read_current()

    def get_power(self):
        return self.sensor.read_power()


# Example usage
if __name__ == "__main__":
    i2c_bus = "MockI2C"
    sensor = INA226Sensor(i2c_bus)
    sensor.configure_sensor(4, 140, 140, "continuous")
    sensor.calibrate_sensor(0.1, 3.2)
    voltage = sensor.get_voltage()
    current = sensor.get_current()
    power = sensor.get_power()

    print(f"Voltage: {voltage} V")
    print(f"Current: {current} A")
    print(f"Power: {power} W")
