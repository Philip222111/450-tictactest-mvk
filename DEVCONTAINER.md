# Devcontainer

## Entwicklungsumgebung

Die Definition unter `.devcontainer/` stellt für lokale Entwicklung und CI
dieselbe Umgebung bereit:

- Eclipse Temurin JDK 25 auf Alpine Linux,
- Gradle 9.7 sowie den projektspezifischen Gradle Wrapper,
- JUnit Jupiter 6 als Gradle-Testabhängigkeit,
- Benutzer `vscode` mit UID und GID `1000:1000`,
- Bash, Git, OpenSSH, Curl und Unzip,
- VS-Code-Erweiterungen für Java und Gradle.

Der `postCreateCommand` führt `./gradlew --no-daemon build` aus. Dadurch
werden Kompilierung, Tests und JaCoCo-Bericht beim Erstellen der lokalen
Umgebung geprüft.

## Verwendung in VS Code

Voraussetzungen sind Docker Desktop, VS Code und die Erweiterung
**Dev Containers**.

1. Das Repository in VS Code öffnen.
2. **Dev Containers: Reopen in Container** ausführen.
3. Image-Download und `postCreateCommand` abwarten.
4. Im Container mit `java -version`, `gradle --version` und
   `./gradlew build` prüfen.

Nach der Freigabe einer neuen Version aktualisiert ein automatischer Pull
Request das Feld `image` in `.devcontainer/devcontainer.json`. Nach dem
Merge lädt **Dev Containers: Rebuild Container** die neue Version.

## Lokaler Build der Container-Definition

Das veröffentlichte Image wird ausschließlich aus dem eingecheckten Dockerfile
gebaut. Änderungen können vor einer Freigabe lokal geprüft werden:

```sh
docker build -f .devcontainer/Dockerfile -t tictactest-devcontainer:local .
docker run --rm tictactest-devcontainer:local java -version
docker run --rm tictactest-devcontainer:local gradle --version
```

Vollständiger Projekttest in PowerShell:

```powershell
docker run --rm --user root `
  -v "${PWD}:/workspace" `
  -w /workspace `
  tictactest-devcontainer:local `
  ./gradlew --no-daemon build
```

## Push, Versionierung und Freigabe

„Devcontainer pushen“ umfasst zwei getrennte Vorgänge:

1. Dockerfile und `devcontainer.json` werden wie normaler Quellcode per Git
   gepusht.
2. Ein freigegebenes Image wird in die GitHub Container Registry gepusht.

Devcontainer-Versionen verwenden Semantic Versioning:

- **Patch** (`v1.0.1`): Fehlerkorrekturen ohne Änderung der vorgesehenen
  Werkzeuge,
- **Minor** (`v1.1.0`): neue kompatible Werkzeuge oder Erweiterungen,
- **Major** (`v2.0.0`): inkompatible Änderungen, etwa ein neues Basissystem.

Ein Image gilt nur dann als freigegeben, wenn ein GitHub-Release mit einem Tag
der Form `devcontainer-vX.Y.Z` veröffentlicht wurde. Der Release-Commit muss
Bestandteil von `main` sein. Branch-Pushes und Pull Requests bauen das
Dockerfile lediglich zur Validierung und erhalten keine Registry-Tags.

Bei einer Freigabe veröffentlicht GitHub Actions vier Tags:

```text
ghcr.io/philip222111/450-tictactest-mvk-devcontainer:vX.Y.Z
ghcr.io/philip222111/450-tictactest-mvk-devcontainer:stable
ghcr.io/philip222111/450-tictactest-mvk-devcontainer:latest
ghcr.io/philip222111/450-tictactest-mvk-devcontainer:sha-<commit>
```

`vX.Y.Z` und `sha-...` sind unveränderliche Referenzen. `stable` und
`latest` werden ausschließlich bei einer offiziellen Freigabe verschoben.
Nach dem Upload und einem Java-/Gradle-Funktionstest erstellt der Workflow
automatisch einen Pull Request. Dieser setzt Devcontainer und CI gemeinsam auf
den unveränderlichen SemVer-Tag. Damit nutzen beide nach geprüftem Merge die
neueste freigegebene Version, ohne ungeprüfte Images zu übernehmen.

Für Build und Push wird nur das kurzlebige `GITHUB_TOKEN` mit
`packages: write` verwendet. Es werden keine Zugangsdaten eingecheckt.
Damit der automatische PR erstellt werden kann, muss unter
**Settings → Actions → General → Workflow permissions** die Option
**Allow GitHub Actions to create and approve pull requests** aktiviert sein.

Der technische Ablauf steht in
[CONTAINER_BUILD_WORKFLOW.md](CONTAINER_BUILD_WORKFLOW.md).
