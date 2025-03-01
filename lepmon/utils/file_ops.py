import os
import csv
import hashlib
import json
import shutil
import sys
import time

def read_coordinates_func(koordinaten_file_path, halbkugel_pfad):
    with open(koordinaten_file_path, "r") as json_file:
        coordinates_data = json.load(json_file)
        latitude = coordinates_data.get("latitude")
        longitude = coordinates_data.get("longitude")

    with open(halbkugel_pfad, "r") as json_file:
        sphere_data = json.load(json_file)
        pol = sphere_data.get("Pol")
        block = sphere_data.get("Block")

    if pol == "Nord":
        pol = ""
    elif pol == "Sued":
        pol = "-"
    else:
        raise ValueError("Hemisphäre Nord/Süd nicht angegeben. Kontrolliere Lepmon/Einstellungen/Hemisphere.json: Pol muss entweder Nord oder Sued sein")

    if block == "Ost":
        block = ""
    elif block == "West":
        block = "-"
    else:
        raise ValueError("Hemisphäre Ost/West nicht angegeben. Kontrolliere Lepmon/Einstellungen/Hemisphere.json: Block muss entweder Ost oder West sein")

    lat = f"{pol}{latitude}"
    lng = f"{block}{longitude}"
    hemisphere_data = {
        "latitude": latitude,
        "longitude": longitude,
        "pol": pol,
        "block": block
    }

    return lat, lng, hemisphere_data

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
        return None, None, None, None, None


def create_csv_file(path, headers):
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(headers)

def append_csv_row(path, data_dict):
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data_dict.keys(), delimiter="\t")
        writer.writerow(data_dict)

def calculate_checksum(filepath, algorithm="md5"):
    try:
        hash_func = hashlib.new(algorithm)
        with open(filepath, "rb") as file:
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception:
        return None

def copy_file_with_checksum(source, destination):
    shutil.copy(source, destination)
    chksum = calculate_checksum(destination)
    # write .md5 file, etc.
    return chksum


def check_usb_connection(path):
    try:
        if not os.path.exists(path):
            raise FileNotFoundError("USB device not found.")
        time.sleep(4)
        return True
    except:
        time.sleep(4)
        sys.exit(4)
        return False
    