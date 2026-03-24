logo-cam
Automatische Kameraansicht-Steuerung per Siemens LOGO! SPS auf dem Raspberry Pi.
Das Skript liest einen Binärwert von einer Siemens LOGO! über das Netzwerk aus und schaltet daraufhin automatisch zwischen zwei Videostreams um, die per mpv im Vollbild angezeigt werden – z. B. für eine 25-Meter- und eine 50-Meter-Schießbahnansicht.

Funktionsweise
LOGO! SPS  ──(TCP/IP)──▶  Raspberry Pi  ──▶  mpv (Vollbild)
  V1104.0 = 1  →  Stream A (z. B. 25m)
  V1104.0 = 0  →  Stream B (z. B. 50m)

Der Pi verbindet sich per python-snap7 mit der LOGO!
Alle 1000 ms wird ein Bit ausgelesen
Bei Änderung wird der laufende Stream sofort gewechselt
Stürzt mpv ab, wird er automatisch neu gestartet
Verbindungsabbrüche zur SPS werden automatisch wiederhergestellt


Voraussetzungen
Hardware:

Raspberry Pi (getestet mit Raspberry Pi OS, labwc Desktop)
Siemens LOGO! SPS mit aktivierter Ethernet-Schnittstelle
Netzwerkverbindung zwischen Pi und LOGO!

Software:

Python 3.10+
mpv
python-snap7


Installation
1. Abhängigkeiten installieren
bashsudo apt-get update
sudo apt-get install -y mpv
pip3 install python-snap7 --break-system-packages
2. Repository klonen
bashgit clone https://github.com/DreDayyy92/logo-cam.git
cd logo-cam
3. Konfiguration anpassen
bashnano config.ini
4. Als systemd-Service einrichten (Autostart)
bash# Service-Datei kopieren
sudo cp logo_cam.service /etc/systemd/system/

# Aktivieren und starten
sudo systemctl daemon-reload
sudo systemctl enable logo_cam
sudo systemctl start logo_cam

Konfiguration (config.ini)
ini[LOGO]
ip     = 192.168.X.XXX   # IP-Adresse der LOGO! SPS
rack   = 0x0300          # Rack (Standardwert für LOGO!)
slot   = 0x0200          # Slot (Standardwert für LOGO!)
var    = V1104.0         # Zu lesende Variable (Bit-Adresse)

[PLAYER]
poll_interval   = 1      # Abfrageintervall in Sekunden
startup_delay   = 30     # Wartezeit beim Start (Netzwerk hochfahren lassen)
connect_retries = 5      # Verbindungsversuche bei Fehler

[STREAMS]
25m = https://...        # Stream-URL für Ansicht 1
50m = https://...        # Stream-URL für Ansicht 2

Die Stream-URLs können lokale Dateipfade, RTSP-Streams, HTTP-URLs oder alles sein, was mpv unterstützt.


Dateien
logo_cam.pyHauptskriptconfig.iniAlle Einstellungen (IP, Streams, Parameter)logo_cam.servicesystemd-Unit für den Autostartrequirements.txtPython-Abhängigkeiten

Betrieb
Status prüfen
bashsudo systemctl status logo_cam
Logs live ansehen
bashsudo journalctl -u logo_cam -f
Manuell stoppen / starten
bashsudo systemctl stop logo_cam
sudo systemctl start logo_cam
Manuell ausführen (zum Testen)
bashpython3 logo_cam.py
# Beenden mit Strg+C
Die Logdatei liegt unter ~/logo_monitor.log und wird automatisch rotiert (max. 1 MB × 4 Dateien).

Deployment auf mehrere Raspberry Pis
Wenn dasselbe Setup auf mehreren Geräten ausgerollt werden soll:
bash# SSH-Key einmalig auf jeden Pi kopieren
ssh-copy-id user@192.168.1.201

# Dateien übertragen und installieren
scp logo_cam.py config.ini logo_cam.service user@192.168.1.201:~/
ssh user@192.168.1.201 "
  sudo cp logo_cam.service /etc/systemd/system/ &&
  sudo systemctl daemon-reload &&
  sudo systemctl enable logo_cam &&
  sudo systemctl start logo_cam
"
Die config.ini kann pro Gerät vorab angepasst werden (z. B. unterschiedliche LOGO!-IPs oder Streams).

Troubleshooting
ProblemLösungsnap7 kann nicht verbunden werdenIP in config.ini prüfen, LOGO! Ethernet aktiviert?mpv startet nichtDISPLAY=:0 gesetzt? Desktop läuft?Service startet nichtjournalctl -u logo_cam -n 50 für DetailsFalscher Benutzer in .serviceUser= in logo_cam.service anpassen

Lizenz
MIT
