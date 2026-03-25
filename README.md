# logo-cam

Automatische Kameraansicht-Steuerung per Siemens LOGO! SPS auf dem Raspberry Pi.

Das Skript liest einen Binärwert von einer Siemens LOGO! über das Netzwerk aus und schaltet daraufhin automatisch zwischen zwei Videostreams um, die per `mpv` im Vollbild angezeigt werden – z. B. für eine 25-Meter- und eine 50-Meter-Schießbahnansicht.

---

## Funktionsweise

```
LOGO! SPS  ──(TCP/IP)──▶  Raspberry Pi  ──▶  mpv (Vollbild)
  V1104.0 = 1  →  Stream A (z. B. 25m)
  V1104.0 = 0  →  Stream B (z. B. 50m)
```

- Der Pi verbindet sich per `python-snap7` mit der LOGO!
- Alle 500 ms wird ein Bit ausgelesen
- Bei Änderung wird der laufende Stream sofort gewechselt
- Stürzt `mpv` ab, wird er automatisch neu gestartet
- Verbindungsabbrüche zur SPS werden automatisch wiederhergestellt
- Logs werden automatisch rotiert (max. 4 MB)

---

## Voraussetzungen

**Hardware:**
- Raspberry Pi (getestet mit Raspberry Pi OS, labwc Desktop)
- Siemens LOGO! SPS mit aktivierter Ethernet-Schnittstelle
- Netzwerkverbindung zwischen Pi und LOGO!

**Software:**
- Python 3.10+
- mpv
- python-snap7

---

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/DreDayyy92/logo-cam.git
cd logo-cam
```

### 2. Konfiguration anpassen

```bash
nano config.ini
```

Mindestens die IP-Adresse der LOGO! und die Stream-URLs eintragen – alles andere kann auf den Standardwerten bleiben.

### 3. Installationsskript ausführen

```bash
sudo bash install.sh
```

Das Skript installiert automatisch alle Abhängigkeiten, richtet den systemd-Service mit den korrekten Pfaden ein und startet ihn. Es erkennt dabei selbstständig den aktuellen Benutzer und sein Home-Verzeichnis – der Service funktioniert so auf jedem Raspberry Pi ohne manuelle Pfadanpassung.

---

## Konfiguration (`config.ini`)

```ini
[LOGO]
ip     = 192.168.1.200   # IP-Adresse der LOGO! SPS
rack   = 0x0300          # Rack (Standardwert für LOGO!)
slot   = 0x0200          # Slot (Standardwert für LOGO!)
var    = V1104.0         # Zu lesende Variable (Bit-Adresse)

[PLAYER]
poll_interval   = 1      # Abfrageintervall in Sekunden
startup_delay   = 30     # Wartezeit beim Start (Netzwerk hochfahren lassen)
connect_retries = 5      # Verbindungsversuche bei Fehler

[STREAMS]
25m = https://...        # Stream-URL für Ansicht 1 (Bit = 1)
50m = https://...        # Stream-URL für Ansicht 2 (Bit = 0)
```

> Die Stream-URLs können lokale Dateipfade, RTSP-Streams, HTTP-URLs oder alles sein, was `mpv` unterstützt.

---

## Dateien

| Datei | Beschreibung |
|---|---|
| `logo_cam.py` | Hauptskript |
| `config.ini` | Alle Einstellungen – IP, Streams, Parameter |
| `logo_cam.service` | systemd-Vorlage (wird von `install.sh` automatisch befüllt) |
| `install.sh` | Installationsskript – richtet alles automatisch ein |
| `requirements.txt` | Python-Abhängigkeiten |

---

## Betrieb

### Status prüfen
```bash
sudo systemctl status logo_cam
```

### Logs live ansehen
```bash
sudo journalctl -u logo_cam -f
```

### Stoppen / Starten / Neustarten
```bash
sudo systemctl stop logo_cam
sudo systemctl start logo_cam
sudo systemctl restart logo_cam
```

### Manuell ausführen (zum Testen)
```bash
python3 logo_cam.py
# Beenden mit Strg+C
```

Die Logdatei liegt unter `~/logo_monitor.log` und wird automatisch rotiert (max. 1 MB × 4 Dateien).

---

## Deployment auf mehrere Raspberry Pis

Wenn dasselbe Setup auf mehreren Geräten ausgerollt werden soll:

```bash
# SSH-Key einmalig auf jeden Pi kopieren
ssh-copy-id user@192.168.1.201

# Dateien übertragen und Installationsskript ausführen
scp -r logo-cam/ user@192.168.1.201:~/
ssh user@192.168.1.201 "sudo bash ~/logo-cam/install.sh"
```

Die `config.ini` kann pro Gerät vorab angepasst werden (z. B. unterschiedliche LOGO!-IPs oder Streams).

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| Service startet nicht | `journalctl -u logo_cam -n 50` für Details |
| LOGO! nicht erreichbar | IP in `config.ini` prüfen, Ethernet an der LOGO! aktiviert? |
| `mpv` startet nicht | Desktop läuft? `DISPLAY=:0` korrekt gesetzt? |
| Stream lädt nicht | URL in `config.ini` direkt mit `mpv <url>` testen |
| Falscher Benutzer | `install.sh` immer mit `sudo bash install.sh` ausführen, nicht als root |
