# LepMon Project

LepMon is a modular Raspberry Pi-based monitoring system for nighttime insect monitoring. This system integrates various sensors, cameras, and UI components to provide a comprehensive environmental monitoring solution.

## Features

- **Sensors**: Reads data from BH1750, PCT2075, INA226, BME280, and more.
- **Camera Integration**: Supports Alvium and Arducam cameras.
- **UI Components**: Includes OLED display and button-based menu navigation.
- **LED Control**: Dimmable LED functionality for optimized illumination.
- **Data Logging**: Logs sensor readings and captures images during specified time windows.

## Prerequisites

1. Raspberry Pi with Raspbian OS installed.
2. Python 3.7 or later.
3. Required hardware components:
   - BH1750 light sensor
   - PCT2075 temperature sensor
   - INA226 power monitor
   - BME280 environmental sensor
   - SH1106 OLED display
   - Alvium or Arducam camera
   - LEDs and dimming hardware

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/lepmon.git
cd lepmon
```

### 2. Install Python Dependencies

Run the following command to install all required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Required Modules

Alternatively, install dependencies individually using the following commands:

```bash
# General Python packages
pip install RPi.GPIO adafruit-circuitpython-bh1750 adafruit-circuitpython-pct2075 smbus2 \
            bme280 pytz timezonefinder-python ephem opencv-python-headless \
            vimba-sdk Pillow luma.oled ina226

# Optional packages for advanced functionality
pip install numpy
```

### 4. Configure the System

#### Enable I2C

Ensure I2C is enabled on your Raspberry Pi:

1. Open Raspberry Pi Configuration:
   ```bash
   sudo raspi-config
   ```
2. Navigate to **Interfacing Options** > **I2C** > **Enable**.
3. Reboot your Raspberry Pi:
   ```bash
   sudo reboot
   ```

#### Camera Setup

Follow your specific camera setup instructions for either Alvium or Arducam.

### 5. Running the Application

Run the main script:

```bash
python3 lepmon/main.py
```

## Directory Structure

```
lepmon
├── devices
│   ├── bh1750.py
│   ├── pct2075.py
│   ├── ina226.py
│   ├── bme280_sensor.py
│   ├── camera.py
│   ├── led.py
│   └── ...
├── ui
│   ├── oled_display.py
│   ├── menu_manager.py
│   ├── button_input.py
│   └── ...
├── utils
│   ├── file_ops.py
│   ├── logger.py
│   ├── time_ops.py
│   ├── error_handling.py
│   └── ...
├── config
│   ├── constants.py
│   └── ...
├── main.py
└── requirements.txt
```

## INstallation 

```bash
sudo apt install -y python3-picamera2
sudo apt-get install i2c-tools -y
sudo raspi-config nonint do_i2c 0
i2cdetect -y 1


cd ~/Downloads
git clone https://github.com/beniroquai/SEPMON
conda create -n lepmon  python=3.9 -y
conda activate lepmon
pip install -r requirements.txt
```

## Start 

```bash
sudo apt-get update && sudo apt-get install libcap-dev
git clone https://github.com/openuc2/ImSwitchDockerInstall
cd ImSwitchDockerInstall
 ./install_vimba.sh 
pip install -r requirements.txt 
sudo apt-get install python3-opencv
pip install https://github.com/BLavery/lib_oled96/archive/refs/heads/master.zip

cd ~/ImSwitchConfig 
checkout lepmon

sudo reboot
sudo raspi-config nonint do_i2c 0
python Downloads/LEPMON/OLD/Lepmon_skript/Lepmon.py 
```

## Notes

- Make sure to provide appropriate permissions to access GPIO and I2C devices. Use `sudo` if necessary.
- If additional hardware is added, extend the `devices` module accordingly.
- For camera settings, ensure the correct configuration file is available in the project directory.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the project.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
