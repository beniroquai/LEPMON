import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def load_calibration_params(bus, address):
    print(f"Loading calibration parameters from BME280 at address: {hex(address)}")

def sample(bus, address, calibration_params):
    print(f"Sampling BME280 at address: {hex(address)}")
    return np.random.rand(3)