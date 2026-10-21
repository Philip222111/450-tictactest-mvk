# Changelog

## 1.1.0 - 2026-10-21

### Added
- PerfectPlayer mit vollstaendiger Minimax-Suche.
- Pioneer-Konsolentests, jqwik-Properties und PIT-Mutationstests.
- Verbindliche 90-%-Branch-Coverage im Build und CI-Berichtsartefakte.

### Changed
- Gemeinsame Board-Fixture statt mehrfacher Testdatenparser.
- Infrastrukturtests als eigener PR-Check; vorbereitete Schutzregeln fuer main.
- Neuer Devcontainer-Dockerfile mit Ubuntu/glibc fuer GitHub Actions.

### Fixed
- Pioneer-Integrationstest erfasst die Ausgabe korrekt.
- Tests pruefen Fehlerausgabe und deterministische Zugwahl bei Gleichstand.
- Generierte IDE-Klassen werden nicht mehr versioniert.

## 1.0.1 - 2026-10-01

### Added
- Keine neuen Spielfunktionen.

### Changed
- Spielregeln und Bedienung bleiben kompatibel zu 1.0.0.

### Fixed
- Doppeltes „to“ in der Eingabeaufforderung entfernt und Satzanfang korrigiert.

## 1.0.0 - 2026-09-23

### Added
- Erste versionierte JAR-Veröffentlichung des vorhandenen Konsolenspiels:
  Mensch (X) gegen den Computer (O), der das erste freie Feld wählt.
- Ausführbares JAR mit Java 25, Release-Workflow und SHA-256-Prüfsumme.
- Automatischer Starttest spielt ein vollständiges Spiel aus dem JAR.

### Changed
- JAR-Dateinamen und Manifest verwenden die zentrale Datei VERSION.

### Fixed
- Kein separater Spiellogik-Bugfix in dieser ersten Veröffentlichung.
