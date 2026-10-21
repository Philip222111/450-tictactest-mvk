# Devcontainer: Build, Freigabe und automatische Übernahme

Diese Dokumentation beschreibt den vollständigen Prozess für das Image aus
`.devcontainer/Dockerfile`:

```text
ghcr.io/philip222111/450-tictactest-mvk-devcontainer
```

## Quellen und Verbraucher

- `.devcontainer/Dockerfile` definiert Java 25, Gradle und `vscode` mit
  UID:GID `1000:1000`.
- `.devcontainer/IMAGE_VERSION` ist die zentrale offizielle Image-Version.
- `.devcontainer/devcontainer.json` verwendet diesen unveränderlichen Tag in
  VS Code.
- `.github/workflows/ci.yml` verwendet denselben Tag für Gradle und JUnit.
- `.github/workflows/container.yml` baut, prüft, veröffentlicht und erzeugt den
  Versions-PR.
- `scripts/update_devcontainer_version.py` aktualisiert zentrale Version,
  `devcontainer.json` und alle YAML-Workflows mit diesem Image-Namen. Unit-Tests
  prüfen Vollständigkeit, Eingaben und Idempotenz.

`latest` und `stable` werden absichtlich nicht verwendet. So kann kein
beweglicher Tag ungeprüft in Entwicklung oder CI gelangen.

## Tags und SemVer

| Tag | Bedeutung | CI/VS Code |
|---|---|---|
| `sha-<40-stellige Commit-ID>` | Kandidat jedes `main`-Commits | niemals |
| `vMAJOR.MINOR.PATCH`, z. B. `v1.0.2` | offizielle Freigabe | ja |

MAJOR steht für inkompatible Änderungen, MINOR für kompatible neue
Werkzeuge/Funktionen und PATCH für kompatible Korrekturen. Eine Freigabe muss
numerisch größer als `.devcontainer/IMAGE_VERSION` sein. Bereits in GHCR
vorhandene SemVer-Tags werden nicht überschrieben. Die Anwendungsversion in
`VERSION` ist davon unabhängig.

## Jeder Push auf main

Der Job `candidate` läuft ohne Pfadfilter bei **jedem** Push auf `main`:

1. Checkout und Unit-Tests des Update-Skripts.
2. GHCR-Login mit dem kurzlebigen `GITHUB_TOKEN`.
3. Build von `.devcontainer/Dockerfile` für `linux/amd64` und Push als
   `sha-${GITHUB_SHA}`.
4. Pull anhand des Digests und Prüfung von Java, Gradle und UID/GID.

Das SHA-Image ist nicht offiziell freigegeben und wird nie von CI oder VS Code
referenziert. Auch der Merge des Versions-PRs erzeugt daher nur ein SHA-Image,
aber weder eine Freigabe noch einen neuen PR. Dies verhindert Endlosschleifen.
Die initiale Devcontainer-Konfiguration darf direkt auf `main` gepusht werden;
dieser Push durchläuft denselben Prozess.

## Offizielle Freigabe

Die Dockerfile-Änderung muss auf `main` liegen und ihr SHA-Build erfolgreich
sein. Beispiel für die nächste Version:

```sh
git switch main
git pull --ff-only
git status --short
git tag -a devcontainer-v1.0.2 -m "Devcontainer v1.0.2"
git push origin devcontainer-v1.0.2
gh release create devcontainer-v1.0.2 --verify-tag \
  --title "Devcontainer v1.0.2" \
  --notes "Offizielle Devcontainer-Freigabe v1.0.2"
```

Ohne GitHub CLI wird derselbe Tag unter **Releases → Draft a new release**
ausgewählt und veröffentlicht. Nur ein veröffentlichtes, nicht als Prerelease
markiertes Release im Format `devcontainer-vMAJOR.MINOR.PATCH` startet
`publish`. Der Tag-Commit muss zu `main` gehören. Der Workflow:

1. validiert Format, `main`-Zugehörigkeit und steigende Version;
2. lehnt die Wiederverwendung eines offiziellen Tags ab;
3. baut lokal und prüft Java 25, Gradle, UID:GID `1000:1000` und den
   vollständigen Gradle-/JUnit-Build;
4. pusht erst danach ausschließlich `vX.Y.Z`;
5. pullt und prüft das Image nochmals anhand seines Digests;
6. aktualisiert alle Verbraucher auf einem Branch und erstellt einen PR;
7. startet CI auf exakt diesem PR-Commit und wartet auf den Erfolg.

## Versions-PR, Duplikate und CI

Der Branch heißt `automation/devcontainer-vX.Y.Z`. Der PR aktualisiert immer:

```text
.devcontainer/IMAGE_VERSION
.devcontainer/devcontainer.json
.github/workflows/ci.yml
```

Weitere Workflows mit dem Image-Namen werden automatisch mitgenommen. Der
Workflow staged deshalb `.github/workflows/` vollständig. Ein bereits offener
PR desselben Branches wird aktualisiert statt dupliziert. Ist `main` schon auf
der Version, entstehen weder leerer Commit noch PR.

Ein mit `GITHUB_TOKEN` erzeugter PR löst nachfolgende Workflows möglicherweise
nicht automatisch aus. Deshalb besitzt nur `publish` die Berechtigung
`actions: write`, startet `ci.yml` explizit per `workflow_dispatch` auf dem
Versionsbranch, ermittelt den Lauf für den exakten Commit und wartet mit
`--exit-status`. Der normale `pull_request`-Trigger bleibt für andere PRs
aktiv. Ein CI-Fehler macht den Release-Workflow rot.

Nach Review und Merge beziehen Entwickler die Version und bauen neu:

```sh
git switch main
git pull --ff-only
```

Danach in VS Code **Dev Containers: Rebuild Container** ausführen. Nur ein
`git pull` lässt einen bereits laufenden Container noch auf dem alten Image.

## Einmalige GitHub-Konfiguration

Unter **Settings → Actions → General** müssen Workflow-Schreibrechte und
**Allow GitHub Actions to create and approve pull requests** aktiviert sein.
Der Workflow erstellt den PR, genehmigt ihn aber nicht. Das Repository muss in
den GHCR-Package-Einstellungen Zugriff auf das Package besitzen. Die Jobs
fordern nur gezielte `packages`, `contents`, `pull-requests` und `actions`
Berechtigungen an. Es wird kein PAT oder langlebiges Secret benötigt. Branch
Protection kann Review und den CI-Job als Pflichtprüfung verlangen.

## Lokale Tests

PowerShell im Repository:

```powershell
python -m unittest discover -s scripts -p 'test_*.py'
docker build --pull --file .devcontainer/Dockerfile --tag tictactest-devcontainer:test .
docker run --rm tictactest-devcontainer:test java -version
docker run --rm tictactest-devcontainer:test gradle --version
docker run --rm tictactest-devcontainer:test id
docker run --rm --user root --mount "type=bind,source=$PWD,target=/workspace" `
  --env "GRADLE_OPTS=-Dorg.gradle.java.installations.paths=/opt/java/openjdk" `
  --workdir /workspace tictactest-devcontainer:test `
  bash gradlew --no-daemon clean build
```

Erwartet werden Java Major 25, Gradle 9.7, `uid=1000(vscode)`,
`gid=1000(vscode)` und ein erfolgreicher JUnit-Build. Der Updater kann in einer
separaten Arbeitskopie manuell getestet werden:

```sh
python scripts/update_devcontainer_version.py v1.0.2
git diff -- .devcontainer .github/workflows
```

## GHCR- und Automationsnachweis

Push und PR benötigen echten GitHub-Zugang. Nach `main`-Push bzw. Release:

```sh
docker login ghcr.io
docker pull ghcr.io/philip222111/450-tictactest-mvk-devcontainer:sha-<COMMIT>
docker pull ghcr.io/philip222111/450-tictactest-mvk-devcontainer:v1.0.2
gh run list --workflow container.yml
gh pr list --head automation/devcontainer-v1.0.2 --state all
gh run list --workflow ci.yml --branch automation/devcontainer-v1.0.2
```

Im PR müssen zentrale Version, `devcontainer.json` und alle Workflow-Verbraucher
denselben SemVer-Tag enthalten. Nach dem Merge darf genau der `main`-SHA-Build
starten; ohne neues GitHub Release entsteht kein weiterer Versions-PR.

## Ausgeführter Nachweis (23. September 2026)

Lokal erfolgreich geprüft wurden der Docker-Build, Temurin Java `25.0.4`,
Gradle `9.7.0`, `uid=1000(vscode)`, `gid=1000(vscode)`, der vollständige
Gradle-Build mit 25 JUnit-Tests (0 Fehler) und JaCoCo, fünf Python-Unit-Tests,
`actionlint`, `git diff --check` sowie die konsistente Referenz `v1.0.1` in
zentraler Datei, VS-Code-Devcontainer und CI. Der lesende GHCR-Pull von
`v1.0.1` war erfolgreich (Digest
`sha256:838142a7788c7478c4716643fb8bc40f4f6deaa885d5319a8c18c6fcddd1c972`).

Nicht ausgeführt wurden ein neuer GHCR-Push, ein echtes GitHub Release, die
dadurch ausgelöste PR-Erstellung und dessen Merge: In der lokalen Umgebung ist
keine authentifizierte GitHub CLI vorhanden, und ein Testrelease würde
dauerhaften externen Zustand erzeugen. Diese Punkte werden beim ersten echten
Release mit den oben genannten Befehlen und Actions-Läufen verifiziert. Zuvor
müssen die einmaligen Repository- und Package-Berechtigungen gesetzt sein.

## Aktueller lokaler Nachweis (21. Oktober 2026)

Der neue Ubuntu-Noble-Dockerfile wurde erfolgreich als
`tictactest-devcontainer:local` gebaut. Nachgewiesen: Java 25.0.4.1, Gradle 9.7.0,
UID/GID 1000:1000 und ein frischer `clean build pitest` mit 112 Tests,
100 % Branch-Coverage und 79/79 erkannten Mutationen. Der vorhandene Benutzer
ubuntu wird in vscode umbenannt, da UID 1000 im Basisimage bereits existiert.

Die gepinnten GHCR-Verbraucher bleiben bis zum naechsten Container-Release auf
v1.0.1. Der lokale neue Dockerfile ist noch kein veroeffentlichtes GHCR-Image.
Aktueller Remote-Nachweis und Release-Links: ABGABE.md.
