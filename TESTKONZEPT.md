# Testkonzept – TicTacTest

Stand: 23. September 2026

## 1. Ziel und Testobjekte

Die Tests sollen nachweisen, dass die Tic-Tac-Toe-Regeln korrekt umgesetzt sind
und Änderungen keine bereits funktionierenden Spielabläufe beschädigen. Geprüft
werden insbesondere:

- Gewinnerkennung für alle drei Reihen, alle drei Spalten und beide Diagonalen,
- normale Spielabläufe mit X- oder O-Sieg,
- ein vollständiges Spiel ohne Gewinner (Unentschieden),
- Zurückweisung von Zügen außerhalb des Spielfelds und auf belegte Felder,
- korrekter Spielerwechsel und korrekte Zuordnung von X und O,
- Schutz des internen Spielfelds gegen Änderungen durch einen Spieler,
- Verhalten des einfachen `GreedyPlayer` und von `Stone.opponent()`.

Testgrundlage sind `TicTacToeMain`, `TicTacToePlayer`, `GreedyPlayer` und die
in `src/test/java` abgelegten Tests. `HumanPlayer` und der interaktive
Programmeinstieg werden nicht automatisiert getestet, weil sie direkt von
`System.in` abhängen; ihr fachlicher Kern läuft über die separat getestete
Methode `play`.

## 2. Risiken und Qualitätsziele

Das höchste Risiko liegt in falsch erkannten Gewinnlinien oder einem fehlerhaften
Spielerwechsel. Ebenfalls relevant sind ungültige Array-Indizes, das Überschreiben
belegter Felder und Seiteneffekte, wenn ein Spieler das erhaltene Board verändert.
Die Tests sind deterministisch, benötigen weder Netzwerk noch Datenbank und müssen
lokal sowie in CI dasselbe Ergebnis liefern.

Für das kleine Projekt wird keine feste Mindest-Coverage als Build-Gate gesetzt.
Coverage dient als Hinweis auf ungetestete Pfade, nicht als alleiniger
Qualitätsnachweis. Die fachlichen Erwartungen werden immer durch Assertions
geprüft.

## 3. Teststrategie

### Unit- und Komponententests

`isWin`, `GreedyPlayer` und `Stone.opponent()` werden als isolierte Units geprüft.
`play` wird als kleine Komponente mit kontrollierten Testspielern ausgeführt. Die
Testspieler liefern festgelegte Zugfolgen; dadurch lassen sich Sieg, Unentschieden
und Fehlerfälle ohne Konsoleneingabe reproduzieren.

### Parametrisierte Tests

Gleichartige Fälle werden mit JUnit `@ParameterizedTest` zusammengefasst:

- `@MethodSource("winningBoards")`: acht mögliche Gewinnlinien,
- `@MethodSource("nonWinningBoards")`: Stellungen ohne Gewinner,
- `@ValueSource`: ungültige Positionen unterhalb und oberhalb des Boards,
- `@CsvSource`: verschiedene Belegungen für die Wahl des ersten freien Felds.

So bleibt die Prüflogik an einer Stelle, während jeder Datensatz als eigener Test
und mit verständlichem Namen im Bericht erscheint.

### Fixtures und Test-Helper

- `TicTacToeMainTest.setUp()` erzeugt mit `@BeforeEach` vor jedem Test ein
  frisches leeres Board.
- Der Helper `board(...)` wandelt lesbare X/O/Punkt-Darstellungen in `Stone[]` um.
- `assertWinner(...)` und `assertNoWinner(...)` bündeln wiederkehrende Assertions.
- `TicTacToeGameTest.ScriptedPlayer` ist ein Fixture für kontrollierte Zugfolgen
  und protokolliert Farben sowie erhaltene Board-Kopien.
- `captureConsoleOutput()` und `restoreConsoleOutput()` isolieren mit
  `@BeforeEach`/`@AfterEach` die Konsolenausgabe des Spielablaufs.

Jede Fixture wird pro Test neu erstellt. Die Tests teilen deshalb keinen
veränderlichen Spielzustand.

## 4. Testfallkatalog

| ID | Ebene | Testfall / Daten | Erwartetes Ergebnis |
| --- | --- | --- | --- |
| WIN-01–03 | Unit | X/O belegt obere, mittlere oder untere Reihe | `isWin` liefert `true` |
| WIN-04–06 | Unit | X/O belegt linke, mittlere oder rechte Spalte | `isWin` liefert `true` |
| WIN-07–08 | Unit | X/O belegt eine der beiden Diagonalen | `isWin` liefert `true` |
| NOWIN-01 | Unit | Leeres Board, Prüfung für X und O | jeweils `false` |
| NOWIN-02–04 | Unit | zwei Steine bzw. volles Board ohne passende Linie | `false` |
| GAME-01 | Komponente | X: 0,1,2; O: 3,4 | X gewinnt nach fünf Zügen; Farben wechseln |
| GAME-02 | Komponente | X: 0,1,8; O: 3,4,5 | O gewinnt nach sechs Zügen |
| GAME-03 | Komponente | neun gültige Züge ohne Linie | Rückgabe `null`, Ausgabe meldet Unentschieden |
| INVALID-01–02 | Komponente, parametrisiert | Position `-1` oder `9` | `IllegalStateException` mit Position |
| INVALID-03 | Komponente | O wählt das bereits von X belegte Feld 0 | `IllegalStateException` |
| INVALID-04 | Komponente | dieselbe Spielerinstanz für X und O | `IllegalArgumentException` |
| EDGE-01 | Komponente | Testspieler verändern die erhaltene Board-Kopie | internes Board bleibt intakt; Spiel endet remis |
| PLAYER-01–03 | Unit, parametrisiert | leeres/teilbelegtes Board | `GreedyPlayer` wählt erstes freies Feld |
| PLAYER-04 | Unit | vollständig belegtes Board | `GreedyPlayer` wirft `IllegalStateException` |
| PLAYER-05 | Unit | `CROSS` und `CIRCLE` | `opponent()` liefert jeweils den anderen Stein |

Aktuell ergeben sich 25 Testausführungen. Der Leertest enthält zwei fachliche
Assertions; die Anzahl der Testausführungen ist daher nicht identisch mit der
Anzahl einzelner Assertions.

## 5. Grenzfälle und Abgrenzung

Die öffentlichen Spielregeln akzeptieren Felder 0 bis 8. Beide unmittelbar
außerhalb liegenden Werte, ein belegtes Feld, ein volles Board und mutierende
Spieler sind abgedeckt. `isWin` erwartet gemäß Methodendokumentation ein Board
mit neun Feldern und einen Spielstein; `null` oder kürzere Arrays sind ungültige
API-Aufrufe und kein definierter Spielfall. Performance-, Last-, Sicherheits-
und UI-Tests sind bei diesem lokalen Konsolenspiel nicht sinnvoll.

Eine kurze manuelle Prüfung kann ergänzend `TicTacToeMain` starten und Eingaben
0–8 verwenden. Sie ersetzt die automatisierten Tests nicht.

## 6. Ausführung und Auswertung

Linux/macOS/Devcontainer:

```sh
./gradlew test
./gradlew build
./gradlew jacocoTestReport
```

Windows PowerShell:

```powershell
.\gradlew.bat test
.\gradlew.bat build
.\gradlew.bat jacocoTestReport
```

Ergebnisse:

- JUnit HTML: `build/reports/tests/test/index.html`
- JUnit XML: `build/test-results/test/`
- JaCoCo HTML: `build/reports/jacoco/test/html/index.html`
- JaCoCo XML: `build/reports/jacoco/test/jacocoTestReport.xml`

Das Gradle-JaCoCo-Plugin instrumentiert die beim `test`-Task ausgeführten
Klassen. `test.finalizedBy jacocoTestReport` und `jacocoTestReport.dependsOn test`
stellen sicher, dass Test und Bericht zusammen erzeugt werden. JaCoCo misst unter
anderem Instructions, Branches, Lines, Methods und Classes.

## 7. CI und Coverage-Verlauf

`.github/workflows/ci.yml` startet bei Pushes, Pull Requests und manuell. Der Job
`build-and-test` führt `gradlew build` im Java-25-CI-Container aus. Testberichte
und der vollständige JaCoCo-Bericht werden als Actions-Artefakte hochgeladen.

Nur nach einem erfolgreichen Nicht-PR-Lauf auf `main` startet `coverage-pages`.
Der Job testet zunächst das Python-Skript, lädt die bisherige Historie aus dem
separaten Branch `coverage-history`, liest die aggregierten `INSTRUCTION`- und
`BRANCH`-Zähler aus dem JaCoCo-XML und ergänzt pro Commit höchstens einen
Messpunkt. Die Einträge werden nach der monotonen Workflow-Run-ID sortiert und
mit UTC-Zeit gespeichert. Anschließend werden statische SVG-Diagramme, die
Wertetabelle und der aktuelle JaCoCo-HTML-Bericht über GitHub Pages veröffentlicht.

Der Branch `coverage-history` ist vom Push-Trigger ausgeschlossen, damit das
Speichern eines Messpunkts keinen Endloslauf auslöst. Details und Betriebsgrenzen
stehen in [COVERAGE.md](COVERAGE.md).

## 8. Pflege

Bei neuen Regeln oder Produktionsklassen werden zuerst Testfallkatalog und
Fixtures angepasst, danach die automatisierten Tests. Neue gleichartige Daten
gehören bevorzugt in bestehende Parameterquellen. Ein Test gilt erst als
erfolgreich, wenn er lokal und im zugehörigen GitHub-Actions-Lauf grün ist.
