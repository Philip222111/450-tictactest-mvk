# Docker-Zugriff aus dem VS-Code-Devcontainer

## Befund

Docker Desktop ist auf dem Windows-Rechner gestartet: Die vorliegende Ausgabe von `docker info` enthält Client und Server sowie den Kontext `desktop-linux`. Im VS-Code-Terminal unter `/workspaces/TicTacToeTest` meldet Bash dagegen `docker: command not found`. Dieser Fehler entsteht vor dem Image-Build; er ist kein Fehler des CI-Dockerfiles.

Im untersuchten Workspace enthält die übergeordnete Konfiguration `/workspaces/TicTacToeTest/.devcontainer/devcontainer.json` ursprünglich lediglich ein Alpine-Basisimage. Die separate Konfiguration im Unterordner `450-tictactest-mvk/.devcontainer` enthält die Java-Entwicklungsumgebung. Keine der beiden ursprünglichen Konfigurationen stellt den Docker-Client mit Zugriff auf den Host-Socket bereit.

## Konfigurationsänderung

Die übergeordnete Workspace-Konfiguration verwendet nun `mcr.microsoft.com/devcontainers/base:ubuntu-24.04` mit `ghcr.io/devcontainers/features/docker-outside-of-docker:1`. Dieses offizielle Feature installiert den Docker-Client einschliesslich Buildx und verbindet ihn mit dem Docker-Socket des Hosts. Ubuntu entspricht der dokumentierten Betriebssystemunterstützung des Features.[^1]

Die Änderung betrifft die Entwicklungsumgebung, nicht das zu veröffentlichende CI-Image. Die Konfiguration liegt ausserhalb des Git-Repositories `450-tictactest-mvk` und wird deshalb bei einem Commit dieses Repositories nicht mitgespeichert. Die dortige Java-Devcontainer-Konfiguration bleibt unverändert.

## Aktivierung und Prüfung

Docker Desktop muss laufen. In VS Code im geöffneten Workspace `TicTacToeTest` über die Befehlspalette **Dev Containers: Rebuild Container** ausführen. Änderungen an der Devcontainer-Konfiguration werden durch den Neuaufbau angewendet.[^2]

Im neu geöffneten Terminal prüfen:

```bash
docker version
docker info
docker buildx version
```

`docker info` muss Client- und Serverinformationen liefern. Fehlt weiterhin der Befehl, wurde die geänderte Konfiguration nicht angewendet. Ist nur der Client verfügbar, müssen Socket-Einbindung und Verbindung zum Docker-Host geprüft werden. Eine reine Client-Installation bestätigt noch keine Verbindung zum Docker-Daemon.

## Manueller Image-Build

Der Projektordner liegt eine Ebene unter dem Workspace. Deshalb vor dem Build ausdrücklich dorthin wechseln:

```bash
cd /workspaces/TicTacToeTest/450-tictactest-mvk
docker buildx build --platform linux/amd64 --load \
  -f .github/container/Dockerfile \
  -t ghcr.io/philip222111/450-tictactest-mvk:latest \
  .github/container
```

Der Build bleibt ein manueller Terminal-Aufruf. Upload und Package-Zugriff sind in [CONTAINER_GH_ACTIONS.md](CONTAINER_GH_ACTIONS.md) beschrieben. Der Neuaufbau der Entwicklungsumgebung führt weder diesen Image-Build noch einen GHCR-Upload automatisch aus.

## Grenzen der Verifikation

Am 9. September 2026 wurde der Docker-Zugriff aus dem Devcontainer bestätigt: `docker version` meldet Client und Docker-Desktop-Server. Der manuelle Image-Build und der Projekt-Build im CI-Container sind erfolgreich; alle 12 Tests bestehen. Der GHCR-Upload scheitert aktuell an fehlenden Schreibrechten (`denied`); siehe [CONTAINER_GH_ACTIONS.md](CONTAINER_GH_ACTIONS.md).

Bei späteren `docker run`-Befehlen mit Bind-Mounts gilt: Der externe Docker-Daemon interpretiert Quellpfade auf dem Host. Ein Containerpfad wie `/workspaces/...` lässt sich deshalb nicht ohne Weiteres als Hostpfad verwenden. Das Feature dokumentiert diese Einschränkung ausdrücklich.[^1] Der oben gezeigte Build überträgt seinen Build-Kontext und benötigt keinen solchen Workspace-Bind-Mount.

## Quellen

[^1]: Dev Containers, [Docker (docker-outside-of-docker)](https://github.com/devcontainers/features/tree/main/src/docker-outside-of-docker), laufende Dokumentation, abgerufen am 9. September 2026. Funktionsweise, Buildx, unterstützte Betriebssysteme und Bind-Mount-Einschränkungen.
[^2]: Microsoft, [Create a Dev Container](https://code.visualstudio.com/docs/devcontainers/create-dev-container), laufende Dokumentation, abgerufen am 9. September 2026. Devcontainer-Konfiguration und Neuaufbau.
