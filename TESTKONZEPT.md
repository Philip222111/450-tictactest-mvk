# Testkonzept - TicTacTest

Stand: 21. Oktober 2026

## Ziel und Strategie

Spielregeln, Eingaben, Ausgaben und Computerspieler werden automatisch mit
JUnit und AssertJ getestet. Es werden keine Mockingframeworks verwendet.
Der vorhandene Spielkern wurde bei dieser Bearbeitung nicht angepasst.

## Testgruppen

| Testklasse | Gegenstand |
| --- | --- |
| TicTacToeMainTest | Gewinnerkennung, leeres Board und Gegenbeispiele |
| WinningLinesTest | Acht Linien fuer beide Farben, jeweils vollstaendig und an jeder Position unterbrochen |
| TicTacToeGameTest | X-/O-Sieg, Remis, Spielerwechsel, ungueltige Zuege und defensive Board-Kopien |
| TicTacToePlayerTest | Erster freier Platz, volles Board und Gegnerzuordnung |
| ConsoleTest | Pioneer StdIn/StdOut: 0, 8, Text, Eingabeende, Board, Sieg und Remis |
| PerfectPlayerTest | Gewinnen, Blockieren, Remis, Argumentfehler und bereits beendete Spiele |
| PlayerPropertiesTest | jqwik: 150 generierte Zugreihenfolgen mit festem Seed |

ParameterizedTest mit MethodSource, CsvSource, ValueSource und EnumSource
vermeidet wiederholte Testlogik. BoardFixtures stellt lesbare Boards bereit;
ScriptedPlayer liefert kontrollierte Zuege und protokolliert den Spielzustand.
Jeder Spieltest startet mit einem frischen Board.

PerfectPlayer verwendet Minimax. Der Test durchlaeuft fuer beide Farben alle
gegnerischen Fortsetzungen bei den deterministischen Zuegen des perfekten
Spielers und prueft, dass keine Niederlage eintritt. Ein Spiel gegen sich
selbst muss remis enden. jqwik prueft auf legalen Spielstaenden, dass beide
Computerspieler ein freies Feld waehlen und das uebergebene Board nicht aendern.
Generierte Partien enden nach Sieg oder neun Zuegen.

## Ausfuehrung und Qualitaetsgate

```powershell
.\gradlew.bat build pitest
```

Linux/Container: `bash gradlew build pitest`.

JaCoCo erzeugt HTML und XML. `jacocoTestCoverageVerification` erzwingt
mindestens 90 % Branch-Coverage ueber alle Produktionsklassen und ist Teil
von `check` und `build`. Coverage allein ersetzt keine fachlichen Assertions.
PIT fuehrt Mutationstests mit JUnit-Integration aus und erzeugt HTML/XML.

Verifizierter lokaler Lauf: 112 Testausfuehrungen ohne Fehler, 100/100 Branches,
502/514 Instructions (97,67 %), 79/79 erkannte Mutationen (100 %).
Keine Mutation blieb ohne Coverage. Alle erzeugten Mutationen wurden erkannt; die Teststaerke ist dennoch
kein Vollstaendigkeitsbeweis.

Berichte:

- JUnit: `build/reports/tests/test/index.html`
- JaCoCo: `build/reports/jacoco/test/html/index.html`
- JaCoCo XML: `build/reports/jacoco/test/jacocoTestReport.xml`
- PIT: `build/reports/pitest/index.html` und `mutations.xml`

## CI und Grenzen

ci.yml fuehrt `build pitest` und einen separaten Python-Infrastrukturcheck bei Pushes und Pull Requests aus und stellt
JUnit-, JaCoCo- und PIT-Berichte als Artefakte bereit. Der bestehende
Coverage-Verlauf ist in COVERAGE.md beschrieben.

Der Programmeinstieg selbst wird nicht aufgerufen; HumanPlayer und play
werden separat getestet. Ungueltige Arrays fuer den unveraenderten Spielkern
sind keine definierten Spielfaelle. Der aktuelle Remote-Abnahmestand und offene Punkte stehen zentral in ABGABE.md.
Der lokale Testlauf allein weist keine fristgerechte Abgabe nach.

## Technologien und Nachweis

Die fixierten stabilen Versionen in build.gradle wurden am 21. Oktober mit den
Maven-Central-Metadaten abgeglichen: JUnit 6.1.3, AssertJ 3.27.7, Pioneer 2.3.0,
jqwik 1.10.2, JaCoCo 0.8.15, PIT 1.30.1 und PIT-JUnit5 1.2.3.
Quelle: https://repo.maven.apache.org/maven2/

Der erneute Linux-Lauf im lokal gebauten Devcontainer mit Java 25.0.4.1 und
Gradle 9.7.0 bestand `clean build pitest`. Zusaetzlich bestanden die fuenf
Python-Tests, actionlint (ohne ShellCheck) und der JAR-Smoke-Test fuer 1.1.0.
SonarQube for IDE (SonarLint) ist als Devcontainer-Erweiterung vorgemerkt;
ein warnungsfreier IDE-Analyselauf ist damit noch nicht nachgewiesen.

Im Windows-OneDrive-Verzeichnis traten bei spaeteren Wiederholungen Dateisperren
und nicht lesbare generierte Klassen auf. Der frische Linux-Lauf kopierte die
Quellen aus einem nur lesbar gemounteten Ordner in /tmp/project und vermied
so synchronisierte Build-Ausgaben. Alternativ lokal ausserhalb OneDrive bauen.
