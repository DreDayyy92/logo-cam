import snap7
import subprocess
import time
import os
import logging
import sys
import configparser
from logging.handlers import RotatingFileHandler

# --- LOGGING (muss zuerst kommen!) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            os.path.expanduser("~/logo_monitor.log"),
            maxBytes=1_000_000,   # 1 MB pro Datei
            backupCount=3,        # max. 3 alte Dateien behalten
        ),
    ],
)
log = logging.getLogger(__name__)

# --- KONFIG LADEN ---
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), "config.ini")
if not config.read(config_path):
    log.critical("config.ini nicht gefunden unter %s", config_path)
    sys.exit(1)

# --- EINSTELLUNGEN ---
LOGO_IP         = config["LOGO"]["ip"]
LOGO_RACK       = int(config["LOGO"]["rack"], 16)
LOGO_SLOT       = int(config["LOGO"]["slot"], 16)
PLC_VAR         = config["LOGO"]["var"]

POLL_INTERVAL   = config.getfloat("PLAYER", "poll_interval")
STARTUP_DELAY   = config.getint("PLAYER",  "startup_delay")
CONNECT_RETRIES = config.getint("PLAYER",  "connect_retries")

STREAMS = {
    "25m": config["STREAMS"]["25m"],
    "50m": config["STREAMS"]["50m"],
}

MPV_CMD = [
    "/usr/bin/mpv",
    "--fullscreen",
    "--no-border",
    "--ontop",
    "--loop",
    "--really-quiet",
]

os.environ.setdefault("DISPLAY", ":0")
os.environ.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")


# ---------------------------------------------------------------------------
# PLC-Wrapper
# ---------------------------------------------------------------------------
class LogoClient:
    """Kapselt die snap7-Verbindung mit automatischem Reconnect."""

    def __init__(self, ip: str, rack: int, slot: int):
        self.ip   = ip
        self.rack = rack
        self.slot = slot
        self._plc = snap7.logo.Logo()

    # -- Verbindung ----------------------------------------------------------
    def connect(self) -> bool:
        for attempt in range(1, CONNECT_RETRIES + 1):
            try:
                self._plc.connect(self.ip, self.rack, self.slot)
                log.info("Verbunden mit LOGO! %s", self.ip)
                return True
            except Exception as exc:
                log.warning("Verbindungsversuch %d/%d fehlgeschlagen: %s",
                            attempt, CONNECT_RETRIES, exc)
                time.sleep(2)
        return False

    def disconnect(self) -> None:
        try:
            self._plc.disconnect()
        except Exception:
            pass

    # -- Lesen ---------------------------------------------------------------
    def read_bit(self, var: str) -> bool | None:
        """Gibt True/False zurück, oder None bei Fehler."""
        if not self._plc.get_connected():
            log.warning("Nicht verbunden – Reconnect …")
            if not self.connect():
                return None

        try:
            return bool(self._plc.read(var))
        except Exception as exc:
            log.error("Lesefehler (%s): %s – trenne Verbindung", var, exc)
            self.disconnect()
            return None


# ---------------------------------------------------------------------------
# Player-Wrapper
# ---------------------------------------------------------------------------
class PlayerManager:
    """Startet/stoppt mpv und erkennt, wenn der Prozess ungewollt endet."""

    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self.current_view: str | None       = None

    def _kill_existing(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        subprocess.run(["pkill", "-9", "mpv"], capture_output=True)
        self._proc = None
        time.sleep(0.5)

    def play(self, name: str) -> None:
        url = STREAMS[name]
        log.info("Starte Player: %s → %s", name, url)
        self._kill_existing()
        try:
            self._proc = subprocess.Popen([*MPV_CMD, url])
            self.current_view = name
            log.info("Player gestartet (PID %d)", self._proc.pid)
        except Exception as exc:
            log.error("Player-Start fehlgeschlagen: %s", exc)
            self._proc        = None
            self.current_view = None

    def is_alive(self) -> bool:
        """True, wenn ein Prozess läuft."""
        return self._proc is not None and self._proc.poll() is None

    def ensure_running(self) -> None:
        """Startet den aktuellen Stream neu, falls mpv abgestürzt ist."""
        if self.current_view and not self.is_alive():
            log.warning("Player tot – starte '%s' neu …", self.current_view)
            self.play(self.current_view)

    def stop(self) -> None:
        self._kill_existing()
        self.current_view = None


# ---------------------------------------------------------------------------
# Hauptschleife
# ---------------------------------------------------------------------------
def main() -> None:
    log.info("Warte %d s auf Netzwerk und LOGO …", STARTUP_DELAY)
    time.sleep(STARTUP_DELAY)

    plc    = LogoClient(LOGO_IP, LOGO_RACK, LOGO_SLOT)
    player = PlayerManager()

    if not plc.connect():
        log.critical("Kann LOGO! nicht erreichen – Abbruch.")
        sys.exit(1)

    log.info("Überwachung läuft auf %s …", LOGO_IP)

    try:
        while True:
            # 1) Sicherstellen, dass mpv noch lebt
            player.ensure_running()

            # 2) SPS lesen
            status = plc.read_bit(PLC_VAR)

            log.debug("LOGO=%s | view=%s | alive=%s",
                      status, player.current_view, player.is_alive())

            # 3) Ansicht wechseln, falls nötig
            if status is True  and player.current_view != "25m":
                player.play("25m")
            elif status is False and player.current_view != "50m":
                player.play("50m")
            # status is None → Verbindungsfehler, nächste Iteration versucht Reconnect

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        log.info("Abbruch durch Benutzer.")
    finally:
        player.stop()
        plc.disconnect()


if __name__ == "__main__":
    main()