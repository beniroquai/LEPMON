import logging
from time import sleep

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("MockBH1750")

class BH1750:
    """
    Mock class for the BH1750 Light Sensor.
    Simulates sensor behavior and logs operations.
    """

    def __init__(self, i2c=None, address=0x23):
        self.i2c_device = None  # No actual I2C device required
        self.address = address
        self._settings_byte = 0
        self._lux_value = 100.0  # Default mock lux value
        logger.info("Initialized MockBH1750 at address 0x%02X", address)

    def initialize(self):
        """Simulate initializing the sensor with default settings."""
        self.mode = "CONTINUOUS"
        self.resolution = "HIGH"
        logger.info("Sensor initialized with mode: %s, resolution: %s", self.mode, self.resolution)

    @property
    def lux(self):
        """Simulated light value in lux."""
        logger.debug("Reading lux value: %.2f", self._lux_value)
        return self._lux_value

    def set_lux(self, value):
        """Set a mock lux value for testing."""
        self._lux_value = value
        logger.info("Mock lux value set to: %.2f", self._lux_value)

    def _write(self, cmd_byte):
        """Simulate writing a command to the sensor."""
        self._settings_byte = cmd_byte
        logger.debug("Mock write: Command byte 0x%02X sent to address 0x%02X", cmd_byte, self.address)
        sleep(0.01)  # Simulate a short delay

# Example usage of the mock class
if __name__ == "__main__":
    # Create a mock sensor instance
    mock_sensor = MockBH1750()

    # Initialize the sensor
    mock_sensor.initialize()

    # Get the current lux value
    current_lux = mock_sensor.lux
    print(f"Current lux: {current_lux}")

    # Set a new lux value
    mock_sensor.set_lux(200.0)

    # Get the updated lux value
    updated_lux = mock_sensor.lux
    print(f"Updated lux: {updated_lux}")
