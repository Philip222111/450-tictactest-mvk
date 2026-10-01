# Release-Prozess für TicTacTest

Eine Anwendungsversion wird bewusst durch einen annotierten Tag `vMAJOR.MINOR.PATCH`
freigegeben. Ein Push auf main führt weiterhin die CI aus, erstellt aber keinen
Anwendungsrelease. Container verwenden unabhängig davon `devcontainer-v...`.

## Version und Voraussetzungen

`VERSION` ist die einzige Quelle für die Anwendungsversionsnummer. Gradle
übernimmt sie in Dateiname und Manifest. Der Workflow verlangt exakt denselben
Wert im Git-Tag. SemVer beginnt hier mit 1.0.0:

- MAJOR: inkompatible Bedienung oder Schnittstellen.
- MINOR: neue kompatible Funktionen, beispielsweise ein zusätzlicher Spielmodus.
- PATCH: kompatible Fehlerkorrekturen oder korrigierte Benutzertexte.

Ein Release wird erstellt, sobald ein getesteter, bewusst freigegebener Stand
auf `main` vorliegt. Die releaseverantwortliche Person legt die Version fest und
startet die Automatisierung durch den Tag-Push. Normale Pushes auf `main` starten
keinen Release, weil unfertige Zwischenstände nicht versehentlich veröffentlicht
werden dürfen.

Vor der Freigabe müssen alle vorgesehenen Änderungen auf `main` liegen, der
Working Tree sauber, Tests und Build erfolgreich und VERSION sowie CHANGELOG.md
konsistent sein. Der geplante Tag darf weder lokal noch auf GitHub existieren.
Das Changelog beschreibt pro Version Datum, neue Funktionen (Added), Änderungen
(Changed) und Fehlerkorrekturen (Fixed) in verständlicher Sprache, nicht als
Commitliste.

## Durchführung

Voraussetzungen: Git, Java 25, Python 3 für den JAR-Starttest und Push-Rechte.
Der Release-Verantwortliche führt nach dem geprüften Merge aus:

```sh
git switch main
git pull --ff-only
git branch --show-current
git status --short
git log -1 --oneline
git tag --list v1.0.1
git ls-remote --exit-code --tags origin refs/tags/v1.0.1
./gradlew --no-daemon --no-build-cache clean build
python scripts/smoke_jar.py build/libs/tictactest-1.0.1.jar
git tag -a v1.0.1 -m "Release v1.0.1"
git show v1.0.1
git rev-list -n 1 v1.0.1
git push origin v1.0.1
```

Unter PowerShell lautet der Gradle-Befehl `.\gradlew.bat`. Bei Folgeversionen
die Versionsnummer in allen Befehlen und im JAR-Pfad anpassen. Der absichtlich
erfolglose `git ls-remote`-Befehl (Exit-Code 2) bestätigt, dass der neue Tag auf
GitHub noch nicht existiert. `git status --short` muss vor dem Taggen leer sein.
VERSION und Changelog werden vorher auf einem Arbeitsbranch angepasst und nach
erfolgreicher CI über einen PR nach `main` übernommen. Der Tag wird erst danach
auf genau dem mit `git log -1` geprüften Commit erstellt.

## Automatisierung und Nachvollziehbarkeit

`.github/workflows/release.yml` startet ausschließlich beim Push von `v*`.
Er prüft das strenge Tagformat, VERSION, die Zugehörigkeit des Commits zu main
und den datierten Changelog-Eintrag. Danach installiert er Java 25, führt
einen frischen Gradle-Build mit allen Tests und JaCoCo aus und startet das JAR.
Der Starttest spielt X auf 0, 4 und 8 gegen den Computer und erwartet einen Sieg.

Erst danach erstellt der Workflow den GitHub Release mit Changelog-Auszug,
Commit-ID, JAR und SHA-256-Prüfsumme. Anschließend lädt er die veröffentlichten
Dateien erneut herunter, prüft die Prüfsumme und spielt erneut aus dem JAR.
Fehlschlag vor Veröffentlichung: kein Release, Actions-Lauf rot. Fehlschlag beim
Downloadtest: Release bereits vorhanden, Lauf rot; nicht als erfolgreich bewerten.
Veröffentlichte Tags/Artefakte nicht überschreiben: Fehler mit neuer Patchversion
beheben. Bei einem Fehler vor Veröffentlichung kann derselbe Taglauf erneut
gestartet werden, sofern der Commit selbst unverändert korrekt ist.

Der Tag zeigt auf genau einen Commit (`git rev-list -n 1 v1.0.0`).
Reproduzierbarkeit beruht auf diesem Quellstand, Gradle Wrapper, expliziten
Abhängigkeitsversionen und Java 25. JAR-Einträge haben eine feste Reihenfolge
und keine wechselnden Dateizeitstempel. Für byteidentische Vergleiche dieselbe
JDK-Patchversion verwenden; der Workflow protokolliert die verwendete Toolchain.

## Download und Verwendung

Unter [GitHub Releases](https://github.com/Philip222111/450-tictactest-mvk/releases)
das JAR der gewünschten Anwendungsversion herunterladen und mit Java 25 starten:

```sh
java -jar tictactest-1.0.0.jar
```

Es ist kein Neubau und keine Gradle-Installation erforderlich. Eingaben erfolgen
einzeln als Feldnummer 0–8. Der Spieler ist X, der Computer O. Die Anwendung
enthält keine externen Laufzeitbibliotheken; JUnit und AssertJ dienen nur Tests.
Die Prüfsumme lässt sich unter PowerShell mit `Get-FileHash <JAR> -Algorithm SHA256`
mit der heruntergeladenen .sha256-Datei vergleichen.

Zur manuellen Abnahme wird das Release-Asset von der Releases-Seite in ein
separates, leeres Verzeichnis heruntergeladen. Dort wird zuerst die SHA-256-
Prüfsumme verglichen und anschließend `java -jar tictactest-1.0.1.jar`
ausgeführt. Das Spiel muss ohne Repository, Quellcode oder erneuten Build starten.
Der Workflow automatisiert denselben Download- und Starttest unmittelbar nach
der Veröffentlichung.

Der zweite Release 1.0.1 korrigiert den Tippfehler der Eingabeaufforderung und
belegt denselben Ablauf erneut mit einem anderen Commit.
