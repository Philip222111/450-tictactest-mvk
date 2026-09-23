# TicTacTest

TicTacTest ist ein kleines Tic-Tac-Toe-Konsolenspiel in Java. Ein Mensch spielt
mit X gegen einen einfachen Computergegner, der jeweils das erste freie Feld
wählt. Das Repository dient zugleich als Beispiel für automatisierte Tests,
JaCoCo-Coverage, GitHub Actions, eine Coverage-Zeitreihe auf GitHub Pages und
eine reproduzierbare Devcontainer-Umgebung.

## Technischer Überblick

- Java 25
- Gradle 9.7 über den eingecheckten Gradle Wrapper
- JUnit Jupiter 6 und AssertJ
- JaCoCo 0.8.15
- GitHub Actions und GitHub Container Registry (GHCR)
- VS Code Dev Containers

Das Buildsystem ist **Gradle (Groovy DSL)**. Für lokale Befehle soll immer der
Wrapper `gradlew` beziehungsweise `gradlew.bat` verwendet werden; eine global
installierte Gradle-Version ist nicht erforderlich.

## Voraussetzungen und Installation

Für die lokale Entwicklung werden Git und ein JDK 25 benötigt. Gradle kann die
im Projekt konfigurierte Java-Toolchain bei Bedarf automatisch beziehen.

```sh
git clone https://github.com/Philip222111/450-tictactest-mvk.git
cd 450-tictactest-mvk
./gradlew build
```

Unter Windows PowerShell lautet der letzte Befehl:

```powershell
.\gradlew.bat build
```

Der Build lädt die Testabhängigkeiten aus Maven Central, kompiliert das Projekt,
führt alle Tests aus und erzeugt den JaCoCo-Bericht. Das Konsolenspiel kann mit
folgendem Befehl gestartet werden:

```sh
./gradlew classes
java -cp build/classes/java/main ch.bbw.m450.tictactoe.TicTacToeMain
```

## Tests und Coverage

```sh
./gradlew test
./gradlew jacocoTestReport
```

`test` erzeugt den Testbericht unter `build/reports/tests/test/index.html`.
Da der Test-Task mit `jacocoTestReport` verknüpft ist, entsteht zusätzlich der
HTML-Coverage-Bericht unter `build/reports/jacoco/test/html/index.html` und der
maschinenlesbare Bericht `build/reports/jacoco/test/jacocoTestReport.xml`.

Das vollständige [Testkonzept](TESTKONZEPT.md) beschreibt Ziele, Strategie,
Testfälle, parametrisierte Tests, Fixtures und Grenzen. Das Design der
[Coverage-Zeitreihe](COVERAGE.md) und die [Abgabe-Links](ABGABE.md) erläutern
die dauerhafte Erfassung auf GitHub Pages.

## CI und Coverage-Zeitreihe

Der Workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) läuft bei
Pushes (außer auf den Datenbranch `coverage-history`), Pull Requests und
manuellen Starts. Er baut im selben freigegebenen Java-25-Devcontainer-Image
wie die lokale Umgebung, führt den Gradle-Build aus und stellt Test- und
JaCoCo-Berichte als Artefakte bereit.

Nach einem erfolgreichen Push auf `main` ergänzt der zweite Job genau einen
Messpunkt pro Commit im separaten Branch `coverage-history` und veröffentlicht
Historie sowie aktuellen Detailbericht auf
[GitHub Pages](https://philip222111.github.io/450-tictactest-mvk/coverage-history/index.html).

## Devcontainer

Wer Docker Desktop und VS Code mit der Erweiterung **Dev Containers** verwendet,
kann den Repository-Ordner direkt mit **Dev Containers: Reopen in Container**
öffnen. Der Container enthält Java 25, Git, Bash und Gradle 9.7; beim ersten
Start führt `postCreateCommand` den vollständigen Build aus. Java- und
Gradle-Erweiterungen werden automatisch installiert.

Erstellung, lokale Prüfung, SemVer-Freigabe, GHCR-Push und automatische
Versions-PRs sind in
[DEVCONTAINER.md](DEVCONTAINER.md) dokumentiert.

## Weitere Dokumentation

- [Anwendungs-Releases, Download und Freigabeprozess](RELEASE.md)
- [Changelog](CHANGELOG.md)

- [Testkonzept](TESTKONZEPT.md)
- [Devcontainer](DEVCONTAINER.md)
- [Coverage-Zeitreihe](COVERAGE.md)
- [CI-Container und GHCR](CONTAINER_BUILD_WORKFLOW.md)
- [Abgabenachweise](ABGABE.md)
