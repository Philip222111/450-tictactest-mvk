# Devcontainer

## Zweck und Aufbau

Die Konfiguration unter `.devcontainer/` stellt dieselbe Hauptumgebung wie das
Projekt bereit:

- Eclipse Temurin JDK 25 auf Alpine Linux,
- Gradle 9.7 und zusätzlich den projektspezifischen Gradle Wrapper,
- Bash, Git, OpenSSH, Curl und Unzip,
- unprivilegierter Benutzer `vscode`,
- persistenter Gradle-Cache als Docker-Volume,
- VS-Code-Erweiterungen für Java und Gradle.

`postCreateCommand` macht den Wrapper ausführbar und führt `./gradlew --no-daemon
build` aus. Damit wird beim Erstellen geprüft, dass Kompilierung, Tests und
JaCoCo-Bericht in der Umgebung funktionieren.

## Verwendung mit VS Code

Voraussetzungen sind Docker Desktop (oder eine kompatible Docker Engine), VS
Code und die Erweiterung **Dev Containers**.

1. Genau den Repository-Ordner `450-tictactest-mvk` in VS Code öffnen.
2. In der Befehlspalette **Dev Containers: Reopen in Container** auswählen.
3. Den Image-Build und anschließend den `postCreateCommand` abwarten.
4. Im Container-Terminal `java -version` und `./gradlew build` ausführen.

Nach Änderungen am Dockerfile oder an `devcontainer.json` wird **Dev Containers:
Rebuild Container** verwendet.

## Manueller Build und Funktionstest

Vom Repository-Wurzelverzeichnis aus:

```sh
docker build -f .devcontainer/Dockerfile -t tictactest-devcontainer:local .
docker run --rm tictactest-devcontainer:local java -version
```

Ein vollständiger Test mit eingebundenem Quellcode ist in PowerShell möglich:

```powershell
docker run --rm `
  -v "${PWD}:/workspaces/450-tictactest-mvk" `
  -w /workspaces/450-tictactest-mvk `
  tictactest-devcontainer:local `
  ./gradlew --no-daemon build
```

## Was bedeutet „Devcontainer pushen“?

Es gibt zwei getrennte Vorgänge:

1. **Konfiguration pushen:** `.devcontainer/devcontainer.json` und das Dockerfile
   werden normal mit Git committet und in das Repository gepusht. Das genügt,
   damit andere Personen den Devcontainer lokal reproduzieren können.
2. **Vorgebautes Image pushen:** Der Workflow `.github/workflows/container.yml`
   baut zusätzlich dasselbe Dockerfile und veröffentlicht die Tags
   `ghcr.io/philip222111/450-tictactest-mvk-devcontainer:latest` und
   `...:sha-<commit>` in GHCR. Das ist ein optionaler, vorgebauter Nachweis; die
   eingecheckte Konfiguration bleibt die maßgebliche Definition.

Der Workflow läuft manuell sowie bei Änderungen an `.devcontainer/`, am
CI-Dockerfile oder am Workflow selbst. Er verwendet ausschließlich das von
GitHub Actions bereitgestellte `GITHUB_TOKEN` mit `packages: write`. Es werden
keine persönlichen Tokens oder Zugangsdaten im Repository gespeichert. Ob das
Package öffentlich sichtbar ist und ob andere Repositories darauf zugreifen
dürfen, wird in den GitHub-Package-Einstellungen festgelegt.

Daneben veröffentlicht derselbe Workflow das separate CI-Image
`ghcr.io/philip222111/450-tictactest-mvk`. Dieses glibc-basierte Image ist für
GitHub Actions optimiert und nicht mit dem interaktiven Alpine-Devcontainer zu
verwechseln.
