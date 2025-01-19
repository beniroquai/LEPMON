import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import pytz
Aktivieren = '/home/Ento/Lepmon_skript/Start.sh'

def json_erstellen():
    # JSON-Daten erstellen
    daten = {
        "Fallenstandort": {
            "latitude": latitude_entry.get(),
            "longitude": longitude_entry.get()
        },
        "Fang_mit_Pause": fang_mit_pause_var.get(),
        "Anlockphase": anlockphase_combobox.get() if fang_mit_pause_var.get() else "",
        "Pause": pause_combobox.get() if fang_mit_pause_var.get() else "",
        "Erweiterte_Einstellungen": {
            "Daemmerungspuffer": daemmerungspuffer_combobox.get(),
            "Blitzaenderungszeit": blitzaenderungszeit_combobox.get(),
            "Zeitzone": zeitzone_combobox.get(),
            "Daemmerung": daemmerung_combobox.get(),
            "Kameratyp": kameratyp_combobox.get(),
            "Intervall_zwischen_Photos": intervall_photos_combobox.get()
        }
    }

    # JSON-Datei schreiben
    with open("Fallenmodus.json", 'w') as datei:
        json.dump(daten, datei, indent=2)

def Falle_starten():
  json_erstellen
  subprocess.run(['bash', '-c', f'. {Aktivieren}'], check=True)
  

# Funktion zum Aktualisieren der GUI abhängig vom Status von "Fang mit Pause"
def update_gui():
    anlockphase_label.grid(row=4, column=0, sticky="e") if fang_mit_pause_var.get() else anlockphase_label.grid_remove()
    anlockphase_combobox.grid(row=4, column=1) if fang_mit_pause_var.get() else anlockphase_combobox.grid_remove()
    anlockphase_infobox.grid(row=4, column=2) if fang_mit_pause_var.get() else anlockphase_infobox.grid_remove()
    
    pause_label.grid(row=5, column=0, sticky="e") if fang_mit_pause_var.get() else pause_label.grid_remove()
    pause_combobox.grid(row=5, column=1) if fang_mit_pause_var.get() else pause_combobox.grid_remove()
    pause_infobox.grid(row=5, column=2) if fang_mit_pause_var.get() else pause_infobox.grid_remove()

# Funktion zum Aktualisieren der GUI abhängig vom Status von "Erweiterte Einstellungen"
def update_advanced_settings():
    daemmerungspuffer_label.grid(row=8, column=0, sticky="e") if erweiterte_einstellungen_var.get() else daemmerungspuffer_label.grid_remove()
    daemmerungspuffer_combobox.grid(row=8, column=1) if erweiterte_einstellungen_var.get() else daemmerungspuffer_combobox.grid_remove()
    daemmerungspuffer_infobox.grid(row=8, column=2) if erweiterte_einstellungen_var.get() else daemmerungspuffer_infobox.grid_remove()
    
    blitzaenderungszeit_label.grid(row=9, column=0, sticky="e") if erweiterte_einstellungen_var.get() else blitzaenderungszeit_label.grid_remove()
    blitzaenderungszeit_combobox.grid(row=9, column=1) if erweiterte_einstellungen_var.get() else blitzaenderungszeit_combobox.grid_remove()
    blitzaenderungszeit_infobox.grid(row=9, column=2) if erweiterte_einstellungen_var.get() else blitzaenderungszeit_infobox.grid_remove()

    zeitzone_label.grid(row=10, column=0, sticky="e") if erweiterte_einstellungen_var.get() else zeitzone_label.grid_remove()
    zeitzone_combobox.grid(row=10, column=1) if erweiterte_einstellungen_var.get() else zeitzone_combobox.grid_remove()
    zeitzone_infobox.grid(row=10, column=2) if erweiterte_einstellungen_var.get() else zeitzone_infobox.grid_remove()

    daemmerung_label.grid(row=11, column=0, sticky="e") if erweiterte_einstellungen_var.get() else daemmerung_label.grid_remove()
    daemmerung_combobox.grid(row=11, column=1) if erweiterte_einstellungen_var.get() else daemmerung_combobox.grid_remove()
    daemmerung_infobox.grid(row=11, column=2) if erweiterte_einstellungen_var.get() else daemmerung_infobox.grid_remove()

    intervall_photos_label.grid(row=12, column=0, sticky="e") if erweiterte_einstellungen_var.get() else intervall_photos_label.grid_remove()
    intervall_photos_combobox.grid(row=12, column=1) if erweiterte_einstellungen_var.get() else intervall_photos_combobox.grid_remove()
    intervall_photos_infobox.grid(row=12, column=2) if erweiterte_einstellungen_var.get() else intervall_photos_infobox.grid_remove()

    kameratyp_label.grid(row=13, column=0, sticky="e") if erweiterte_einstellungen_var.get() else kameratyp_label.grid_remove()
    kameratyp_combobox.grid(row=13, column=1) if erweiterte_einstellungen_var.get() else kameratyp_combobox.grid_remove()
    kameratyp_infobox.grid(row=13, column=2) if erweiterte_einstellungen_var.get() else kameratyp_infobox.grid_remove()

# Funktion zum Laden von Zeitzone-Optionen im Format "Kontinent/Landeshauptstadt"
def load_timezone_options():
    timezones = [tz.replace("_", "/") for tz in pytz.all_timezones]
    zeitzone_combobox['values'] = timezones

# Funktion zum Anzeigen der Infobox mit Platzhaltertext
def show_infobox(placeholder_text):
    messagebox.showinfo("Info", placeholder_text)

# Funktion für den Funktionslosen Knopf "Auslesen Standortkoordinaten"
def dummy_function():
    # Setze die vordefinierten Werte für Breitengrad und Längengrad
    latitude_entry.delete(0, tk.END)
    latitude_entry.insert(0, "50.9271")

    longitude_entry.delete(0, tk.END)
    longitude_entry.insert(0, "11.5892")

# GUI erstellen
root = tk.Tk()
root.title("Parameter LEPMON Falle")

# Einheitliches Padding
padding = {'padx': 5, 'pady': 5}

# Labels und Entry Widgets für Daten
ttk.Label(root, text="Breitengrad:").grid(row=0, column=0, sticky="e", **padding)
latitude_entry = ttk.Entry(root)
latitude_entry.grid(row=0, column=1, **padding)

ttk.Label(root, text="Längengrad:").grid(row=1, column=0, sticky="e", **padding)
longitude_entry = ttk.Entry(root)
longitude_entry.grid(row=1, column=1, **padding)

# Rahmen für "Fang mit Pause" Optionen hinzufügen
frame_fang_mit_pause = ttk.Frame(root, borderwidth=2, relief="groove")
frame_fang_mit_pause.grid(row=2, column=0, columnspan=3, **padding)

ttk.Label(frame_fang_mit_pause, text="Fang in Unterbrechungen:").grid(row=0, column=0, sticky="e", **padding)
fang_mit_pause_var = tk.BooleanVar()
fang_mit_pause_checkbox = ttk.Checkbutton(frame_fang_mit_pause, variable=fang_mit_pause_var, command=update_gui)
fang_mit_pause_checkbox.grid(row=0, column=1, sticky="w", **padding)
fang_mit_pause_infobox = ttk.Label(frame_fang_mit_pause, text="i", cursor="question_arrow", foreground="blue")
fang_mit_pause_infobox.grid(row=0, column=2, **padding)
fang_mit_pause_infobox.bind("<Button-1>", lambda e: show_infobox("Optional für Fang in den Tropen. Die UV Lampe brennt während der Anlockphase und erlischt während der Unterbrechung, sodass Tiere die Chance haben, den Schirm zu verlassen"))

anlockphase_label = ttk.Label(frame_fang_mit_pause, text="Anlockphase [min] - UV Lampe an:")
anlockphase_options = [3,5, 10, 15, 20, 25, 30]
anlockphase_combobox = ttk.Combobox(frame_fang_mit_pause, values=anlockphase_options, state="readonly")
anlockphase_combobox.grid(row=4, column=1, **padding)
anlockphase_combobox.set(anlockphase_options[0])  # Vorauswahl
anlockphase_infobox = ttk.Label(frame_fang_mit_pause, text="i", cursor="question_arrow", foreground="blue")
anlockphase_infobox.grid(row=4, column=2, **padding)
anlockphase_infobox.bind("<Button-1>", lambda e: show_infobox("Brenndauer der UV LED in Minuten. Es werden Tiere angelockt"))

pause_label = ttk.Label(frame_fang_mit_pause, text="Unterbrechung [min] - UV Lampe aus:")
pause_options = [2, 5, 10, 15, 20, 25, 30] # 1 ist nicht möglich
pause_combobox = ttk.Combobox(frame_fang_mit_pause, values=pause_options, state="readonly")
pause_combobox.grid(row=5, column=1, **padding)
pause_combobox.set(pause_options[0])  # Vorauswahl
pause_infobox = ttk.Label(frame_fang_mit_pause, text="i", cursor="question_arrow", foreground="blue")
pause_infobox.grid(row=5, column=2, **padding)
pause_infobox.bind("<Button-1>", lambda e: show_infobox("UV LED ist in dieser Zeit aus. Tiere haben die Chance, den Schirm zu verlassen"))

# Rahmen für erweiterte Einstellungen hinzufügen
frame_advanced_settings = ttk.Frame(root, borderwidth=2, relief="groove")
frame_advanced_settings.grid(row=3, column=0, columnspan=3, **padding)

erweiterte_einstellungen_var = tk.BooleanVar()
erweiterte_einstellungen_checkbox = ttk.Checkbutton(frame_advanced_settings, text="Erweiterte Einstellungen",
                                                     variable=erweiterte_einstellungen_var, command=update_advanced_settings)
erweiterte_einstellungen_checkbox.grid(row=0, column=0, **padding)

daemmerungspuffer_label = ttk.Label(frame_advanced_settings, text="Dämmerungspuffer [min]:")
daemmerungspuffer_options = [0,15,30,45,600]
daemmerungspuffer_combobox = ttk.Combobox(frame_advanced_settings, values=daemmerungspuffer_options, state="readonly")
daemmerungspuffer_combobox.grid(row=8, column=1, **padding)
daemmerungspuffer_combobox.set(daemmerungspuffer_options[4])  # Vorauswahl
daemmerungspuffer_infobox = ttk.Label(frame_advanced_settings, text="i", cursor="question_arrow", foreground="blue")
daemmerungspuffer_infobox.grid(row=8, column=2, **padding)
daemmerungspuffer_infobox.bind("<Button-1>", lambda e: show_infobox("Zeitraum in Minuten vor der Abenddämmerung und nach der Morgendämmerung. In dieser Zeit ist die Falle aktiv und misst das Umgebungslicht"))

blitzaenderungszeit_label = ttk.Label(frame_advanced_settings, text="Dimmdauer für Beleuchtung [s]:")
blitzaenderungszeit_options = [1,2,2.5,4,5]
blitzaenderungszeit_combobox = ttk.Combobox(frame_advanced_settings, values=blitzaenderungszeit_options, state="readonly")
blitzaenderungszeit_combobox.grid(row=9, column=1, **padding)
blitzaenderungszeit_combobox.set(blitzaenderungszeit_options[2])  # Vorauswahl
blitzaenderungszeit_infobox = ttk.Label(frame_advanced_settings, text="i", cursor="question_arrow", foreground="blue")
blitzaenderungszeit_infobox.grid(row=9, column=2, **padding)
blitzaenderungszeit_infobox.bind("<Button-1>", lambda e: show_infobox("Zeit in Sekunden, in der die Beleuchtung dimmt"))

zeitzone_label = ttk.Label(frame_advanced_settings, text="Zeitzone:")
zeitzone_combobox = ttk.Combobox(frame_advanced_settings, state="readonly")
load_timezone_options()  # Lade Zeitzone-Optionen beim Start
zeitzone_combobox.grid(row=10, column=1, **padding)
zeitzone_combobox.set("Europe/Berlin")  # Setze Standard-Zeitzone
zeitzone_infobox = ttk.Label(frame_advanced_settings, text="i", cursor="question_arrow", foreground="blue")
zeitzone_infobox.grid(row=10, column=2, **padding)
zeitzone_infobox.bind("<Button-1>", lambda e: show_infobox("lokale Zeitzone einstellen"))

daemmerung_label = ttk.Label(frame_advanced_settings, text="Dämmerungsschwellenwert [Lux]:")
daemmerung_options = [30,60,90,150,300]
daemmerung_combobox = ttk.Combobox(frame_advanced_settings, values=daemmerung_options, state="readonly")
daemmerung_combobox.grid(row=11, column=1, **padding)
daemmerung_combobox.set(daemmerung_options[2])  # Vorauswahl
daemmerung_infobox = ttk.Label(frame_advanced_settings, text="i", cursor="question_arrow", foreground="blue")
daemmerung_infobox.grid(row=11, column=2, **padding)
daemmerung_infobox.bind("<Button-1>", lambda e: show_infobox("Wert des Umgebungslichtes in LUX. Sobald das Umgebungslicht unter diesen Wert sinkt ,wird Dämmerung bzw. Nacht angenommen und die Falle nimmt Photos auf"))

intervall_photos_label = ttk.Label(frame_advanced_settings, text="Intervall zwischen Photos [min]:")
intervall_photos_options = [1, 2, 3, 4, 5, 6]
intervall_photos_combobox = ttk.Combobox(frame_advanced_settings, values=intervall_photos_options, state="readonly")
intervall_photos_combobox.grid(row=12, column=1, **padding)
intervall_photos_combobox.set(intervall_photos_options[0])  # Vorauswahl
intervall_photos_infobox = ttk.Label(frame_advanced_settings, text="i", cursor="question_arrow", foreground="blue")
intervall_photos_infobox.grid(row=12, column=2, **padding)
intervall_photos_infobox.bind("<Button-1>", lambda e: show_infobox("Aufnahme Intervall in Minuten zwischen 2 Bildern"))

kameratyp_label = ttk.Label(frame_advanced_settings, text="Kameratyp:")
kameratyp_options = ["Allied Vision Alvium", "Arducam Hawkeye"]
kameratyp_combobox = ttk.Combobox(frame_advanced_settings, values=kameratyp_options, state="readonly")
kameratyp_combobox.grid(row=13, column=1, **padding)
kameratyp_combobox.set(kameratyp_options[0])  # Vorauswahl
kameratyp_infobox = ttk.Label(frame_advanced_settings, text="i", cursor="question_arrow", foreground="blue")
kameratyp_infobox.grid(row=13, column=2, **padding)
kameratyp_infobox.bind("<Button-1>", lambda e: show_infobox("Verwendete Kamera. Die große Falle verwendet eine Allied Vision Kamera, die kleine Falle eine Arducam"))

# Knopf "Auslesen Standortkoordinaten" hinzufügen
standort_knopf = ttk.Button(root, text="Auslesen Standort", command=dummy_function)
standort_knopf.grid(row=0, column=2, **padding)

# Info-Label neben Knopf "Auslesen Standortkoordinaten" hinzufügen
standort_infobox = ttk.Label(root, text="i", cursor="question_arrow", foreground="blue")
standort_infobox.grid(row=0, column=3, **padding)
standort_infobox.bind("<Button-1>", lambda e: show_infobox("Auslesen der GPS Koordinaten des Smartphones. Diese werden als Fallenstandort gespeichert"))

# Initialisieren der GUI abhängig vom Status von "Fang mit Pause" und "Erweiterte Einstellungen"
update_gui()
update_advanced_settings()

# Button zum Erstellen der JSON-Datei (jetzt am Ende platziert)
erstellen_button = ttk.Button(root, text="Parameter speichern", command=json_erstellen)
erstellen_button.grid(row=4, column=0, columnspan=3, pady=10)

# Button zum Erstellen der JSON-Datei und starten der Falle
erstellen_button = ttk.Button(root, text="Parameter speichern und Falle starten", command=Falle_starten)
erstellen_button.grid(row=5, column=0, columnspan=3, pady=10)
root.mainloop()
