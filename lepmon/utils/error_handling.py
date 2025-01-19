
try: 
    import RPi.GPIO as GPIO
except ImportError:
    import VPi.GPIO as GPIO
    # from lepmon.devices.MockGPIO import MockGPIO as GPIO
import time
import json

def error_indicator(error_code, sensor_id, uart, error_pin=17):
    """
    Indicate errors via GPIO blinking, log them, send LoRa, etc.
    """
    try:
        error_message = f"Lepmon#{sensor_id} Fehler {error_code}"
        uart.write(error_message.encode('utf-8') + b'\n')
    except Exception as e:
        print(f"Lora Message nicht gesendet: {e}")

    for _ in range(1):
        for _ in range(error_code):
            GPIO.output(error_pin, GPIO.HIGH)
            time.sleep(0.25)
            GPIO.output(error_pin, GPIO.LOW)
            time.sleep(0.5)
        data = {"Fehler_code": error_code}
        with open("/home/Ento/Lepmon_skript/FehlerNummer.json", "w") as json_file:
            json.dump(data, json_file)
        time.sleep(3)
