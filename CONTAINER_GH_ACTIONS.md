# Eigenes Container-Image für GitHub Actions

## 1. Aktueller Stand

Auf dem gepushten Branch `task/ghcr-container-ci` sind das CI-Dockerfile und die Verwendung von `ghcr.io/philip222111/450-tictactest-mvk:latest` im Workflow umgesetzt.

**Abgeschlossen am 9. September 2026:** Das CI-Image wurde manuell für `linux/amd64` gebaut, mit `latest` getaggt und erfolgreich nach GHCR hochgeladen. Der anschliessende authentifizierte `docker pull` war erfolgreich. Nach Vergabe der Package-Leserechte an das Repository ist auch der [Actions-Lauf](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/34343894748) erfolgreich: Container-Start, Checkout, Java-Prüfung, Build mit Tests und Upload der Testberichte.

Veröffentlichter und durch Pull bestätigter Digest: `sha256:698aac8baa7536a30fad89cf3f6288b74460a0b41bb15d31dc3e7fcefd3c2b1c`.

Alle folgenden Befehle werden in Bash auf einem Rechner mit laufendem Docker im Projektverzeichnis `450-tictactest-mvk` ausgeführt.

## 2. Container manuell bauen und taggen

Das [CI-Dockerfile](.github/container/Dockerfile) enthält Java 25 und Kommandozeilenwerkzeuge auf Ubuntu-Basis für die Ausführung der GitHub Actions. Gradle wird durch den Projekt-Wrapper geladen; der Quellcode kommt durch Checkout hinzu.

```bash
docker build --platform linux/amd64 \
  --file .github/container/Dockerfile \
  --tag tictactest-ci:latest \
  .github/container

docker tag tictactest-ci:latest ghcr.io/philip222111/450-tictactest-mvk:latest
```

`linux/amd64` entspricht dem verwendeten GitHub-Runner. Auf ARM-Rechnern benötigt Docker entsprechende Emulationsunterstützung.

Vor dem Upload den Projekt-Build samt Tests im Image ausführen. Die folgende Variante funktioniert auch mit einem externen Docker-Daemon im Devcontainer, weil die Dateien kopiert werden:

```bash
docker create --name tictactest-ci-check --platform linux/amd64 \
  ghcr.io/philip222111/450-tictactest-mvk:latest \
  bash -c 'bash gradlew --no-daemon -Dorg.gradle.java.installations.paths="$JAVA_HOME" build'
tar --exclude=.git --exclude=.gradle --exclude=build -cf - . \
  | docker cp - tictactest-ci-check:/workspace
docker start --attach tictactest-ci-check
docker inspect tictactest-ci-check --format '{{.State.ExitCode}}'
mkdir -p build/container-check
docker cp tictactest-ci-check:/workspace/build/reports build/container-check/
docker cp tictactest-ci-check:/workspace/build/test-results build/container-check/
docker rm tictactest-ci-check
```

Der Exit-Code muss `0` sein; die Berichte werden aus dem Container kopiert. Die vorhandene Gradle-Daemon-Konfiguration verlangt AZUL Java 25 und enthält Download-URLs dafür. Das Image liefert Temurin Java 25; Gradle kann deshalb die konfigurierte Daemon-JVM zusätzlich herunterladen. Die explizite Installationsangabe macht das Container-JDK trotz deaktivierter automatischer Erkennung für die Projekt-Toolchain verfügbar. Netzwerkzugriff für Gradle, JVM und Maven-Abhängigkeiten bleibt erforderlich.

## 3. Bei GHCR anmelden und Image hochladen

Für den manuellen Upload einen GitHub Personal Access Token **classic** mit `write:packages` verwenden. Den Token lokal verdeckt eingeben:

```bash
read -r -s -p 'GitHub PAT (classic): ' GHCR_PAT
printf '\n'
printf '%s' "$GHCR_PAT" | docker login ghcr.io --username Philip222111 --password-stdin
unset GHCR_PAT

docker push ghcr.io/philip222111/450-tictactest-mvk:latest
```

Das Dockerfile enthält das OCI-Source-Label für das Repository. Die Package-API meldete nach diesem Upload dennoch keine Repository-Verknüpfung. Deshalb in den Package-Einstellungen sicherstellen, dass `Philip222111/450-tictactest-mvk` unter **Manage Actions access** Leserechte besitzt. Eine öffentliche Freigabe ist für diesen Workflow nicht erforderlich.

Den Upload prüfen und den Digest als Nachweis festhalten:

```bash
docker pull ghcr.io/philip222111/450-tictactest-mvk:latest
docker image inspect ghcr.io/philip222111/450-tictactest-mvk:latest --format '{{json .RepoDigests}}'
docker logout ghcr.io
```

Authentifizierung, Source-Label und Package-Zugriff folgen der [GitHub-Anleitung zur Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## 4. Verwendung in GitHub Actions

Der [Workflow](.github/workflows/ci.yml) verwendet das GHCR-Image als Job-Container. Checkout, Java-Prüfung und `gradlew build` laufen darin; `setup-java` entfällt.

Zum Download verwendet der Job `github.actor` und den automatisch bereitgestellten `GITHUB_TOKEN` mit `packages: read`. `contents: read` erlaubt den Checkout. Ein eigenes PAT-Secret ist in CI bei eingerichtetem Package-Zugriff nicht notwendig. Grundlage ist die [GitHub-Dokumentation zu Job-Containern](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/run-jobs-in-a-container).

Push und Pull Request lösen den Workflow aus; zusätzlich ist ein manueller Start konfiguriert. Vorhandene Testberichte werden als Artefakt `test-results` hochgeladen. Der Workflow selbst baut und veröffentlicht kein Image.

**Reihenfolge:** Image bauen, testen und hochladen, Package-Zugriff prüfen, danach die vorbereiteten Git-Änderungen gemeinsam committen und den Branch pushen. Ohne verfügbares Image scheitert der Job bereits beim Container-Start.

## 5. Abgabenachweise

Nach der tatsächlichen Durchführung festhalten:

- Erfolgreicher manueller Image-Build und lokaler Build-/Testlauf.
- GHCR-Package mit Tag `latest` und ausgegebenem Digest.
- Erfolgreicher Actions-Lauf mit Download des eigenen Images und Projekt-Build.
- Testbericht aus dem Workflow-Artefakt.

Am 9. September 2026 bestätigt:

- Manueller Image-Build für `linux/amd64` mit Tag `latest` erfolgreich.
- Container-JDK: Temurin 25.0.4+7.
- Projekt-Build im Container: `BUILD SUCCESSFUL in 45s`, vier Tasks ausgeführt, Exit-Code `0`.
- Testergebnis: 12 Tests, 0 Fehler, 0 Fehlschläge, 0 übersprungen.
- Lokale Nachweise: `build/container-verification/build.log`, `build/container-verification/reports/tests/test/index.html` und XML-Berichte unter `build/container-verification/test-results/test/`.
- GHCR-Push und anschliessender Pull nach Anmeldung mit PAT (classic) erfolgreich; Digest siehe oben.
- [Veröffentlichtes Package](https://github.com/users/Philip222111/packages/container/package/450-tictactest-mvk), Tag `latest`.
- Branch mit Commit `9c3668c` gepusht.
- [Erster Actions-Lauf](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/34343409198): Download mit `GITHUB_TOKEN` wegen fehlendem Package-Zugriff abgelehnt; anschliessend unter **Manage Actions access** behoben.
- [Erfolgreicher Actions-Lauf](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/34343894748) für Commit `ad38f12`: alle Job-Schritte erfolgreich, einschliesslich GHCR-Download, Projekt-Build und Testbericht-Upload als `test-results`.
