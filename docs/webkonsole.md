# Auftrag 1: echte Web-Konsole und getrenntes Frontend

## Erweiterung ab Release 1.4.0: Gegner wählen

Auf Anwenderwunsch bietet das JAR vor jeder Partie ein Konsolenmenü:
**1 + Enter** wählt GreedyPlayer, **2 + Enter** den vorhandenen PerfectPlayer
mit Minimax. Danach die Feldnummern 0–8 eingeben. „Neues Spiel“ öffnet eine
neue Verbindung und damit eine neue Auswahl; andere Tabs bleiben unabhängig.
Ungültige Menüeingaben werden erneut abgefragt. Der PerfectPlayer spielt optimal
und kann bei korrekten Zügen beider Seiten höchstens ein Remis zulassen.

Die Spiellogik und die beiden Spieler-Algorithmen sind unverändert. Neu ist die
Auswahl in `main()` und ein gemeinsam verwendeter Scanner für Menü und Züge.
Das so gebaute Release-JAR wird weiterhin unverändert deployt. ttyd startet nur
das feste JAR; es gibt keine Shell und keine frei übergebenen URL-Kommandoargumente.

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

### Getestete Windows-Alternative: lokaler Linux-Container

Die native Windows-Version von ttyd/ConPTY kann beim Beenden des Java-Prozesses
die letzte Ausgabe abschneiden. Ein Python-Kindprozess als Puffer-Workaround
war in dieser Umgebung ebenfalls nicht zuverlässig und wurde nicht ausgeliefert.
Der vollständige Partietest wurde deshalb im lokalen Linux-Container bestanden.
Er verwendet dieselben Release-Assets und keinen Anwendungssourcecode.

Docker Desktop starten. In einem Ordner mit heruntergeladenem und geprüftem
Release 1.3.0 die Tools entpacken (`Expand-Archive ... tools`) und ausführen:

```powershell
$assets = (Get-Location).Path
docker run -d --name tictactest-local -p 127.0.0.1:8000:8080 -p 127.0.0.1:7681:7682 --mount "type=bind,source=$assets,target=/assets,readonly" eclipse-temurin:25-jdk-noble bash -c 'apt-get update -qq && apt-get install -y -qq python3 socat && cp /assets/tools/ttyd.x86_64 /tmp/ttyd && chmod +x /tmp/ttyd && (socat TCP-LISTEN:8080,fork,reuseaddr TCP:127.0.0.1:8000 &) && (socat TCP-LISTEN:7682,fork,reuseaddr TCP:127.0.0.1:7681 &) && python3 /assets/tools/local_run.py --jar /assets/tictactest-1.3.0.jar --frontend /assets/tictactest-frontend-1.3.0.zip --ttyd /tmp/ttyd'
docker logs tictactest-local
```

Nach Installation der Laufzeitpakete: <http://localhost:8000> öffnen. Die
Portweiterleitungen ändern nur die lokale Netzwerkkonfiguration; ttyd startet
weiterhin ausschliesslich das feste Java-JAR. Beenden: `docker stop tictactest-local`.

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
