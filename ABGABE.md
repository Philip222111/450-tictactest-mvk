# Abgabe – Coverage Time-Series (Auftrag 2 und 2.5)

- **Repository:** https://github.com/Philip222111/450-tictactest-mvk
- **Coverage-Verlauf:** https://philip222111.github.io/450-tictactest-mvk/coverage-history/index.html
- **Aktueller JaCoCo-Bericht:** https://philip222111.github.io/450-tictactest-mvk/report/index.html
- **Design und Architekturdiagramm:** [COVERAGE.md](COVERAGE.md)
- **Workflow:** [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **Workflow-Läufe und Berichtsartefakte:** https://github.com/Philip222111/450-tictactest-mvk/actions/workflows/ci.yml
- **Dauerhafte Messdaten:** https://github.com/Philip222111/450-tictactest-mvk/blob/coverage-history/coverage-history/history.json

## Abnahmekriterien nachvollziehen

1. Einen erfolgreichen Workflow-Lauf auf `main` öffnen. Im Job `build-and-test`
   werden Tests und JaCoCo ausgeführt; `jacoco-report` enthält HTML und XML.
2. Den Job `coverage-pages` prüfen: Er lädt die Historie, ergänzt den Messwert,
   speichert die Daten im Branch `coverage-history` und veröffentlicht die Seite.
3. Den Coverage-Verlauf öffnen. Er zeigt Instruction- und Branch-Coverage
   mit Commit-Kürzeln und einer Tabelle der Messwerte.
4. Nach einem weiteren erfolgreichen `main`-Lauf kontrollieren, dass der erste
   Messpunkt erhalten bleibt und ein neuer Commit hinzukommt.

Unveränderte Tests und unveränderter Anwendungscode ergeben dieselben Coverage-Werte.
Auch eine waagrechte Linie über mehrere Commits ist ein korrekt gemessener Verlauf.
Die initiale Veröffentlichung und die anschließende Ergänzung dieses Abgabedokuments
ermöglichen diese Prüfung ohne künstlich veränderte Messdaten.

## Kurzvorstellung im Plenum

- **Quelle:** aggregierte JaCoCo-Zähler im XML-Bericht des erfolgreichen Builds.
- **Metriken:** Instruction- und Branch-Coverage in Prozent.
- **Speicherung:** JSON im separaten Branch `coverage-history`, unabhängig von Artefaktablauffristen.
- **Aktualisierung:** nach erfolgreichen `main`-Builds; pro Commit ein Messpunkt.
- **Darstellung:** zwei statische SVG-Diagramme, Tabelle und Detailbericht auf GitHub Pages.
- **Architektur:** Diagramm in `COVERAGE.md` zeigen und einen Workflow-Lauf vorführen.

## Bewerteter Stand

Abgabe: Sonntag, 25. Oktober 2026, 23:59 Uhr (Europe/Zurich).
Es zaehlt ausschliesslich der zu diesem Zeitpunkt auf main gepushte Stand.
Muendliches Code-Review: 28. Oktober oder 4. November, 10-15 Minuten.
Notebook mit lokalem Abgabestand mitbringen. Die Note gilt fuer Modul 450 und 324.

[Auftragsnachweis](AUFTRAG.md), [Testkonzept](TESTKONZEPT.md),
[Releasekonzept](RELEASE.md), [Branch Protection](BRANCH_PROTECTION.md) und
[Pruefungsvorbereitung](PRUEFUNG.md) beschreiben die Anforderungen.
Die oben genannten Remote-Links sind Zieladressen, kein Nachweis eines
bereits erfolgreich veroeffentlichten aktuellen Stands.
