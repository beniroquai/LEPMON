import logging

class SMBus:
    """
    Mock class for smbus2.SMBus to simulate I2C communication without hardware.
    """

    def __init__(self, bus):
        """
        Initialize the mock SMBus.

        :param bus: Bus number (mocked, no actual hardware access).
        """
        self.bus = bus
        self.registers = {}  # Simulate I2C device registers
        logging.info(f"Initialized MockSMBus on bus {bus}")

    def write_byte(self, addr, val):
        """
        Mock method for writing a byte to a device.

        :param addr: I2C address of the device.
        :param val: Byte value to write.
        """
        self.registers[addr] = val
        logging.info(f"Write byte: {val} to address: {addr}")

    def write_byte_data(self, addr, reg, val):
        """
        Mock method for writing a byte to a specific register.

        :param addr: I2C address of the device.
        :param reg: Register address.
        :param val: Byte value to write.
        """
        if addr not in self.registers:
            self.registers[addr] = {}
        self.registers[addr][reg] = val
        logging.info(f"Write byte: {val} to register: {reg} at address: {addr}")

    def write_i2c_block_data(self, addr, reg, data):
        """
        Mock method for writing a block of data to a specific register.

        :param addr: I2C address of the device.
        :param reg: Register address.
        :param data: List of byte values to write.
        """
        if addr not in self.registers:
            self.registers[addr] = {}
        self.registers[addr][reg] = data
        logging.info(f"Write block: {data} to register: {reg} at address: {addr}")

    def read_byte(self, addr):
        """
        Mock method for reading a byte from a device.

        :param addr: I2C address of the device.
        :return: Byte value from the device.
        """
        val = self.registers.get(addr, {}).get(0, 0)
        logging.info(f"Read byte: {val} from address: {addr}")
        return val

    def read_byte_data(self, addr, reg):
        """
        Mock method for reading a byte from a specific register.

        :param addr: I2C address of the device.
        :param reg: Register address.
        :return: Byte value from the register.
        """
        val = self.registers.get(addr, {}).get(reg, 0)
        logging.info(f"Read byte: {val} from register: {reg} at address: {addr}")
        return val

    def read_i2c_block_data(self, addr, reg, length):
        """
        Mock method for reading a block of data from a specific register.

        :param addr: I2C address of the device.
        :param reg: Register address.
        :param length: Number of bytes to read.
        :return: List of byte values from the register.
        """
        block = self.registers.get(addr, {}).get(reg, [0] * length)
        logging.info(f"Read block: {block} from register: {reg} at address: {addr}")
        return block

    def close(self):
        """
        Mock method for closing the bus.
        """
        logging.info(f"Closed MockSMBus on bus {self.bus}")


# Usage example
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    bus = MockSMBus(1)
    bus.write_byte(0x40, 0xFF)
    bus.write_byte_data(0x40, 0x01, 0xAA)
    bus.write_i2c_block_data(0x40, 0x02, [0x01, 0x02, 0x03])
    bus.read_byte(0x40)
    bus.read_byte_data(0x40, 0x01)
    bus.read_i2c_block_data(0x40, 0x02, 3)
    bus.close()
