# Vorbereitung auf das Code-Review

## Teststrategie

Die Basis der Testpyramide sind schnelle Unit-Tests fuer Gewinnlinien, Stein-
zuordnung und Spieler. `play` wird als Komponente mit selbst geschriebenen
ScriptedPlayers getestet. Pioneer erfasst die Konsole. Der JAR-Smoke-Test ist
ein schmaler Ende-zu-Ende-Test des verpackten Programms. Es gibt keine Web-UI,
Datenbank oder externen Dienste, die weitere Integrationstests rechtfertigen.

AssertJ prueft Ergebnisse, Exceptions, Array-Inhalte und Ausgabe. Parametrisierte
Tests trennen Daten und Prueflogik. Fixtures liefern frische Boards und feste
Zugfolgen. jqwik erzeugt viele Zugreihenfolgen; der feste Seed reproduziert
Fehler. Das ist eine Stichprobe, kein vollstaendiger Beweis.

## Perfekter Spieler

Minimax durchsucht alle legalen Fortsetzungen. Negamax nutzt die Symmetrie:
Der Wert des Gegners wird negiert. Ein Sieg liefert einen hoeheren Wert als
Remis oder Niederlage; die Tiefe bevorzugt fruehe Siege und spaete Niederlagen.
Nach jedem simulierten Zug wird das Feld wieder geleert. Der Eingabezustand
wird kopiert, damit die Suche das Board des Aufrufers nicht veraendert.
Tests untersuchen alle gegnerischen Antworten auf die deterministischen
Spielerzuege fuer X und O. Fuer groessere Bretter waeren Caching und
Alpha-Beta-Pruning sinnvoll; hier bleibt die vollstaendige Suche ueberschaubar.

## Coverage und Mutationstests

Branch-Coverage misst ausgefuehrte Entscheidungszweige. 100 % bedeutet nicht,
dass jede fachliche Anforderung oder jeder moegliche Fehler getestet ist.
PIT veraendert Bytecode, zum Beispiel Vergleichsoperatoren. Schlaegt ein Test
fehl, wurde die Mutation erkannt. Ueberlebende Mutationen koennen Testluecken
oder aequivalentes Verhalten zeigen; den konkreten Diff im Bericht bewerten.
Das 90-%-Gate verhindert strukturelle Rueckschritte, ersetzt aber kein Review.

## Pipeline und Releases

PR -> Java-Build, Tests, Coverage-Gate und PIT sowie Python-Infrastrukturtests.
GitHub Branch Protection muss diese Checks verbindlich machen. Erst erfolgreiche
main-Laeufe ergaenzen die Coverage-Zeitreihe. JSON bleibt im separaten Branch
erhalten, Berichte werden als Artefakte und ueber Pages bereitgestellt.
Bei schnellen Pushes kann die Pages-Concurrency wartende Laeufe ueberspringen.

VERSION steuert JAR-Namen und Manifest. Ein passender vMAJOR.MINOR.PATCH-Tag
auf einem main-Commit startet den Anwendungsrelease mit Build, Smoke-Test,
Pruefsumme und erneutem Downloadtest. Devcontainer-Releases haben eigene
Tags devcontainer-v...; ein Versions-PR aktualisiert die Verbraucher.
Quellstand und explizite Versionen helfen der Reproduzierbarkeit. Bewegliche
Basisimage-Tags und JDK-Patchstaende begrenzen byteidentische Wiederholungen.

## Schwachstellen und neue Requirements

- Ungueltige Konsoleneingaben brechen ab: Eingaben erneut abfragen und klare
  Fehlermeldungen definieren, bevor die Implementierung geaendert wird.
- main nutzt weiterhin GreedyPlayer: Auswahl zwischen einfachem und perfektem
  Gegner als neues Requirement spezifizieren.
- Spielkern erwartet gueltige Boards und Spielsteine: fuer eine oeffentliche
  API Validierungsregeln und Verhalten fuer unmoegliche Spielstaende festlegen.
- Groessere Teams: mindestens ein fremdes Review, CODEOWNERS nach Verantwortung,
  Releaseberechtigungen und regelmaessige Abhaengigkeitsupdates.

Vor der Pruefung jeden genannten Test und Workflow selbst oeffnen und eine
konkrete Entscheidung, Alternative und Grenze erklaeren koennen. Notebook
mit dem tatsaechlich abgegebenen Commit vom 25. Oktober bereithalten.
