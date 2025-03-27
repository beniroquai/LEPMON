untitled:Untitled-3 {"typeId":""}
#! /usr/bin/python3
# -*- coding: utf-8 -*-

# Version 123
# 2025-01-14

#
print("Hauptskript")
#
#################################################################################################################

import sys
sys.path.append('/home/Ento/Lepmon_venv/lib/python3.11/site-packages')
import adafruit_bh1750
import adafruit_ds3231
import board
import busio
import bme280
import adafruit_pct2075 # lM75
import csv
import cv2
from datetime import datetime, timedelta
import ephem
from gpiozero import LED
import hashlib
from imutils import paths
from ina226 import INA226
import json
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from lib_oled96 import ssd1306
import logging
import os
#import picamera
#from picamera2 import Picamera2
from PIL import ImageFont, ImageDraw, Image
import pytz
import RPi.GPIO as GPIO
import serial
import shutil
import smbus2
import time
from timezonefinder import TimezoneFinder
from vimba import *
from time import mktime


IMSWITCH_URL = "localhost"
IMSWITCH_PORT = 8001



#######################
## Camera
######################
import imswitchclient.ImSwitchClient as imc
client = imc.ImSwitchClient(host="localhost", isHttps=True, port=443)


#################################################################################################################
######################################## I2C Variablen - NICHT ÄNDERN!!! ########################################
#################################################################################################################
GPIO.cleanup()

Display = i2c(port=1, address=0x3C)
oled = sh1106(Display)

# current folder path
current_folder = os.path.dirname(os.path.abspath(__file__))
# path to the font file
font_path = os.path.join(current_folder, 'FreeSans.ttf')
oled_font = ImageFont.truetype(font_path, 14)
oled_font_large = ImageFont.truetype(font_path, 17)

# get folder of Settings 
settings_folder = os.path.join(current_folder, 'Lepmon_Einstellungen')
with open(os.path.join(settings_folder,'LepmonCode.json')) as f:
    data = json.load(f)
sensor_id = data["sensor_id"]


try:
    uart = serial.Serial("/dev/serial0", 9600, timeout=1)
    print("Hauptprogramm: Lora Sender initialisiert")
except Exception as e:
    print(f"Hauptprogramm: Warnung: Lora Sender nicht initialisiert: {e}")
    pass
    
with canvas(oled) as draw:
    draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
    draw.text((5, 5), "Willkommen...", font = oled_font, fill = "white")
    draw.text((5, 30), "Laden... 3/3", font = oled_font, fill = "white")
    
GUI_pin = LED(22)    
for _ in range(3):
    GUI_pin.on()
    time.sleep(.5)
    GUI_pin.off()
    time.sleep(.5)    
        
blau = LED(6)
blau.off()

logo = Image.open(os.path.join(current_folder, 'logo_small.png'))

with canvas(oled) as draw:
    draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
    draw.text((5, 5), "Willkommen bei", font = oled_font, fill = "white")
    draw.text((5, 35), "LepMon", font = oled_font_large, fill = "white")
    draw.bitmap((70,30),logo, fill = 1)
class Sensor:
    def __init__(self, lux):
        self.lux = lux

Fehler_code = None
bmp = None
rtc = None

Fehler_pin = 17
def Fehlerindikator(Fehler_code):
    try:
        error_message = f"Lepmon#{sensor_id} Fehler {Fehler_code}"
        uart.write(error_message.encode('utf-8') + b'\n') 
    except Exception as e:
        print(f"Lora Message nicht gesendet: {e}")
        
    for f in range(1):
      for _ in range(Fehler_code):
        GPIO.output(Fehler_pin, GPIO.HIGH)
        time.sleep(0.25)
        GPIO.output(Fehler_pin, GPIO.LOW)
        time.sleep(0.5)
      data = {"Fehler_code": Fehler_code}  
      with open(os.path.join(current_folder, 'FehlerNummer.json'), "w") as json_file:
          json.dump(data, json_file)
      time.sleep(3)
      
    # schreibe Fehlercode und dessen Bedeutung nach Skript Ordner  
      
      
def set_pin_state(pin, state):
    GPIO.output(pin, state)         

GPIO.setup(Fehler_pin, GPIO.OUT)

#################################################################################################################
os.system('sudo raspi-config nonint do_i2c 0') # I2C aktivieren
i2c = busio.I2C(board.SCL, board.SDA)


try:
  pct = adafruit_pct2075.PCT2075(i2c)
  Sensorstatus_Temp = 1
except Exception as e:
    print(f"Fehler in der Verbindung zum Innen - Temperatursensor. Verbindung RPi - Sensor überprüfen: {e}")
    Fehlerindikator(1)
    Sensorstatus_Temp = 0
    pass
  
  
try: 
  bh = adafruit_bh1750.BH1750(i2c)
  Sensorstatus_Licht = 1
except Exception as e:
  print(f"Fehler in der Verbindung zum Lichtsensor. Verbindung RPi - Sensor überprüfen: {e}")
  Fehlerindikator(2) 
  Sensorstatus_Licht = 0
  pass
    
port = 1
address = 0x76
bus = smbus2.SMBus(port)

try:
  calibration_params = bme280.load_calibration_params(bus, address)
  Außensensor = bme280.sample(bus, address, calibration_params)
except Exception as e:
  print(f"Fehler in der Verbindung zum Außensensor. Verbindung RPi - Sensor überprüfen: {e}")
  #Fehlerindikator(9)
  Sensorstatus_hum = 0
  
  
try:
    ina = INA226(busnum=1, max_expected_amps=10, log_level=logging.INFO)
    ina.configure()
    ina.set_low_battery(5)
    Sensorstatus_Strom =1
  
    ina.wake(3)
    time.sleep(0.2)  
except Exception as e:
    print(f"Fehler in der Verbindung zum Spannungsmesser. Verbindung RPi - Sensor überprüfen: {e}")
    Sensorstatus_Strom =0
  
  
###
sensor_data = {} #dictionary für Messwerte

#lösche alles, was nicht mit #Lepmon beginnt und alles im Papierkorb
# for root, dirs, files in os.walk(zielverzeichnis, topdown=True):         # Überprüfen, ob der Name nicht mit "Lepmon#" beginnt und lösche es nicht
#     for name in files + dirs:
#         if not name.startswith("Lepmon#"):
#             try:
#                 os.remove(os.path.join(root, name)) if os.path.isfile(os.path.join(root, name)) else shutil.rmtree(os.path.join(root, name))
#                 print(f"{name} gelöscht")
#             except Exception as e:
#                 print(f"Fehler beim Löschen von {name}: {e}")
# try:# Papierkorb leeren
#     trash_path = os.popen("xdg-user-dir TRASH").read().strip()
# except Exception as e:
#     print(f"Fehler beim Abrufen des Papierkorbpfads: {e}")
#     trash_path = None
# 
# if trash_path:
#     try:
#         # Alle Dateien und Ordner im Papierkorb löschen
#         for item in os.listdir(trash_path):
#             item_path = os.path.join(trash_path, item)
#             if os.path.isfile(item_path):
#                 os.remove(item_path)
#                 print(f"{item} gelöscht")
#             elif os.path.isdir(item_path):
#                 shutil.rmtree(item_path)
#                 print(f"{item} gelöscht")
#         print("Papierkorb geleert")
#     except Exception as e:
#         print(f"Fehler beim Leeren des Papierkorbs: {e}")
# else:
#     print("Der Papierkorb konnte nicht gefunden werden.")




#################################################################################################################
######################################### Funktionen fürs Hauptprogramm #########################################
#################################################################################################################
control_pin = LED(27)
control_pin.on()

def update_sensor_data(key, value):
    sensor_data[key] = value
    
    
def Zeit_aktualisieren():
        global jetzt_local, jetzt_UTC, lokale_Zeit
        jetzt_UTC = datetime.utcnow()
        jetzt_local = datetime.now()
        lokale_Zeit = jetzt_local.strftime("%H:%M:%S")
        
        return jetzt_local, lokale_Zeit


def get_usb_path():
    """Ermittelt den Pfad des USB-Sticks."""
    global zielverzeichnis
    username = os.getenv('USER')
    media_path = f"/media/{username}"
    if os.path.exists(media_path):
        for item in os.listdir(media_path):
            zielverzeichnis = os.path.join(media_path, item)
            if os.path.ismount(zielverzeichnis):
                USB_PATH = zielverzeichnis
                return zielverzeichnis
    else:
        print("USB-Stick nicht gefunden.")
        # use the default path as Downloads
        zielverzeichnis = os.path.join("home", username, "Downloads")
        return zielverzeichnis
    return None
  

def berechne_zeitzone(lat,lng):
    lat = float(lat)
    lng = float(lng)
    tf = TimezoneFinder()
    
    # Finde die Zeitzone basierend auf den Koordinaten
    zeitzone_name = tf.timezone_at(lat=lat, lng=lng)
    
    if zeitzone_name is None:
        print("Keine Zeitzone gefunden für diese Koordinaten.")
        return None
    
    # Hole das aktuelle Datum und die Uhrzeit in der gefundenen Zeitzone
    Zeitzone = pytz.timezone(zeitzone_name)
    #lokale_zeit = datetime.now(Zeitzone)
    #print(Zeitzone)
    return Zeitzone


def get_twilight_times(lat, lng, date):
    global Abenddämmerung, Abenddämmerung_formatted, Abenddämmerung_short, Morgendämmerung, Morgendämmerung_formatted, Morgendämmerung_short, nacht_beginn_zeit, nacht_ende_zeit, Zeitzone
    Zeitzone = berechne_zeitzone(lat, lng)
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lng)
    #date_utc = date.astimezone(ephem.UTC) # Convert the local date to UTC
    date_utc = date.astimezone(pytz.utc)
    
    sunset = ephem.localtime(observer.next_setting(ephem.Sun(), start=date_utc)) # Calculate times based on UTC time
    Abenddämmerung = ephem.localtime(observer.next_setting(ephem.Sun(), use_center=True, start=date_utc))# Calculate times based on UTC time
    
    
    Abenddämmerung_local = Abenddämmerung.astimezone(Zeitzone)    
    nacht_beginn_zeit = Abenddämmerung_local - Dämmerungspuffer
    nacht_beginn_zeit = nacht_beginn_zeit.replace(tzinfo=None)

    Abenddämmerung_formatted = Abenddämmerung_local.strftime("%Y-%m-%d  %H:%M:%S")
    Abenddämmerung_short = Abenddämmerung_local.strftime("%H:%M:%S")

    
    next_day = date + timedelta(days=1)# For the following day
    next_day_utc = next_day.astimezone(ephem.UTC)
    
    sunrise = ephem.localtime(observer.previous_rising(ephem.Sun(), start=next_day_utc))
    Morgendämmerung = ephem.localtime(observer.previous_rising(ephem.Sun(), use_center=True, start=next_day_utc))
    
    Morgendämmerung_local = Morgendämmerung.astimezone(Zeitzone)
    nacht_ende_zeit = Morgendämmerung_local + Dämmerungspuffer
    nacht_ende_zeit = nacht_ende_zeit.replace(tzinfo=None)
    Morgendämmerung_formatted = Morgendämmerung_local.strftime("%Y-%m-%d  %H:%M:%S")
    Morgendämmerung_short =  Morgendämmerung_local.strftime("%H:%M:%S")
 
 
def get_disk_space(path): ####Speicher Abfrage####
    try:
        stat = os.statvfs(path) # Erhalte Informationen über den Dateisystemstatus
        total_space = stat.f_frsize * stat.f_blocks # Gesamtgröße des Dateisystems in Bytes
        used_space = stat.f_frsize * (stat.f_blocks - stat.f_bfree) # Verwendeter Speicherplatz in Bytes
        free_space = stat.f_frsize * stat.f_bavail # Freier Speicherplatz in Bytes
        
        # Konvertiere Bytes in GB
        total_space_gb = total_space / (1024 ** 3)
        used_space_gb = used_space / (1024 ** 3)
        free_space_gb = free_space / (1024 ** 3)
        
        used_percent = (used_space / total_space) * 100 # Berechne Prozentanteil des belegten und freien Speicherplatzes
        free_percent = (free_space / total_space) * 100
        
        return total_space_gb, used_space_gb, free_space_gb, used_percent, free_percent
    except Exception as e:
        log_schreiben(f"Fehler beim Abrufen des Speicherplatzes: {e}")
        return None, None, None, None, None
      



#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------

def initialisiere_logfile():
  global log_dateipfad  
  jetzt_local = datetime.now()
  lokale_Zeit = jetzt_local.strftime("%H:%M:%S")
  
  ordnerpfad = erstelle_ordner_und_dateiname()
  datum_nacht_beginn = jetzt_local.strftime("%Y%m%d")
  ordnername = os.path.basename(ordnerpfad)
  log_dateiname = f"{ordnername}.log"
  log_dateipfad = os.path.join(ordnerpfad, log_dateiname)
  
  try:
        # Initiales Erstellen des Logfiles
        if not os.path.exists(log_dateipfad):
            with open(log_dateipfad, 'w') as f:
                f.write(f"{lokale_Zeit}; Logfile erstellt: {log_dateipfad}\n")
  except Exception as e:
        lokale_Zeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{lokale_Zeit}; Fehler beim Erstellen des Logfiles: {e}")
        Fehlerindikator(4)
        raise
        return None

  return log_dateipfad


def log_schreiben(text):
    """Schreibt den übergebenen Text in das Logfile."""
    try:
        log_dateipfad = initialisiere_logfile()
        if log_dateipfad is None:
            print("Logfile konnte nicht erstellt werden.")
            return
    except Exception as e:
        print("Logfile Feherl:" +str(e))
        #sys.exit(0)

    try:
        with open(log_dateipfad, 'a') as f:
            f.write(text + '\n')
    except Exception as e:
        print(f"Fehler beim Schreiben ins Logfile: {e}")
        
        
        

# Funktion zum Erstellen des Ordners und Bildernamen
def erstelle_ordner_und_dateiname():
    global aktueller_nachtordner
    jetzt_local = datetime.now()
    Jahr = jetzt_local.strftime("%Y")  # Aktualisiere das Datum hier
    Monat = jetzt_local.strftime("%m")
    Tag = jetzt_local.strftime("%d") 
    uhrzeit_erstes_bild = jetzt_local.strftime("%H%M")
    ordnername = f"{projekt_name}{sensor_id}_{bundesland}_{stadt_code}_{Jahr}-{Monat}-{Tag}_T_{uhrzeit_erstes_bild}"
    try:
        if aktueller_nachtordner is None or not os.path.exists(aktueller_nachtordner):
            aktueller_nachtordner = os.path.join(zielverzeichnis, ordnername)
            os.makedirs(aktueller_nachtordner, exist_ok=True)
    except Exception as e:
        Fehlerindikator(4)

    return aktueller_nachtordner

def dim_up(Blitz_Änderung_zeit):
   pwm.start(0)
   for duty_cycle in range(0, 99,1):
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(Blitz_Änderung_zeit / 100)
        
      
def dim_down(Blitz_Änderung_zeit):  
  pwm.start(100)
  for duty_cycle in range(99, 0, -1):
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(Blitz_Änderung_zeit / 100)
  pwm.start(0)
  
# Aufnehmen eines Bildes
def nehme_bild_auf():
    time.sleep(1)
    global dateipfad, Leistung_An
    ordnerpfad = erstelle_ordner_und_dateiname()
    Jahr = jetzt_local.strftime("%Y")  # Aktualisiere das Datum hier
    Monat = jetzt_local.strftime("%m")
    Tag = jetzt_local.strftime("%d") 
    dateiname = f"{projekt_name}{sensor_id}_{bundesland}_{stadt_code}_{Jahr}-{Monat}-{Tag}_T_{jetzt_local.strftime('%H%M')}.tiff"
    dateipfad = os.path.join(ordnerpfad, dateiname)

    if Kamera == "Allied Vision Alvium":
      # Vimba zum aufnehmen
      with Vimba.get_instance() as vimba:
         cams = vimba.get_all_cameras()
         with cams[0] as cam:
              try:
                 cam.set_pixel_format(PixelFormat.Bgr8)
                 settings_file = '/home/Ento/Lepmon_Einstellungen/Kamera_Einstellungen.xml'.format(cam.get_id())
                 cam.load_settings(settings_file, PersistType.All)                 
                 
                 dim_up(Blitz_Änderung_zeit)
                 #VIS_LED.on()
                 messe_strom()
                 Leistung_An = power
                 
                 frame = cam.get_frame(timeout_ms=864000000).as_opencv_image()
                 dim_down(Blitz_Änderung_zeit)
                 #VIS_LED.off()
                 cv2.imwrite(dateipfad, frame)
                 log_schreiben(f"{lokale_Zeit}; Bild gespeichert: {dateiname}")
                 image_message = f"Lepmon#{sensor_id} Bild gespeichert: {dateiname}"
                 try:
                    uart.write(image_message.encode('utf-8') + b'\n')
                 except Exception as e:
                      print(f"Fehler beim Lora senden: {e}")
                      pass   
              except Exception as e:
                  log_schreiben(f"{lokale_Zeit}; Fehler beim Bilderspeichern: {e}")
                  pass
                  
    elif Kamera == "Arducam Hawkeye":
      Aufnahme = 'libcamera-still -t 5000 -n -o'  + str(ordnerpfad) + '/' + str(dateiname)
      log_schreiben(Aufnahme)
      try:
            os.system(Aufnahme)
            log_schreiben(f"{lokale_Zeit}; Bild gespeichert: {dateiname}")
      except Exception as e:
            log_schreiben(f"{lokale_Zeit}; Fehler beim Bilderspeichern: {e}")
            pass
    elif Kamera == "HIK":
      '''
      this will request to take an image from imswitch and save it on disk 
      '''
      image = client.recordingManager.snapNumpyToFastAPI()
      cv2.imwrite(dateipfad, image)
      log_schreiben(f"{lokale_Zeit}; Bild gespeichert: {dateiname}")
    return Leistung_An      

csv_dateipfad = ""
# Erstellen oder Aktualisieren der CSV-Datei
def erstelle_und_aktualisiere_csv():
    global aktueller_nachtordner, csv_dateipfad
    
    ordnerpfad = erstelle_ordner_und_dateiname()
    datum_nacht_beginn = jetzt_local.strftime("%Y%m%d")
    ordnername = os.path.basename(ordnerpfad)  # Extrahiere den Ordnername aus dem vollständigen Pfad
    csv_dateiname = f"{ordnername}.csv"
    csv_dateipfad = os.path.join(ordnerpfad, csv_dateiname)
    file_exists = os.path.exists(csv_dateipfad)

    # Überprüfe, ob die CSV-Datei bereits existiert
    if not os.path.exists(csv_dateipfad):
        # Erstelle die CSV-Datei und schreibe die Spaltennamen
        with open(csv_dateipfad, mode='w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter='\t')  # Setze den Tabulator als Trennzeichen
            csv_writer.writerow(["#UTC Time:", jetzt_UTC.strftime("%Y-%m-%d  %H:%M:%S")])
            csv_writer.writerow(["#Longitude:",lng]) 
            csv_writer.writerow(["#Latitude:", lat])
            csv_writer.writerow([])
            csv_writer.writerow(["#errechneter Beginn Abenddämmerung:",Abenddämmerung_formatted])
            csv_writer.writerow(["#errechnetes Ende Morgendämmerung:", Morgendämmerung_formatted])
            csv_writer.writerow([])
            csv_writer.writerow(["#Machine ID:", sensor_id])
            csv_writer.writerow(["#Verwendete Kamera:",Kamera])
            csv_writer.writerow(["#Dämmerungs Schwellenwert:",Dämmerungsschwellenwert])
            csv_writer.writerow(["#Aufnahme Intervall:",Intervall])
            if Kontinuität:
              csv_writer.writerow([])
              csv_writer.writerow(["#Aufnahme Modus:","mit Unterbrechung"])
              csv_writer.writerow(["#UV Anlockphase (UV an):",UV_anlocken])
              csv_writer.writerow(["#UV cool down (UV aus):",UV_freilassen])
            csv_writer.writerow([])
            csv_writer.writerow(["********************"])
            csv_writer.writerow([])
            csv_writer.writerow(["#Starting new Programme"])
            csv_writer.writerow(["#Local Time:", jetzt_local.strftime("%Y-%m-%d  %H:%M:%S")])
            #csv_writer.writerow(["#Local Time:", lokale_Zeit])
            csv_writer.writerow([])
            
    with open(csv_dateipfad, mode='a', newline='') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=sensor_data.keys(), delimiter='\t')
        
        if not file_exists:
            csv_writer.writeheader()
        
        csv_writer.writerow(sensor_data)
        
    return csv_dateipfad        

def checksum(dateipfad, algorithm="md5"):

  try:
    hash_func = hashlib.new(algorithm)  # Erstelle ein neues Hash-Objekt
  
    with open(dateipfad, "rb") as file: # Datei im Binärmodus lesen und Hash aktualisieren
      while chunk := file.read(8192):  # Datei in 8-KB-Blöcken lesen
        hash_func.update(chunk)
 
    checksum = hash_func.hexdigest() # Prüfsumme als Hex-String
  
    dir_name = os.path.dirname(dateipfad) # Erzeuge den Pfad für die Prüfsummen-Datei
    base_name = os.path.basename(dateipfad)
    checksum_file_name = f"{base_name}.{algorithm}"
    checksum_dateipfad = os.path.join(dir_name, checksum_file_name)
  
    with open(checksum_dateipfad, "w") as checksum_file:
      checksum_file.write(checksum) # Prüfsumme in der Datei speichern
  
  except Exception as e:
     print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
     log_schreiben(f"{lokale_Zeit}; Fehler beim schreiben der Checksumme: {e}")
     
     
def LepiLED_start():
    global LepiLed_pwm, LepiLed_pwm_active
    log_schreiben(f"{lokale_Zeit}; LepiLED eingeschaltet")

    LepiLed_pwm.start(0)
    for duty_cycle in range(0, 99, 1):
        LepiLed_pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(Blitz_Änderung_zeit / 100)
        LepiLed_pwm.ChangeDutyCycle(100)
    LepiLed_pwm_active = True
    LepiLED_message = f"Lepmon#{sensor_id} LepiLED eingeschaltet"
    try:
        uart.write(LepiLED_message.encode('utf-8') + b'\n')
    except Exception as e:
        print(f"Fehler beim Lora senden: {e}")
        pass   
    
    
    
def LepiLED_ende():
    global LepiLed_pwm, LepiLed_pwm_active
    log_schreiben(f"{lokale_Zeit}; LepiLED ausgeschaltet")

    LepiLed_pwm.start(100)
    for duty_cycle in range(99, 0, -1):
        LepiLed_pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(Blitz_Änderung_zeit / 100)
        LepiLed_pwm.ChangeDutyCycle(0)
    LepiLed_pwm_active = False
    LepiLed_pwm.start(0)
    
    
def Luxwert_lesen():
  global LUX
  try:
   LUX = adafruit_bh1750.BH1750(i2c)
   LUX = LUX.lux
  except Exception as e:
    log_schreiben(f"{lokale_Zeit}; Fehler in der Verbindung zum Lichtsensor. Verbindung RPi - Multiplexor - Sensor überprüfen. Wert des Umgebungslichtes auf Schwellenwert gesetzt: {e}")
    Fehlerindikator(8)
    LUX = Dämmerungsschwellenwert
    pass  
  
  
def messe_strom():
  global bus_voltage, shunt_voltage, current, power, Status_Strom     
  
  try:
    ina = INA226(busnum=1, max_expected_amps=10, log_level=logging.INFO)
    ina.configure()
    ina.set_low_battery(5)
    Sensorstatus_Strom =1
  
    ina.wake(3)
    time.sleep(0.2)    

    bus_voltage = round(ina.voltage(),2)
    shunt_voltage = round(ina.shunt_voltage(),2)
    current = round(ina.current(),2)
    power = round(ina.power(),2)
    Status_Strom = 1

    
  except Exception as e:
    print(f"Fehler in der Verbindung zum Spannungsmesser. Verbindung RPi - Sensor überprüfen: {e}")
    bus_voltage = "---"
    shunt_voltage = "---"
    current = "---"
    power = "---"
    Status_Strom = 0
    pass

  return bus_voltage, shunt_voltage, current, power, Status_Strom

def json_einlesen(dateipfad):
    with open(dateipfad, 'r') as datei:
        daten = json.load(datei)
    return daten
  
  
def breitengrad_in_liste(breitengrad,längengrad):
  global breitengrad_list, längengrad_list
  
  if breitengrad / 10 < 1:
    latitude_str = str(breitengrad).replace('.', '')
    latitude_str = str(0)+latitude_str
  
  elif breitengrad / 10 >= 1:
    latitude_str = str(breitengrad).replace('.', '')
    
  fehlende_nullen = 9 - len(latitude_str)
  if fehlende_nullen > 0:
      latitude_str = latitude_str + '0' * fehlende_nullen
  
  breitengrad_list = [int(x) for x in latitude_str]

  if 0.1 > längengrad / 100 >= 0.01:
    longitude_str = str(längengrad).replace('.', '')
    longitude_str = str(0)+str(0)+longitude_str  
    
  elif 1 > längengrad / 100 >= 0.1:
    longitude_str = str(längengrad).replace('.', '')
    longitude_str = str(0)+longitude_str
    
  elif längengrad / 100 >= 1:
    longitude_str = str(längengrad).replace('.', '')

  fehlende_nullen = 10 - len(longitude_str)
  if fehlende_nullen > 0:
      longitude_str = longitude_str + '0' * fehlende_nullen

    
  längengrad_list = [int(x) for x in longitude_str]   
  

def check_usb_connection(zielverzeichnis):
    try:
        os.path.exists(zielverzeichnis)
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "USB Stick", font = oled_font, fill = "white")
          draw.text((5, 25), "richtig verbunden", font = oled_font, fill = "white")
        time.sleep(4)
    except:
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "Fehler 4", font = oled_font, fill = "white")
          draw.text((5, 25), "USB nicht gefunden", font = oled_font, fill = "white")
          draw.text((5, 45), "Falle neu starten", font = oled_font, fill = "white")
        Fehlerindikator(4)
        time.sleep(4)
        sys.exit(4)

  
#################################################################################################################
################################################# kombinierte Funktionen #################################################
#################################################################################################################
def Zeit_nächste_Aufnahme():
  naechste_minute = jetzt_local.replace(second=0, microsecond=0) + timedelta(minutes=Intervall)
  zeit_bis_naechste_minute = (naechste_minute - jetzt_local).total_seconds()
  log_schreiben(f"{lokale_Zeit}, Warten bis zur nächsten Aufnahme: {round(zeit_bis_naechste_minute,0)} Sekunden")
  time.sleep(zeit_bis_naechste_minute)


def Daten_erfassen():
  global Kamera_Fehlerserie
  Kamera_Strom.on()
  time.sleep(1)
  Zeit_aktualisieren()
  Timecode = f"{sensor_id}_{bundesland}_{stadt_code}_{jetzt_local.strftime('%Y')}_{jetzt_local.strftime('%m')}_{jetzt_local.strftime('%d')}_T_{jetzt_local.strftime('%H%M')}"
  update_sensor_data("Code", Timecode)
  try:
    bh = adafruit_bh1750.BH1750(i2c)
    bh = round(bh.lux,2)
    Status_Licht = 1
  except Exception as e:
    log_schreiben(f"{lokale_Zeit}; Fehler in der Verbindung zum Lichtsensor. Verbindung RPi - Sensor überprüfen: {e}")
    Fehlerindikator(2)
    bh = Sensor(Dämmerungsschwellenwert)
    Status_Licht = 0
    pass  
  update_sensor_data("Umgebungslicht [LUX]", bh)
  update_sensor_data("Status_Licht", Status_Licht)
  
  messe_strom()
  Leistung_Aus = power
  
  try: 
    nehme_bild_auf()
    checksum(dateipfad, algorithm="md5")
    Kamera_Fehlerserie = 0
    Status_Kamera = 1

  except Exception as e:
    print("WARNUNG Kein Bild aufgenommen: {e}")  
    Status_Kamera = 0
    Kamera_Fehlerserie = Kamera_Fehlerserie+1
    Fehlerindikator(5)
    log_schreiben(f"{lokale_Zeit}; Fehler bei der Verbindung zur Kamera: {e}")
  update_sensor_data("Kamera Status", Status_Kamera)
  
  if Status_Strom == 1:
      try:    
          Leistung_LED = round((Leistung_An - Leistung_Aus)/1000,2)
          update_sensor_data("VIS LED [W]", Leistung_LED)
          if 1 < Leistung_LED < 2.5:
              log_schreiben(f"{lokale_Zeit}; Warnung: Beleuchtung/Visible LED verdunkelt")
              try:
                beleuchtungs_message = f" Warnung: Beleuchtung/Visible LED verdunkelt"
                uart.write(beleuchtungs_message.encode('utf-8') + b'\n') 
              except Exception as e:
                print(f"Lora Message nicht gesendet: {e}")
                
          if 1 >= Leistung_LED:
              log_schreiben(f"{lokale_Zeit}; Warnung: Beleuchtung/Visible LED nicht an")
             
              try:
                beleuchtungs_message = f" Warnung: Beleuchtung/Visible LED nicht an"
                uart.write(beleuchtungs_message.encode('utf-8') + b'\n') 
              except Exception as e:
                print(f"Lora Message nicht gesendet: {e}")            
      except:
          pass
  elif Status_Strom == 0:
      update_sensor_data("VIS LED [W]", "---")
      
      
  if Kamera_Fehlerserie == 3:
    log_schreiben(f"{lokale_Zeit}; Fehler 5: Verbindung zur Kamera erneut fehlgeschlagen. Falle startet neu")
    Ende()
    sys.exit(5)
  time.sleep(1)  
  try:
     pct = adafruit_pct2075.PCT2075(i2c)
     pct = round(pct.temperature,2)
     Status_innen = 1
  except Exception as e:
    log_schreiben(f"{lokale_Zeit}; Fehler in der Verbindung zum Innensensor. Verbindung RPi -  Sensor überprüfen: {e}")
    Fehlerindikator(1)
    pct = "---"
    Status_innen = 0
    pass
  update_sensor_data("Innentemperatur [C]", pct)
  update_sensor_data("Status_innen", Status_innen)
  
  
  try: 
    calibration_params = bme280.load_calibration_params(bus, address)
    Außensensor = bme280.sample(bus, address, calibration_params)
    Temperatur = round(Außensensor.temperature,2)
    Luftdruck = round(Außensensor.pressure,2)
    Luftfeuchte =  round(Außensensor.humidity,2)
    Status_außen = 1
  except Exception as e:  
    log_schreiben(f"{lokale_Zeit}; Fehler in der Verbindung zum Außensensor. Verbindung RPi -  Sensor überprüfen: {e}")
    Fehlerindikator(9)
    Temperatur = "---"
    Luftdruck = "---"
    Luftfeuchte =  "---"
    Status_außen = 0
    pass
  update_sensor_data("Außentemperatur [C]", Temperatur)
  update_sensor_data("Luftdruck [hPa]", Luftdruck)
  update_sensor_data("Luftfeuchte [%]", Luftfeuchte)  
  update_sensor_data("Status_außen", Status_außen)
  
  try:
    messe_strom()
    update_sensor_data("bus_voltage [V]", bus_voltage)
    update_sensor_data("shunt_voltage [V]", shunt_voltage)
    update_sensor_data("current [mA]", current)  
    update_sensor_data("power [mW]", power)  
  except:
      pass
  time.sleep(1)  
  Kamera_Strom.off()
  
  # send update sensor data to rest (e.g. imswitch probably as json)
  def sendSensorDataToImSwitch():
    import requests
    # URL und Port anpassen
    url = f"https://{IMSWITCH_URL}:{IMSWITCH_PORT}/LepmonController/setSensorData"
    data = {
        "innerTemp": pct,
        "outerTemp": Temperatur,
        "humidity": Luftfeuchte,
        "sensor_id": sensor_id,
        "Status_Licht": Status_Licht,
        "Umgebungshelligkeit": bh,
        "Status_Strom": Status_Strom,
        "Leistung_LED": Leistung_LED,
        "bus_voltage": bus_voltage,
        "shunt_voltage": shunt_voltage,
        "current": current,
        "power": power,
        "Status_innen": Status_innen,
        "Status_außen": Status_außen,
        "Luftdruck": Luftdruck
    }
    # Senden der Anfrage
    response = requests.get(url, json=data, timeout=1, verify=False)

    # Überprüfen der Antwort
    if response.status_code == 200:
        print("Daten erfolgreich gesendet:", response.json())
    else:
        print("Fehler beim Senden der Daten:", response.status_code, response.text)
  
  sendSensorDataToImSwitch()
  
  try:
    sensorik_message = "\n".join([
        f"Lepmon#{sensor_id}",
        f" Status_Lichtsensor: {Status_Licht}",
        f" Umgebungshelligkeit: {bh} Lux",
        f"",
        f" Status Stromsensor: {Status_Strom}",
        f" Aufnahmeleistung:{Leistung_LED} W (Bildaufnahme)",
        f" bus_voltage: {bus_voltage} V",        
        f" shunt_voltage: {shunt_voltage} V",
        f" current: {current} mA",
        f" power: {power} mW",        
        f"",
        f" Status Innensensor: {Status_innen}",
        f" Innentemperatur: {pct} Celsius",
        f"",     
        f" Status Aussensensor: {Status_außen}",
        f" Temperatur: {Temperatur} Celsius",
        f" Luftdruck: {Luftdruck} hPa",
        f" Luftfeuchte: {Luftfeuchte}%",
        f"",
        f"",
        ])
    uart.write(sensorik_message.encode('utf-8') + b'\n') 
  except Exception as e:
    print(f"Lora Message nicht gesendet: {e}")

def Ende():  
    LepiLED_ende()
    Zeit_aktualisieren()                
    log_schreiben(f"{lokale_Zeit}; Ordner zurückgesetzt")
    control_pin.off()
    try:
      log_schreiben(f"{lokale_Zeit}; Logfile geschlossen.")
      sys.stdout = sys.__stdout__
      sys.stderr = sys.__stderr__
      time.sleep(3)
      
    except Exception as e:
      log_schreiben(f"{lokale_Zeit}; Fehler beim Schließen des Logfiles: {e}")  
      pass
    
    ### berechne die checksumme für csv und log
    checksum(log_dateipfad, algorithm="md5")
    try:
        checksum(csv_dateipfad, algorithm="md5")
    except:
        pass
    
    aktueller_nachtordner = None # Nachtordner zurücksetzen
    
    try:
        end_message = f"Lepmon#{sensor_id} Falle startet neu"
        uart.write(end_message.encode('utf-8') + b'\n') 
    except Exception as e:
        print(f"Lora Message nicht gesendet: {e}")
        
    time.sleep(5)
    os.system('sudo reboot')
    print("Ende")

def fokusieren():
    Kamera_Strom.on()
    print("Strom an")
    with canvas(oled) as draw:
        draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
        draw.text((5, 5), "fokussieren", font = oled_font, fill = "white") 
        draw.text((5, 25), "bis Anzeigewert ", font = oled_font, fill = "white")
        draw.text((5, 45), "Maximum erreicht", font = oled_font, fill = "white")
    
    time.sleep(9)
    print("starte")
    FokusFehler = 0
    maximum = 0
    Zeit_aktualisieren()
    Fokus_neu = True
    pwm.start(100)
    Belichtungszeit = 150
    while GPIO.input(PIN_EINGABE) is not GPIO.LOW:
        print("Bild")
        blau.on()
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras()
            with cams[0] as cam:
                try:
                    cam.set_pixel_format(PixelFormat.Bgr8)
                    settings_file = '/home/Ento/Lepmon_Einstellungen/Kamera_Einstellungen.xml'.format(cam.get_id())
                    cam.load_settings(settings_file, PersistType.All)
                    
                    exposure_time = cam.ExposureTime
                    exposure_time.set(Belichtungszeit*1000)
                    print(f"Exposure geändert:{(exposure_time.get()/1000):.0f}")
                 
                    frame = cam.get_frame(timeout_ms=864000000).as_opencv_image()
                    FokusFehler = 0
                except:
                    FokusFehler +=1
        print(FokusFehler)            
        if FokusFehler ==2:
            Fehlerindikator(5)
            with canvas(oled) as draw:
                        draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                        draw.text((5, 5), "Fehler Kamera", font = oled_font, fill = "white") 
                        draw.text((5, 25), "überlastet", font = oled_font, fill = "white")
                        draw.text((5, 45), "Falle neu starten", font = oled_font, fill = "white")
            print("Kamera nicht gefunden")
            Fehlerindikator(5)
            time.sleep(5)
        
        blau.off()
        print("analyse")
        GUI_pin.on()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sharpness = round(cv2.Laplacian(gray, cv2.CV_64F).var(),0) 	# compute the Laplacian of the image and then return the focus - measure, which is simply the variance of the Laplacian
        if sharpness > maximum:
            maximum = sharpness
        
        for _ in range(25):
            if GPIO.input(PIN_HOCH) is GPIO.LOW:
                if Belichtungszeit >20:
                    Belichtungszeit += 10
                if Belichtungszeit <= 20:
                    Belichtungszeit +=1

            if GPIO.input(PIN_RUNTER) is GPIO.LOW:
                if Belichtungszeit >20:
                    Belichtungszeit -= 10
                if Belichtungszeit <= 20:
                    Belichtungszeit -=1
            
            with canvas(oled) as draw:
                draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                draw.text((5, 5), f"Schärfewert: {sharpness}", font = oled_font, fill = "white")
                draw.text((5, 25), f"peak: {maximum}", font = oled_font, fill = "white")
                draw.text((5, 45), f"Exposure: {Belichtungszeit} ms", font = oled_font, fill = "white")
            time.sleep(.1)
            
        if GPIO.input(PIN_EINGABE) is GPIO.LOW: # Enter drücken, um fokusieren zu verlassen
            break
        GUI_pin.off()
        time.sleep(.25)
            
                
                
def eingabe_gps_koordinaten():
    
    global Breite, Länge
    Zeit_aktualisieren() 
    breitengrad_in_liste(breitengrad,längengrad)
    
    aktuelle_position = 0
    Wahlmodus = 1
    while True:
      GUI_pin.on()  
      if Wahlmodus < 3:
        if Wahlmodus == 1 :
            if aktuelle_position < 2:
                positionszeiger = pol+"_" * aktuelle_position
            else:
                positionszeiger =  pol+"__." +"_" * (aktuelle_position -2)
            positionszeiger += "x"
            
            with canvas(oled) as draw:
              draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
              draw.text((5, 5), "Latitude eingeben", font = oled_font, fill = "white")
              draw.text((5, 25), f"{pol}{breitengrad_list[0]}{breitengrad_list[1]}.{breitengrad_list[2]}{breitengrad_list[3]}{breitengrad_list[4]}{breitengrad_list[5]}{breitengrad_list[6]}{breitengrad_list[7]}{breitengrad_list[8]}", font = oled_font, fill = "white")
              draw.text((5, 40), positionszeiger, font = oled_font, fill = "white")
            
        elif Wahlmodus == 2 :
            if aktuelle_position < 3:
                positionszeiger = block + "_" * aktuelle_position
            else:
                positionszeiger = block + "___." + "_" * (aktuelle_position -3)
            positionszeiger += "x"
            with canvas(oled) as draw:
              draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
              draw.text((5, 5), "Longitude eingeben", font = oled_font, fill = "white")
              draw.text((5, 25), f"{block}{längengrad_list[0]}{längengrad_list[1]}{längengrad_list[2]}.{längengrad_list[3]}{längengrad_list[4]}{längengrad_list[5]}{längengrad_list[6]}{längengrad_list[7]}{längengrad_list[8]}{längengrad_list[9]}", font = oled_font, fill = "white")
              draw.text((5, 40), positionszeiger, font = oled_font, fill = "white")

        # Auf Tastendruck warten und entsprechende Aktion durchführen
        if GPIO.input(PIN_HOCH) == GPIO.LOW:
            if Wahlmodus == 1 :
                breitengrad_list[aktuelle_position] = (breitengrad_list[aktuelle_position] + 1) % 10
            elif Wahlmodus == 2 :
                längengrad_list[aktuelle_position] = (längengrad_list[aktuelle_position] + 1) % 10
        
        elif GPIO.input(PIN_RUNTER) == GPIO.LOW:
            if Wahlmodus == 1 :
                breitengrad_list[aktuelle_position] = (breitengrad_list[aktuelle_position] - 1) % 10
            elif Wahlmodus == 2 :
                längengrad_list[aktuelle_position] = (längengrad_list[aktuelle_position] - 1) % 10
        
        elif GPIO.input(Rechts) == GPIO.LOW:
          if Wahlmodus == 1 :
            aktuelle_position = (aktuelle_position + 1) % 9
            aktuelle_position = aktuelle_position
          elif   Wahlmodus == 2 :
           aktuelle_position = (aktuelle_position + 1) % 10
           aktuelle_position = aktuelle_position
        
        elif GPIO.input(PIN_EINGABE) == GPIO.LOW:
            Wahlmodus +=1
            aktuelle_position = 0
        
      elif Wahlmodus == 3:
          GUI_pin.off()
          break

      time.sleep(0.005)  # Kurze Pause für die Stabilität
      Breite = float(f"{breitengrad_list[0]}{breitengrad_list[1]}.{breitengrad_list[2]}{breitengrad_list[3]}{breitengrad_list[4]}{breitengrad_list[5]}{breitengrad_list[6]}{breitengrad_list[7]}{breitengrad_list[8]}")
      Länge = float(f"{längengrad_list[0]}{längengrad_list[1]}{längengrad_list[2]}.{längengrad_list[3]}{längengrad_list[4]}{längengrad_list[5]}{längengrad_list[6]}{längengrad_list[7]}{längengrad_list[8]}{längengrad_list[9]}")
    lng = Länge
    lat = Breite
    
    
    if lat != gelesen_lat:
        log_schreiben(f"{lokale_Zeit}; Geografische Breite neu eingegeben")
    if lat == gelesen_lat:
        log_schreiben(f"{lokale_Zeit}; Geografische Breite unverändert")  
      
    if lng != gelesen_lng:
        log_schreiben(f"{lokale_Zeit}; Geografische Länge neu eingegeben")
    if lng == gelesen_lng:
        log_schreiben(f"{lokale_Zeit}; Geografische Länge unverändert")
    
    return lng, lat
          
def Uhrzeit_stellen():
    current_datetime = datetime.now()
    date_time_str = current_datetime.strftime("%Y%m%d%H%M%S")
    date_time_list = [int(digit) for digit in date_time_str]
    
    aktuelle_position = 0
    Wahlmodus = 1
    try:
     while True:
        GUI_pin.on() 
        if Wahlmodus < 3:
            if Wahlmodus == 1:
              if aktuelle_position < 4:
                positionszeiger_time = "_" * aktuelle_position
              elif 4 <= aktuelle_position < 6:
                positionszeiger_time = "_"*4 + "-" +"_" * (aktuelle_position-4)
              elif aktuelle_position >= 6:
                positionszeiger_time = "_"*4 + "-" + "_" *2 + "-" + "_" * (aktuelle_position-6)
              positionszeiger_time += "x"
              
              with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                  draw.text((5, 5), "Datum einstellen", font = oled_font, fill = "white")
                  draw.text((5, 25), f"{date_time_list[0]}{date_time_list[1]}{date_time_list[2]}{date_time_list[3]}-{date_time_list[4]}{date_time_list[5]}-{date_time_list[6]}{date_time_list[7]}", font = oled_font, fill = "white")
                  draw.text((5, 40), positionszeiger_time, font = oled_font, fill = "white")

            elif Wahlmodus == 2:
              if 8 <= aktuelle_position <10:
                positionszeiger = "_" * (aktuelle_position-8)
              elif 10 <= aktuelle_position < 12:
                positionszeiger = "__:" + "_" * (aktuelle_position-10)
              elif aktuelle_position >=12 :
                positionszeiger = "__:__" + ":" + "_" * (aktuelle_position-12)
              positionszeiger += "x"
              
              with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                  draw.text((5, 5), "Zeit einstellen", font = oled_font, fill = "white")
                  draw.text((5, 25), f"{date_time_list[8]}{date_time_list[9]}:{date_time_list[10]}{date_time_list[11]}:{date_time_list[12]}{date_time_list[13]}", font = oled_font, fill = "white")
                  draw.text((5, 40), positionszeiger, font = oled_font, fill = "white")
        
            if GPIO.input(PIN_HOCH) == GPIO.LOW:
                date_time_list[aktuelle_position] = (date_time_list[aktuelle_position] + 1) % 10
            
            elif GPIO.input(PIN_RUNTER) == GPIO.LOW:
                date_time_list[aktuelle_position] = (date_time_list[aktuelle_position] - 1) % 10
            
            elif GPIO.input(Rechts) == GPIO.LOW:
              if Wahlmodus == 1:
                aktuelle_position = (aktuelle_position + 1) % 8 
                aktuelle_position = aktuelle_position
              elif Wahlmodus == 2:
                if aktuelle_position != 13:  # Anstatt 14, da die Positionen 8 bis 13 die Zeit HH:MM:SS repräsentieren
                    aktuelle_position = (aktuelle_position + 1) % 14
                    aktuelle_position = aktuelle_position
                else:
                    aktuelle_position = 8  # Zurück zur Position 8 für Stunden (HH) wenn Sekunden (SS) bearbeitet wurden
                    aktuelle_position = aktuelle_position
        
            elif GPIO.input(PIN_EINGABE) == GPIO.LOW:
                Wahlmodus += 1
                aktuelle_position = 8
                with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
        
        elif Wahlmodus == 3:
            GUI_pin.off()
            break

        time.sleep(0.1)  # Kurze Pause für die Stabilität
     # Construct the command for setting system time
     system_time_str = f"{date_time_list[0]}{date_time_list[1]}{date_time_list[2]}{date_time_list[3]}-{date_time_list[4]}{date_time_list[5]}-{date_time_list[6]}{date_time_list[7]} {date_time_list[8]}{date_time_list[9]}:{date_time_list[10]}{date_time_list[11]}:{date_time_list[12]}{date_time_list[13]}"
     command = f"sudo timedatectl set-time '{system_time_str}'"
    
     # Execute the command
     os.system("sudo timedatectl set-ntp false")
     os.system(command)
     with canvas(oled) as draw:
      draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
      draw.text((5, 5), "Zeit aktualisiert", font = oled_font, fill = "white")
     start_time = time.time()
     while time.time() - start_time < 5:
        current_time = datetime.now().strftime("%H:%M:%S")
    
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "aktuelle Uhrzeit", font = oled_font, fill = "white")        
          draw.text((5, 25), current_time, font = oled_font, fill = "white") 
        time.sleep(1) 
     log_schreiben(f"{current_time}; Eingabe Menü vom Benutzer geöffnet")
     log_schreiben(f"{current_time}; Uhrzeit vom Nutzer neu gestellt")
     
    except:
        log_schreiben(f"{current_time}; Eingabe Menü vom Benutzer geöffnet")
        log_schreiben(f"{current_time}; Fehler 3: Uhrezeit konnte nicht neu gestellt werden")
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "Fehler 3", font = oled_font, fill = "white")        
          draw.text((5, 25), "Hardware Uhr", font = oled_font, fill = "white")      
        Fehlerindikator(3)

class SensorData:
    try:
     def __init__(self, innentemperatur, umgebungslicht, außentemperatur, luftdruck, luftfeuchte):
        self.innentemperatur = innentemperatur
        self.umgebungslicht = umgebungslicht
        self.außentemperatur = außentemperatur
        self.luftdruck = luftdruck
        self.luftfeuchte = luftfeuchte
    except:
        pass


    @classmethod
    def read_sensor_data(cls):
        i2c = busio.I2C(board.SCL, board.SDA)
        
        try:
            pct = adafruit_pct2075.PCT2075(i2c)
            innentemperatur = round(pct.temperature,1)

        except:
         with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Fehler 1", font = oled_font, fill = "white")        
            draw.text((5, 25), "Kabinensensor", font = oled_font, fill = "white")          
         Fehlerindikator(1)
         innentemperatur = 00.00
          
        try:
          umgebungslicht = adafruit_bh1750.BH1750(i2c)
          umgebungslicht = round(umgebungslicht.lux, 1)
        except:
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Fehler 2", font = oled_font, fill = "white")        
            draw.text((5, 25), "Umgebungslicht", font = oled_font, fill = "white")
            draw.text((5, 45), "-sensor", font = oled_font, fill = "white") 
          Fehlerindikator(2)
          umgebungslicht = 00.00

        try:
          calibration_params = bme280.load_calibration_params(bus, address)
          Außensensor = bme280.sample(bus, address, calibration_params)
          
          außentemperatur = round(Außensensor.temperature, 1)  # Placeholder for actual outside temperature reading
          luftdruck = round(Außensensor.pressure, 1)  # Placeholder for actual air pressure reading
          luftfeuchte = round(Außensensor.humidity, 1)  # Placeholder for actual humidity reading
  
        except:
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Fehler 9:", font = oled_font, fill = "white")        
            draw.text((5, 25), "Außensensor", font = oled_font, fill = "white")  
          Fehlerindikator(9)
          außentemperatur = 00.00
          luftdruck = 000.00
          luftfeuchte = 00.00
          
        return cls(innentemperatur, umgebungslicht, außentemperatur, luftdruck, luftfeuchte)
  

def lese_Koordinaten():
    global lat, lng, breitengrad, längengrad
    with open(koordinaten_file_path, "r") as json_file:
            coordinates_data = json.load(json_file)
            latitude = coordinates_data.get("latitude")
            longitude = coordinates_data.get("longitude")

    breitengrad = latitude
    längengrad = longitude
  

    with open(Halbkugel_pfad, "r") as json_file:
            sphere_data = json.load(json_file)
            pol = sphere_data.get("Pol")
            block = sphere_data.get("Block")

        
    if pol == "Nord":
                pol =""
    elif pol == "Sued":
                pol ="-"
    else:
        print("Hemisphäre Nord/Süd nicht angegeben. Kontrolliere Lepmon/Einstellungen/Hemisphere.json: Pol muss entweder Nord oder Sued sein")
        
    if block == "Ost":
                block =""
    elif block == "West":
                block ="-"
    else:
        print("Hemisphäre Ost/West nicht angegeben. Kontrolliere Lepmon/Einstellungen/Hemisphere.json: Block muss entweder Ost oder West sein")
        
    lat = f"{pol}{latitude}"
    lng = f"{block}{longitude}"
      
    return lat, lng, breitengrad, längengrad

#################################################################################################################
################################################# Hauptprogramm #################################################
#################################################################################################################
### Verzeichnisse
koordinaten_file_path = os.path.join(current_folder,"Lepmon_Einstellungen", "Koordinaten.json")
erw_einstellungen_pfad = os.path.join(current_folder,"Lepmon_Einstellungen", "Fallenmodus.json")
Kamera_Einstellungen = os.path.join(current_folder,"Lepmon_Einstellungen", "Kamera_Einstellungen.xml")
Halbkugel_pfad = os.path.join(current_folder,"Lepmon_Einstellungen", "Hemisphere.json")
zielverzeichnis = None
get_usb_path()

### Variablen
Blitz_PMW = 350 # Modulation für LED im Optofet
dimmer_pin = 13 # Visible LED
#VIS_LED = LED(13) # An und Aus ohne Dimmer
Kamera_Strom = LED(5)
LepiLed_pin = 26 

aktueller_nachtordner = None
Kamera_Fehlerserie = 0
LepiLed_pwm = None
LepiLed_pwm_active = False
LUX = None
nacht_beginn_zeit = None
nacht_ende_zeit = None
pwm = None
vorhandene_Koordinaten = None

################### Koordinaten und Hemispheren aus dem Speicher lesen, um diese Einzustellen bei Fallenwartung#####
# Koordinaten
lese_Koordinaten()
gelesen_lat = lat
gelesen_lng = lng

### Knöpfe
Rechts = 8
PIN_EINGABE = 7
PIN_HOCH = 23
PIN_RUNTER = 24

### GPIO
GPIO.setmode(GPIO.BCM) # Initialisierung der GPIO und PWM außerhalb der Schleife
GPIO.setup(dimmer_pin, GPIO.OUT)
GPIO.setup(LepiLed_pin, GPIO.OUT)
GPIO.setup(Rechts, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_EINGABE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_HOCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_RUNTER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
pwm = GPIO.PWM(dimmer_pin, Blitz_PMW)
LepiLed_pwm = GPIO.PWM(LepiLed_pin, Blitz_PMW)

#################################################################################################################
################################################## Einstellungen ################################################
#################################################################################################################

### erweiterte Einstellungen
#Lepmoncode
codeverzeichnis = ""
with open(os.path.join(current_folder, "Lepmon_Einstellungen/LepmonCode.json")) as f:
    data = json.load(f)

projekt_name = data["projekt_name"]
sensor_id = data["sensor_id"]
bundesland = data["bundesland"]
stadt_code = data["stadtcode"]

# Fallenmodus
Fallen_Setup = json_einlesen(erw_einstellungen_pfad)  
Blitz_Änderung_zeit = float(Fallen_Setup["Erweiterte_Einstellungen"]["Blitzaenderungszeit"])
Dämmerungspuffer = int(Fallen_Setup["Erweiterte_Einstellungen"]["Daemmerungspuffer"])
Dämmerungspuffer = timedelta(minutes=Dämmerungspuffer)
Dämmerungsschwellenwert = int(Fallen_Setup["Erweiterte_Einstellungen"]["Daemmerung"])# Luxwert, unter dem von Dämmerung ausgegangen wird
Intervall = int(Fallen_Setup["Erweiterte_Einstellungen"]["Intervall_zwischen_Photos"]) # Intervall zwischen 2 Aufnahmen in Minuten
Kamera = str(Fallen_Setup["Erweiterte_Einstellungen"]["Kameratyp"])
utc_timezone = pytz.utc

Kontinuität = Fallen_Setup["Fang_mit_Pause"]
if Kontinuität:
    UV_anlocken = int(Fallen_Setup["Anlockphase"])
    UV_freilassen = int(Fallen_Setup["Pause"])
    uv_an_zähler = 0
    uv_an_dauer = Intervall/Intervall*UV_anlocken
    uv_aus_zähler = 0
    uv_aus_dauer = Intervall/Intervall*UV_freilassen 
    
    
### Einstellungen via Oled
time.sleep(1)
GUI_pin.on()
with canvas(oled) as draw:
  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
  draw.text((5, 5), "Menü öffnen:", font = oled_font, fill = "white")        
  draw.text((5, 25), "Bitte rechte Taste", font = oled_font, fill = "white")
  draw.text((5, 45), "drücken", font = oled_font, fill = "white")   

    # 20 Sekunden lang auf Tastendruck warten
for _ in range(2): #200
    if GPIO.input(PIN_EINGABE) is not GPIO.HIGH:
        GUI_pin.off()
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "Eingabe Menü", font = oled_font, fill = "white")
          draw.text((45,5),"x", font = oled_font, fill = "white")
        Fokus_neu = False  

        #time.sleep(5)
        
        #########
        for _ in range(100):
            if GPIO.input(Rechts) is not GPIO.HIGH:
                fokusieren()
                Kamera_Strom.off()
                break
            time.sleep(0.05)    
        
        pwm.start(0)
        # Test auf USB Stick
        check_usb_connection(zielverzeichnis)
     
# Anzeige der internen Uhrzeit - Interaktion vom Nutzer Nötig, um diese neu zu stellen
        for i in range(5):
            
            Zeit_aktualisieren()
            #current_time = datetime.now().strftime("%H:%M:%S")
    
            with canvas(oled) as draw:
              draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
              draw.text((5, 5), "aktuelle Uhrzeit", font = oled_font, fill = "white")        
              draw.text((5, 25), lokale_Zeit, font = oled_font, fill = "white")
            i = i+1  
            time.sleep(1)
            
        GUI_pin.on()
        with canvas(oled) as draw:
              draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
              draw.text((5, 5), "Uhrzeit mit ", font = oled_font, fill = "white")        
              draw.text((5, 25), "rechter Taste", font = oled_font, fill = "white")
              draw.text((5, 45), "neu stellen", font = oled_font, fill = "white")      

        Uhrzeit_neu = False
        for _ in range(40): 
            if GPIO.input(PIN_EINGABE) is not GPIO.HIGH:
                GUI_pin.off()
                with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                  draw.text((5, 5), "Zeit und Datum", font = oled_font, fill = "white") 
                  draw.text((5, 25), "eingeben", font = oled_font, fill = "white")           
                time.sleep(1)
                Uhrzeit_neu = True
                Uhrzeit_stellen()
            time.sleep(0.1)    
        if not Uhrzeit_neu:
            Zeit_aktualisieren()
            log_schreiben(f"{lokale_Zeit}; Eingabe Menü vom Benutzer geöffnet")
            log_schreiben(f"{lokale_Zeit}; Uhrzeit vom Benutzer unverändert")
            
        GUI_pin.off()
        if Fokus_neu:
          log_schreiben(f"{lokale_Zeit}; Falle vom Nutzer neu fokusiert")
        
        with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                  draw.text((5, 5), "Koordinaten", font = oled_font, fill = "white") 
                  draw.text((5, 25), f"Lat: {lat}", font = oled_font, fill = "white")
                  draw.text((5, 45), f"Long: {lng}", font = oled_font, fill = "white")
        time.sleep(5)
        Koordinaten_neu = False

        GUI_pin.on()
        with canvas(oled) as draw:
              draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
              draw.text((5, 5), "Koordinaten mit ", font = oled_font, fill = "white")        
              draw.text((5, 25), "rechter Taste", font = oled_font, fill = "white")
              draw.text((5, 45), "neu stellen", font = oled_font, fill = "white")
              
        for _ in range(40):  
            if GPIO.input(PIN_EINGABE) is not GPIO.HIGH:
                GUI_pin.off()
                with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                  draw.text((5, 5), "Koordinaten", font = oled_font, fill = "white") 
                  draw.text((5, 25), "eingeben", font = oled_font, fill = "white")           
                time.sleep(1)
                Koordinaten_neu = True
                
                with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                  draw.text((5, 5), "Bitte Halbkugeln ", font = oled_font, fill = "white") 
                  draw.text((5, 25), "eingeben", font = oled_font, fill = "white")                 
                time.sleep(3)
                with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                  draw.text((5, 5), "Knopf oben = Nord", font = oled_font, fill = "white") 
                  draw.text((5, 25), "Knopf unten = Süd", font = oled_font, fill = "white")
                
                user = False
                nordsüd =""
                while not user:
                    GUI_pin.on()
                    if GPIO.input(PIN_HOCH) ==GPIO.LOW:
                        pol = ""
                        nordsüd = "Nord"
                        user = True
                        GUI_pin.off()
                    elif GPIO.input(PIN_RUNTER) ==GPIO.LOW:
                        pol = "-"
                        nordsüd = "Sued"
                        user = True
                        GUI_pin.off()
                    else:
                         time.sleep(0.1)
                         
                with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                  draw.text((5, 5), "Knopf oben = Ost", font = oled_font, fill = "white") 
                  draw.text((5, 25), "Knopf unten = West", font = oled_font, fill = "white")
                
                user = False
                ostwest = ""
                while not user:
                    GUI_pin.on()
                    if GPIO.input(PIN_HOCH) ==GPIO.LOW:
                        block = ""
                        ostwest = "Ost"
                        user = True
                        GUI_pin.off()
                    elif GPIO.input(PIN_RUNTER) ==GPIO.LOW:
                        block = "-"
                        ostwest = "West"
                        user = True
                        GUI_pin.off()
                    else:
                         time.sleep(0.1)         
                spheren_pfad = os.path.join(current_folder,"Lepmon_Einstellungen", "Hemisphere.json")
                Hemisphere = {
                "Pol": nordsüd,
                "Block": ostwest
                }
                with open(spheren_pfad, "w") as json_datei:
                  json.dump(Hemisphere, json_datei, indent=4)         
                                
                eingabe_gps_koordinaten()
                with canvas(oled) as draw:
                  draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
        
                Koordinaten_pfad = os.path.join(current_folder,"Lepmon_Einstellungen", "Koordinaten.json")
                koordinaten = {
                "latitude": Breite,
                "longitude": Länge
                }
                with open(Koordinaten_pfad, "w") as json_datei:
                  json.dump(koordinaten, json_datei, indent=4)
         
                with canvas(oled) as draw:
                    draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
                    draw.text((5, 5), "GPS Koordinaten", font = oled_font, fill = "white") 
                    draw.text((5, 25), "gespeichert", font = oled_font, fill = "white") 
                time.sleep(2)
        
            time.sleep(0.1)  
        GUI_pin.off()
        if not Koordinaten_neu:
            Zeit_aktualisieren()
            log_schreiben(f"{lokale_Zeit}; Geografische Breite unverändert")
            log_schreiben(f"{lokale_Zeit}; Geografische Länge unverändert")
  
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "Testlauf starten", font = oled_font, fill = "white") 
        time.sleep(2)  
        sensor_data = SensorData.read_sensor_data()
        
        try:
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Innentemperatur", font = oled_font, fill = "white") 
            draw.text((5, 25), "{} C".format(sensor_data.innentemperatur), font = oled_font, fill = "white") 
          time.sleep(3)     
        except:  
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Fehler 1", font = oled_font, fill = "white") 
            draw.text((5, 25), "Innensensor", font = oled_font, fill = "white") 
                   
          Fehlerindikator(1)
          time.sleep(3)
         
        try:
          
         with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Umgebungslicht", font = oled_font, fill = "white") 
            draw.text((5, 25), "{} Lux".format(sensor_data.umgebungslicht), font = oled_font, fill = "white") 
         time.sleep(3)
        
        except:
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Fehler 2", font = oled_font, fill = "white") 
            draw.text((5, 25), "Lichtsensor", font = oled_font, fill = "white") 
                  

          Fehlerindikator(2)
          
        try:
         with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Aussentemperatur", font = oled_font, fill = "white") 
            draw.text((5, 25), "{} C".format(sensor_data.außentemperatur), font = oled_font, fill = "white")           
         time.sleep(3)
         
         with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Luftdruck", font = oled_font, fill = "white") 
            draw.text((5, 25), "{} hPa".format(sensor_data.luftdruck), font = oled_font, fill = "white")           
         time.sleep(3)      
         
         with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Luftfeuchte", font = oled_font, fill = "white") 
            draw.text((5, 25), "{} %".format(sensor_data.luftfeuchte), font = oled_font, fill = "white")           
         time.sleep(3)           
         
        except:
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Fehler 9:", font = oled_font, fill = "white") 
            draw.text((5, 25), "Außensensor", font = oled_font, fill = "white")    
          Fehlerindikator(9)
        
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "Kamera Test", font = oled_font, fill = "white")
        Kamera_Strom.on()
        time.sleep(1)
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "Kamera Test", font = oled_font, fill = "white") 
          draw.text((5, 25), "initialisieren...", font = oled_font, fill = "white")  
        time.sleep(8)
        
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "Kamera Test", font = oled_font, fill = "white") 
          draw.text((5, 25), "Aufnahme", font = oled_font, fill = "white")
          
        LepiLed_pwm.start(0)
        for duty_cycle in range(0, 99, 1):
          LepiLed_pwm.ChangeDutyCycle(duty_cycle)
          time.sleep(Blitz_Änderung_zeit / 100)
          LepiLed_pwm.ChangeDutyCycle(100)  
        
        try:
###########################
          dateiname = f"{projekt_name}{sensor_id}-{bundesland}-{stadt_code}__test.jpg" 
          #print(dateiname)
          lokaler_dateipfad = os.path.join(zielverzeichnis, dateiname)
          if Kamera == "Allied Vision Alvium":
      # Vimba zum aufnehmen
            with Vimba.get_instance() as vimba:
              cams = vimba.get_all_cameras()
              with cams[0] as cam:
                  try:
                    cam.set_pixel_format(PixelFormat.Bgr8)
                    cam.load_settings(Kamera_Einstellungen, PersistType.All)
                    dim_up(Blitz_Änderung_zeit)
                    frame = cam.get_frame(timeout_ms=864000000).as_opencv_image()
                    dim_down(Blitz_Änderung_zeit)
                    cv2.imwrite(lokaler_dateipfad, frame)
                  except Exception as e:
                    print("Exception:", e)
                    pass
                  
          elif Kamera == "Arducam Hawkeye":
            Aufnahme = 'libcamera-still -t 5000 -n -o'  + str(lokaler_dateipfad)
            log_schreiben(Aufnahme)
            try:
              os.system(Aufnahme)
              log_schreiben(f"Bild gespeichert: {dateiname}")
            except Exception as e:
              log_schreiben("Error:", e)
              pass
###########################          
          
          LepiLed_pwm.start(100)
          for duty_cycle in range(99, 0, -1):
            LepiLed_pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(Blitz_Änderung_zeit / 100)
            LepiLed_pwm.ChangeDutyCycle(0)
          
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Kamera Test", font = oled_font, fill = "white") 
            draw.text((5, 25), "erfolgeich beendet", font = oled_font, fill = "white")  
        
          
          time.sleep(3)
        except Exception as ex:
          dim_down(Blitz_Änderung_zeit)
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Fehler 5", font = oled_font, fill = "white") 
            draw.text((5, 25), "Kamera", font = oled_font, fill = "white")
            draw.text((5, 45), "Falle neu starten", font = oled_font, fill = "white") 
          print("Error:", ex)          
          Fehlerindikator(5)
          sys.exit(4)
        Kamera_Strom.off()
        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
        try:
          löschbefehl = str(lokaler_dateipfad)
          time.sleep(2)
          os.remove(löschbefehl)
          #print("gelöscht")
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Speicherzugriff", font = oled_font, fill = "white") 
            draw.text((5, 25), "erfolgreich", font = oled_font, fill = "white")            
          time.sleep(3)
        except:
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Fehler 4: USB", font = oled_font, fill = "white") 
            draw.text((5, 25), "nicht gefunden", font = oled_font, fill = "white")
            draw.text((5, 45), "Falle neu starten", font = oled_font, fill = "white")
          Fehlerindikator(4)
          time.sleep(4)
          sys.exit(4)
          
        Fallen_Setup = json_einlesen(erw_einstellungen_pfad)
        #Zeitzone = Fallen_Setup["Erweiterte_Einstellungen"]["Zeitzone"]
        #Zeitzone = pytz.timezone(Zeitzone)
        Start_Datum = datetime.now()
        lese_Koordinaten()
        get_twilight_times(lat, lng, Start_Datum)
        
        with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Abenddämmerung", font = oled_font, fill = "white") 
            draw.text((5, 25), Abenddämmerung_short, font = oled_font, fill = "white")
        
        time.sleep(3)
        with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Morgendämmerung", font = oled_font, fill = "white") 
            draw.text((5, 25), Morgendämmerung_short, font = oled_font, fill = "white")
        time.sleep(3)
        
        try:
         total_space_gb, used_space_gb, free_space_gb, used_percent, free_percent = get_disk_space(zielverzeichnis)
         with canvas(oled) as draw:
             
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Speicher gesamt:", font = oled_font, fill = "white") 
            draw.text((5, 25), "{:.1f} GB".format(total_space_gb, used_percent), font = oled_font, fill = "white")
         time.sleep(5)
         
         with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Speicher belegt:", font = oled_font, fill = "white") 
            draw.text((5, 25), "{:.1f} GB {:.1f} %".format(used_space_gb, used_percent), font = oled_font, fill = "white")
         time.sleep(5)
        
         with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Speicher frei:", font = oled_font, fill = "white") 
            draw.text((5, 25), "{:.1f} GB {:.1f} %".format(free_space_gb, free_percent), font = oled_font, fill = "white")
         time.sleep(5)
        except:
          
          with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
            draw.text((5, 5), "Fehler 4: USB", font = oled_font, fill = "white") 
            draw.text((5, 25), "nicht gefunden", font = oled_font, fill = "white")
            draw.text((5, 45), "Falle neu starten", font = oled_font, fill = "white")          
          time.sleep(4)
          sys.exit(4)

        with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "Testlauf beendet", font = oled_font, fill = "white") 
          draw.text((5, 25), "Bitte Deckel", font = oled_font, fill = "white")
          draw.text((5, 45), "schließen", font = oled_font, fill = "white")
          
        time.sleep(5)         
          
        break
        
    time.sleep(0.1)  
    
else:
        GUI_pin.off()
        Zeit_aktualisieren()
        try:
            log_schreiben(f"{lokale_Zeit}; 20 Sekunden sind vergangen, ohne dass der Taster gedrückt wurde.")
        except:
            pass
#################### Koordinaten und Hemispheren neu aus dem Speicher lesen, um Einstellungen zu erfassen

lese_Koordinaten()
############
sensor_data = {} # Leere dictionary für Messwerte

#################################################################################################################
################################################# Hauptprogramm #################################################
#################################################################################################################
Zeit_aktualisieren()
Start_Datum = datetime.now()

with canvas(oled) as draw:
            draw.rectangle(oled.bounding_box, outline = "black", fill = "black")
log_schreiben(f"{lokale_Zeit}; {Start_Datum.strftime('%Y-%m-%d')}")
log_schreiben(f"{lokale_Zeit}; Geografische Breite: {lng}")
log_schreiben(f"{lokale_Zeit}; Geografische Länge:  {lat}")
get_twilight_times(lat, lng, Start_Datum)
log_schreiben(f"{lokale_Zeit}; Zeitzone: {Zeitzone}")
log_schreiben(f"{lokale_Zeit}; berechneter Beginn Abenddämmerung: {Abenddämmerung_formatted}")
log_schreiben(f"{lokale_Zeit}; berechnetes Ende Morgendämmerung:  {Morgendämmerung_formatted}")
log_schreiben(f"{lokale_Zeit}; Puffer für Dämmerung: {Dämmerungspuffer}")


total_space_gb, used_space_gb, free_space_gb, used_percent, free_percent = get_disk_space(zielverzeichnis)

if total_space_gb is not None:
    log_schreiben(f"{lokale_Zeit}; Gesamter Speicherplatz: {total_space_gb:.2f} GB")
    log_schreiben(f"{lokale_Zeit}; Belegter Speicherplatz: {used_space_gb:.2f} GB ({used_percent:.2f}%)")
    log_schreiben(f"{lokale_Zeit}; Freier Speicherplatz:   {free_space_gb:.2f} GB ({free_percent:.2f}%)")
    
    speicher_message =f"Lepmon#{sensor_id} Freier Speicher: {free_space_gb:.2f} GB ({free_percent:.2f}%)"
    try:
        uart.write(speicher_message.encode('utf-8') + b'\n') 
    except:
        print("Lora Message nicht gesendet")
else:
    log_schreiben(f"{lokale_Zeit}; Zielverzeichnis konnte nicht ausglesen werden: verfügbarer Speicher unbekannt.")

#copy Kamera Einstellungen
try:
    xml_pfad = os.path.join(aktueller_nachtordner, 'Kamera_Einstellungen.xml')
    shutil.copy(os.path.join(current_folder,"Lepmon_Einstellungen", "Kamera_Einstellungen.xml"),xml_pfad)
    checksum(xml_pfad, algorithm="md5")
    
except:
    pass
    
Luxwert_lesen()

control_pin.off()
if nacht_ende_zeit.time()<= jetzt_local.time() <nacht_beginn_zeit.time():
  jetzt_local = jetzt_local.replace(tzinfo=None)
  Schlaf_bis_beginn = (nacht_beginn_zeit - jetzt_local).total_seconds()
  Schlaf_Stunden = int(Schlaf_bis_beginn// 3600)
  Schlaf_rest = Schlaf_bis_beginn % 3600
  Schlaf_Minuten = int(Schlaf_rest // 60)
  Schlaf_Sekunden = int(Schlaf_rest % 60)
  Schlaf_Zeit = "{:02d}:{:02d}:{:02d}".format(Schlaf_Stunden, Schlaf_Minuten, Schlaf_Sekunden)
  log_schreiben(f"{lokale_Zeit}; Warte bis Nachtbeginn: {Schlaf_Zeit}")
  Tag_message =f"{sensor_id} Warte bis Nachtbeginn: {Schlaf_Zeit}"
  try:
        uart.write(Tag_message.encode('utf-8') + b'\n') 
  except:
        print("Lora Message nicht gesendet")

  try:
    countdown = datetime.strptime(Schlaf_Zeit, "%H:%M:%S")
  except Exception as e:
    print(e)
    countdown = datetime.strptime("00:00:00", "%H:%M:%S")

  #with canvas(oled) as draw:
  #        draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
  #        draw.text((5, 5), "Start in:", font = oled_font, fill = "white") 
  #        draw.text((5, 25), f"{countdown_str}", font = oled_font, fill = "white") 

  nWait = 0 # TODO 120
  
  for _ in range(nWait):
    countdown_str = countdown.strftime("%H:%M:%S")  # Konvertiere datetime-Objekt in formatierten String
    with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "white", fill = "black")
          draw.text((5, 5), "Start in:", font = oled_font, fill = "white") 
          draw.text((5, 25), f"{countdown_str}", font = oled_font, fill = "white")
          draw.bitmap((70,30),logo, fill = 1)
    countdown -= timedelta(seconds=1)
    time.sleep(1)

  with canvas(oled) as draw:
          draw.rectangle(oled.bounding_box, outline = "black", fill = "black")
  Schlaf_bis_beginn = Schlaf_bis_beginn-120
  Schlaf_bis_beginn = 0 # TODO
  time.sleep(Schlaf_bis_beginn)
  Zeit_aktualisieren()



Fang_started = False
if (LUX >= Dämmerungsschwellenwert and not nacht_ende_zeit.strftime("%H:%M:%S") <= jetzt_local.strftime("%H:%M:%S") < nacht_beginn_zeit.strftime("%H:%M:%S")):
      LepiLED_start()
      Start_message =f"Lepmon#{sensor_id} Beginne Aufnahme Schleife"
      try:
        uart.write(Start_message.encode('utf-8') + b'\n') 
      except:
        print("Lora Message nicht gesendet")
      
      Fang_started = True

naechste_volle_minute = jetzt_local.replace(second=0, microsecond=0) + timedelta(minutes=1) # Warte bis zur nächsten vollen Minute
try: # Überprüfe, ob die nächste Minute ungerade ist, und füge eine zusätzliche Minute hinzu, wenn erforderlich
  if naechste_volle_minute.minute % Intervall != 0:
      naechste_volle_minute += timedelta(minutes=1)  
except: 
  pass


#################################################################################################################
#################################################### Schleife ###################################################
#################################################################################################################
try:   
    while True:
        Zeit_aktualisieren()
        Luxwert_lesen()

        jetzt_local = jetzt_local.replace(tzinfo=None)
        if (LUX <= Dämmerungsschwellenwert and not nacht_ende_zeit.strftime("%H:%M:%S") <= jetzt_local.strftime("%H:%M:%S") < nacht_beginn_zeit.strftime("%H:%M:%S")) or\
           (LUX >  Dämmerungsschwellenwert and not Morgendämmerung.strftime("%H:%M:%S") <= jetzt_local.strftime("%H:%M:%S") < nacht_beginn_zeit.strftime("%H:%M:%S")) and Fang_started:
          if not Fang_started:
            LepiLED_start()
            Fang_started = True
            Start_message =f"Lepmon#{sensor_id} Beginne Aufnahme Schleife"
            try:
                uart.write(Start_message.encode('utf-8') + b'\n') 
            except:
                print("Lora Message nicht gesendet")
            
          bh = None
          if not Kontinuität: # kontinuierlicher Fang (Standard)
            Daten_erfassen()
            erstelle_und_aktualisiere_csv()
            Zeit_nächste_Aufnahme()
            
          # TODO: post data from update_sensor_data to ImSwitch and display
          
          elif Kontinuität: # Fangmodus für Tropen: mit Zeit in der die UV Lampe aus ist
              if not LepiLed_pwm_active: 
                if uv_aus_zähler <= uv_aus_dauer:
                  uv_aus_zähler +=1
                  Daten_erfassen()
                  erstelle_und_aktualisiere_csv()
                  Zeit_nächste_Aufnahme()
                  
                if uv_aus_zähler == uv_aus_dauer:
                  LepiLED_start()
                  erstelle_und_aktualisiere_csv()
                  uv_aus_zähler = 0
            
              if LepiLed_pwm_active: 
                if uv_an_zähler <= uv_an_dauer:
                  uv_an_zähler += 1
                  Daten_erfassen()
                  erstelle_und_aktualisiere_csv()
                  Zeit_nächste_Aufnahme()
                  
                if uv_an_zähler == uv_an_dauer:
                  LepiLED_ende()
                  erstelle_und_aktualisiere_csv()
                  uv_an_zähler = 0
        #elif (LUX >= Dämmerungsschwellenwert and Morgendämmerung.strftime("%H:%M:%S") < jetzt_local.strftime("%H:%M:%S") < nacht_beginn_zeit.strftime("%H:%M:%S")):
        elif (Morgendämmerung.strftime("%H:%M:%S") < jetzt_local.strftime("%H:%M:%S") < nacht_beginn_zeit.strftime("%H:%M:%S")):
          Ende()
        else:
          Zeit_nächste_Aufnahme()
                  
except KeyboardInterrupt: # Programm beenden, wenn Strg+C gedrückt wird
    log_schreiben(f"{lokale_Zeit}; Programm beendet.")
    pass

finally:
    # Aufräumarbeiten vor dem Beenden
    if pwm is not None:
        pwm.stop()
    GPIO.cleanup()
