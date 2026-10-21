# TicTacTest - Auftragsnachweis

Die Anforderungen und ihre Tests sind in [TESTKONZEPT.md](TESTKONZEPT.md)
dokumentiert. Lokal erfolgreich: `gradlew.bat build pitest`.

- JUnit/AssertJ und parametrisierte Tests mit Hilfsstrukturen
- Pioneer fuer StdIn/StdOut
- JaCoCo: 100 % Branch-Coverage; mindestens 90 % als Build-Gate
- PerfectPlayer mit Minimax und Pruefung aller gegnerischen Fortsetzungen
- jqwik als weiteres Framework, 150 generierte Zugreihenfolgen
- PIT: 79 von 79 Mutationen erkannt
- CI fuehrt Build und PIT aus und archiviert alle drei Berichtstypen

112 Testausfuehrungen waren erfolgreich. Original-Spielkern unveraendert;
keine Mockingframeworks. Der aktuelle Abnahmestand steht in ABGABE.md.

Weitere Nachweise: frischer Linux-Container-Build, fuenf Python-Tests,
actionlint und JAR-Smoke-Test fuer den Release 1.1.0.
Das aktive Main-Ruleset verlangt PRs und die drei erforderlichen CI-Checks.
Details stehen in BRANCH_PROTECTION.md.
