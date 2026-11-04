# Changelog

## 1.3.2 - 2026-11-04

### Added
- Automatischer Frontend-only-Release als Trennungsnachweis.

### Changed
- Dunkelblauer Hintergrund im Frontend.

### Fixed
- Windows-ConPTY-Einschraenkung dokumentiert; lokaler Linux-Container als Alternative.

## 1.3.1 - 2026-11-04

### Added
- Manueller Release-B-Nachweis fuer die getrennte Frontend-Auslieferung.

### Changed
- Goldene Schaltflaeche als sichtbare Frontend-Aenderung.
- EC2 laedt nur die zu aktivierenden Komponenten aus dem privaten Artefaktspeicher.

### Fixed
- Keine Backend-Aenderung.

## 1.3.0 - 2026-11-04

### Added
- Echte ttyd-Web-Konsole mit PTY/WebSocket und getrenntem statischem Frontend.
- Frontend- und Tools-Archive, Deployment-Manifest und HTTP-Versionsabfragen.
- Elastic IP, LabInstanceProfile, SSM-Bootstrap und privater Artefaktspeicher.
- Release-Tag-Vergleich, komponentenbezogenes Deployment und gezielter Rollback.
- Secrets-Konzept, Betriebsanleitung und Promotion-Strategie in docs/deployment.md.

### Changed
- App-Deployments verwenden S3/SSM und fuehren kein OpenTofu mehr aus.
- Laufzeitkonfiguration und Infrastruktur sind vom Release-Inhalt getrennt.

### Fixed
- Frontend-only-Releases starten das Backend nicht mehr allein wegen VERSION neu.
- Frontend-Deployments erhalten die von der Infrastruktur erzeugte Konfiguration.

## 1.2.0 - 2026-11-04

### Added
- Browser-Konsole fuer das unveraenderte Release-JAR mit getrennten Spielsitzungen.
- EC2-Webzugang, systemd-Installation und gemeinsamer verschluesselter S3-State.
- Release-Deployment mit OpenTofu, SHA-256-Pruefung und inhaltsbasiertem Dateiabgleich.
- HTTP-Integrationstest und Schritt-fuer-Schritt-Dokumentation der Cloud-Einrichtung.

### Changed
- AMI wird explizit festgelegt, damit neue AWS-Images keine EC2-Ersetzung ausloesen.
- Der Release-Workflow ruft nach erfolgreicher Veroeffentlichung das Deployment auf.

### Fixed
- Unveraenderte Anwendungsdateien verursachen keinen erneuten Dienstneustart.
- Automatische Infrastruktur-Deployments blockieren Loeschungen und Ersetzungen.

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
