import os
import csv
import hashlib
import json
import shutil

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
