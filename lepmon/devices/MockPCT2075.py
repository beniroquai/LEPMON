import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("MockPCT2075")

class PCT2075:
    """
    Mock driver for the PCT2075 Digital Temperature Sensor and Thermal Watchdog.
    Logs all interactions to simulate sensor behavior.
    """

    def __init__(self, i2c_bus=None, address=0x37):
        logger.debug(f"Initializing MockPCT2075 with address: {hex(address)}")
        self.address = address
        self._temperature = 25.0  # Default mock temperature in Celsius
        self.mode = 0  # Default mode
        self.shutdown = False
        self._fault_queue_length = 0
        self._high_temperature_threshold = 75.0  # Default high threshold
        self._temp_hysteresis = 70.0  # Default hysteresis
        self._idle_time = 100  # Default delay in ms

    @property
    def temperature(self):
        logger.debug(f"Reading temperature: {self._temperature}°C")
        return self._temperature

    @property
    def high_temperature_threshold(self):
        logger.debug(f"Getting high_temperature_threshold: {self._high_temperature_threshold}°C")
        return self._high_temperature_threshold

    @high_temperature_threshold.setter
    def high_temperature_threshold(self, value):
        logger.debug(f"Setting high_temperature_threshold to: {value}°C")
        self._high_temperature_threshold = value

    @property
    def temperature_hysteresis(self):
        logger.debug(f"Getting temperature_hysteresis: {self._temp_hysteresis}°C")
        return self._temp_hysteresis

    @temperature_hysteresis.setter
    def temperature_hysteresis(self, value):
        if value >= self._high_temperature_threshold:
            raise ValueError(
                "temperature_hysteresis must be less than high_temperature_threshold"
            )
        logger.debug(f"Setting temperature_hysteresis to: {value}°C")
        self._temp_hysteresis = value

    @property
    def faults_to_alert(self):
        logger.debug(f"Getting faults_to_alert: {self._fault_queue_length}")
        return self._fault_queue_length

    @faults_to_alert.setter
    def faults_to_alert(self, value):
        if value > 4 or value < 1:
            raise ValueError("faults_to_alert must be between 1 and 4")
        logger.debug(f"Setting faults_to_alert to: {value}")
        self._fault_queue_length = value

    @property
    def delay_between_measurements(self):
        delay = self._idle_time * 100
        logger.debug(f"Getting delay_between_measurements: {delay} ms")
        return delay

    @delay_between_measurements.setter
    def delay_between_measurements(self, value):
        if value > 3100 or value < 100 or value % 100 > 0:
            raise AttributeError(
                "delay_between_measurements must be >= 100, <= 3100, and a multiple of 100"
            )
        logger.debug(f"Setting delay_between_measurements to: {value} ms")
        self._idle_time = value // 100

# Example usage
if __name__ == "__main__":
    mock_sensor = MockPCT2075()
    print(mock_sensor.temperature)
    mock_sensor.high_temperature_threshold = 80.0
    print(mock_sensor.high_temperature_threshold)
    mock_sensor.temperature_hysteresis = 75.0
    print(mock_sensor.temperature_hysteresis)
    mock_sensor.faults_to_alert = 2
    print(mock_sensor.faults_to_alert)
    mock_sensor.delay_between_measurements = 200
    print(mock_sensor.delay_between_measurements)
