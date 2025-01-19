import logging

class I2C:
    """
    Mock class for busio.I2C to simulate I2C communication.
    """

    def __init__(self, scl, sda, frequency=100000):
        """Initialize the mock I2C interface."""
        self.scl = scl
        self.sda = sda
        self.frequency = frequency
        self.devices = {}
        logging.info(f"Mock I2C initialized with SCL={scl}, SDA={sda}, frequency={frequency} Hz")

    def scan(self):
        """Simulate scanning for I2C devices."""
        logging.info(f"Scanning for I2C devices: Found {list(self.devices.keys())}")
        return list(self.devices.keys())

    def writeto(self, address, buffer, stop=True):
        """Simulate writing to an I2C device."""
        if address in self.devices:
            logging.info(f"Writing to I2C address {address}: {buffer}")
            self.devices[address]['data'] = buffer
        else:
            logging.error(f"I2C write failed: No device at address {address}")

    def readfrom_into(self, address, buffer, stop=True):
        """Simulate reading from an I2C device."""
        if address in self.devices:
            data = self.devices[address].get('data', b'\x00' * len(buffer))
            buffer[:] = data[:len(buffer)]
            logging.info(f"Reading from I2C address {address}: {data}")
        else:
            logging.error(f"I2C read failed: No device at address {address}")

    def add_device(self, address, data=b""):
        """Add a mock device to the I2C bus."""
        self.devices[address] = {'data': data}
        logging.info(f"Added mock I2C device at address {address} with initial data: {data}")


class MockSPI:
    """
    Mock class for busio.SPI to simulate SPI communication.
    """

    def __init__(self, clock, MOSI=None, MISO=None):
        """Initialize the mock SPI interface."""
        self.clock = clock
        self.MOSI = MOSI
        self.MISO = MISO
        self.connected_device = None
        logging.info(f"Mock SPI initialized with clock={clock}, MOSI={MOSI}, MISO={MISO}")

    def configure(self, baudrate=1000000, polarity=0, phase=0):
        """Simulate configuring the SPI bus."""
        self.baudrate = baudrate
        self.polarity = polarity
        self.phase = phase
        logging.info(f"SPI configured with baudrate={baudrate}, polarity={polarity}, phase={phase}")

    def write(self, buffer):
        """Simulate writing to an SPI device."""
        if self.connected_device:
            logging.info(f"SPI write to device: {buffer}")
        else:
            logging.error("SPI write failed: No device connected")

    def readinto(self, buffer):
        """Simulate reading from an SPI device."""
        if self.connected_device:
            data = b'\xAA' * len(buffer)  # Simulated response
            buffer[:] = data
            logging.info(f"SPI read from device: {data}")
        else:
            logging.error("SPI read failed: No device connected")

    def connect_device(self, device_name):
        """Connect a mock device to the SPI bus."""
        self.connected_device = device_name
        logging.info(f"Connected mock SPI device: {device_name}")

    def disconnect_device(self):
        """Disconnect the current device from the SPI bus."""
        logging.info(f"Disconnected mock SPI device: {self.connected_device}")
        self.connected_device = None


# Usage example
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Mock I2C example
    i2c = MockI2C(scl="SCL", sda="SDA")
    i2c.add_device(0x40, data=b"\x12\x34")
    i2c.scan()
    buffer = bytearray(4)
    i2c.readfrom_into(0x40, buffer)
    i2c.writeto(0x40, b"\x56\x78")

    # Mock SPI example
    spi = MockSPI(clock="CLK", MOSI="MOSI", MISO="MISO")
    spi.configure(baudrate=500000, polarity=1, phase=1)
    spi.connect_device("MockSensor")
    buffer = bytearray(4)
    spi.readinto(buffer)
    spi.write(b"\x01\x02\x03")
    spi.disconnect_device()
