# Auftrag 1: echte Web-Konsole und getrenntes Frontend

## Werkzeug und Sicherheit

Wir verwenden **ttyd 1.7.7** statt der zuerst entwickelten Python-HTTP-Brücke
unter `web/`. ttyd enthält xterm.js, überträgt Terminaldaten per WebSocket und
startet für jede Verbindung eine JVM in einem Pseudo-Terminal. Damit bleiben
ANSI-Farben, Tastatureingaben und die originale Konsolenoberfläche erhalten.
GoTTY ist eine Alternative; websocketd bietet nur Textzeilen und würde eine
eigene Terminaldarstellung benötigen. Die alte Python-Brücke ist nur ein
historischer Prototyp und nicht mehr der Cloud-Dienst.

`-W` erlaubt Eingaben (ohne diese Option ist ttyd schreibgeschützt), `-m 8`
begrenzt die Verbindungen und `-b /terminal` konfiguriert den Proxy-Pfad.
Gestartet wird ausschliesslich `java -Xmx48m -jar /opt/tictactest/app.jar`.
Insbesondere werden keine Shell, kein `login`, keine URL-Argumente und kein
Terminal-Zugriff auf das Betriebssystem angeboten. Eine Shell würde Besuchern
die Rechte des Dienstbenutzers geben, inklusive möglichem Datenabfluss.

Der Dienst läuft als `tictactest`, nicht als root, mit systemd-Härtung und
700 MB Gesamtlimit. Acht Heaps à 48 MB sind keine acht garantierten 48-MB-JVMs:
jede JVM benötigt zusätzlich native Speicherbereiche, Threads und Metadaten.
Die Grenze acht ist eine obere Schutzgrenze, keine garantierte Kapazität;
bei einem 1-GB-Server sind wenige gleichzeitige Spiele sinnvoll. Reale Last
muss gemessen werden; bei Speicherdruck beendet systemd Prozesse.

Nach Spielende oder ungültiger Eingabe beendet sich das Original-JAR. „Neues
Spiel“ lädt das eingebettete Terminal erneut und startet eine neue JVM. Zwei
offene, verbundene Terminal-Tabs starten zwei getrennte Java-Prozesse. Das
Schliessen einer Verbindung beendet ihren Prozess. Bei einem Backend-Neustart
verlieren aktive Partien ihren Zustand; Drain/Blue-Green mit Verbindungsabbau
wäre eine mögliche Verbesserung, wurde aber nicht umgesetzt.

## Nur aus Release-Assets lokal starten

Voraussetzungen: Python 3.9+ und Java 25. Kein Gradle-Build und kein Checkout nötig.
Die folgenden Dateien desselben Releases herunterladen:

- `tictactest-VERSION.jar` und dessen `.sha256`
- `tictactest-frontend-VERSION.zip` und dessen `.sha256`
- `tictactest-tools-VERSION.zip` und dessen `.sha256`

Die Tools enthalten den Starthelfer und die anhand der Hersteller-Prüfsummen
verifizierten ttyd-Binaries für Windows und Linux x86_64. Java wird als
vorinstallierte Laufzeit vorausgesetzt, nicht mit dem Frontend ausgeliefert.

PowerShell, Beispiel für 1.3.0 im Downloadordner:

```powershell
Get-ChildItem *.sha256 | ForEach-Object {
  $parts = (Get-Content $_.FullName) -split '\s+'
  if ((Get-FileHash $parts[1] -Algorithm SHA256).Hash.ToLower() -ne $parts[0]) { throw 'Checksum mismatch' }
}
Expand-Archive tictactest-tools-1.3.0.zip tools
python tools/local_run.py --jar tictactest-1.3.0.jar --frontend tictactest-frontend-1.3.0.zip --ttyd tools/ttyd.win32.exe
```

Linux/Devcontainer: `sha256sum -c *.sha256`, Tools entpacken und
`chmod +x tools/ttyd.x86_64`; anschliessend denselben Python-Aufruf mit
`--ttyd tools/ttyd.x86_64` verwenden.

Frontend: <http://localhost:8000>, Web-Konsole: <http://localhost:7681/terminal/>.
Es sind zwei getrennte Server. Der lokale Helfer erzeugt `/config.js` und liest
die Backend-Version aus `Implementation-Version` im **heruntergeladenen** JAR.
Mit Ctrl+C werden beide Server beendet. `--port` und `--console-port` erlauben
abweichende Ports, die Konfiguration wird automatisch angepasst.

## Versionen und Konfiguration

`frontend/` enthält plain HTML, CSS und JavaScript, keinen Build-Schritt.
`config.js` gehört ausschliesslich zur Umgebung, nie ins Frontend-ZIP.
In AWS schreibt die Infrastruktur `consoleUrl: '/terminal/'`; lokal schreibt
der Starthelfer eine localhost-URL und einen separaten Versions-Endpunkt.
Es gibt keine EC2-Adresse in `frontend/app.js`.

Die Seite zeigt zwei unabhängige Versionen:

- Backend: `/backend-version.json`, nach geprüftem Deployment aus Release-Tag
  und JAR-Manifest erzeugt; wird nur beim Backend-Deployment geändert.
- Frontend: `/version.json` aus dem Frontend-Release-ZIP; wird nur beim
  Frontend-Deployment geändert.

In AWS sind Frontend und Proxy same-origin. Für lokale, getrennte Origins
stellt der Starthelfer die Versionsinformation same-origin bereit. Der
Cloud-Versionsendpunkt erlaubt CORS (`Access-Control-Allow-Origin: *`), enthält
aber nur eine öffentliche Versionsnummer. Das Terminal ist per iframe eingebettet;
das Frontend greift nicht auf dessen DOM zu. Deshalb ist hierfür keine
Aufweichung der Same-Origin-Policy erforderlich.

Frontend-Assets als Release sichern nachvollziehbare, unveränderliche Rollbacks
und erlauben denselben Stand ohne Quellcode oder Build-Werkzeug auszuliefern.
Unit, nginx-Konfiguration und Cloud-Installer gehören zur Infrastruktur:
Änderungen daran erfordern einen lokalen IaC-Apply, nicht ein App-Deployment.

Quellen: [ttyd und Optionen](https://github.com/tsl0922/ttyd),
[ttyd 1.7.7 und SHA256SUMS](https://github.com/tsl0922/ttyd/releases/tag/1.7.7).
