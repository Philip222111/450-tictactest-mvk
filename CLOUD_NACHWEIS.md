# Cloud-Aufträge: Umsetzung und Nachweise

Stand: 4. November 2026. Repository: `Philip222111/450-tictactest-mvk`.

## Auftrag 1: unverändertes Release-JAR im Browser

- `web/server.py` startet das JAR als eigenen Java-Prozess pro Spiel und verbindet
  dessen stdin/stdout mit der Browser-Konsole. Keine Änderung der Java-Spiellogik.
- HTTP-Integrationstest lokal erfolgreich: vollständige Partie, voneinander
  getrennte Sitzungen, ungültige Position und unbekannte Sitzung.
- Derselbe Integrationstest gegen die EC2-Webschnittstelle erfolgreich.
- Java-Build, Coverage-Gate und PIT erfolgreich; 79 von 79 Mutationen erkannt.
- Der Release-Lauf prüft die Web-Konsole direkt gegen das veröffentlichte JAR.

## Auftrag 2: OpenTofu erweitern und manuell deployen

- Bestehende Instanz `i-0e9c89d71a5e61c34` in `us-east-1` beibehalten.
- AMI `ami-0952e94e8e3ae87bf` festgelegt; keine unbeabsichtigte Ersetzung
  durch die Suche nach dem jeweils neuesten Image.
- OpenTofu-Apply: 0 hinzugefügt, 1 geändert, 0 zerstört (Web-Port TCP 8080).
- Release 1.1.0 zuerst manuell übertragen, SHA-256 geprüft, Corretto 25 installiert
  und systemd-Dienst `tictactest` als eigener Systembenutzer eingerichtet.
- Browseradresse: <http://44.213.113.233:8080>. Healthcheck: `/health`.
- S3-State nach `s3://tictactest-state-766661076063-us-east-1/tictactest/terraform.tfstate`
  migriert. Bucket mit blockiertem öffentlichen Zugriff, Versionierung,
  SSE-S3-Verschlüsselung und nativer State-Sperrdatei.
- Nach Migration: OpenTofu meldet keine Änderungen.

## Auftrag 3: Release-basiertes Deployment

- [Implementierungs-PR #10](https://github.com/Philip222111/450-tictactest-mvk/pull/10)
  nach erfolgreichen GitHub-Prüfungen zusammengeführt.
- GitHub-Umgebung `production` mit AWS- und SSH-Secrets sowie den benötigten
  Variablen eingerichtet. Secrets sind nicht im Repository gespeichert.
- [Release v1.2.0](https://github.com/Philip222111/450-tictactest-mvk/releases/tag/v1.2.0)
  per Tag-Push ausgelöst.
- [Release und automatisches Deployment: erfolgreich](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41803795667).
  JAR gebaut, getestet, veröffentlicht, erneut heruntergeladen und geprüft;
  anschliessend vom wiederverwendbaren Workflow auf EC2 installiert.
- Infrastruktur blieb unverändert. Das neue JAR ersetzte die manuell installierte
  Version. Der Dienst startete für die neue Version neu und bestand den Healthcheck.
- [Identisches Release erneut deployt: erfolgreich](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41804082644).
  OpenTofu: `No changes`, Apply: 0 hinzugefügt, 0 geändert, 0 zerstört.
  Rsync meldete keine geänderten Nutzdateien.
- Prozess-ID und Startzeit vor und nach dem Wiederholungsdeployment identisch:

```text
MainPID=27822
ActiveEnterTimestamp=Wed 2026-11-04 09:01:14 UTC
```

Die UTC-Zeit entspricht 10:01:14 Uhr in der Schweiz am genannten Datum.
SHA-256 des installierten und veröffentlichten JARs:

```text
5cd356f22dcd043b428c01f8fd607f2c6e57c064c783b9e2a7074ace80cdae2c
```

Damit ist nachgewiesen: Identische Dateien werden nicht erneut übertragen und
verursachen keinen Dienstneustart. OpenTofu wendet nur Zustandsunterschiede an.
Der temporäre Runner-Zugang wird nach jedem Deployment wieder entfernt.

## Späterer Betrieb und Abgabe

- AWS-Lab und EC2 müssen laufen. Die öffentliche IP kann sich nach Stop/Start
  ändern; danach SSH-Host-Key für die neue Adresse verifizieren und
  `EC2_KNOWN_HOSTS` in GitHub aktualisieren.
- Lab-Credentials sind temporär. Bei Ablauf die drei AWS-Secrets der Umgebung
  `production` aus derselben neuen Lab-Sitzung aktualisieren. Ein erfolgreiches
  Deployment heute bedeutet keine unbegrenzt gültige Anmeldung.
- Für spätere Releases VERSION und CHANGELOG gemäss [RELEASE.md](RELEASE.md)
  aktualisieren und einen neuen Versions-Tag pushen.
- Anleitung für Neuaufbau und Fehlersuche: [CLOUD.md](CLOUD.md).
- Die zusätzlichen Teams-Auftragsdateien lagen nicht vor. Besondere Kriterien
  oder verlangte Screenshots daraus müssen vor Abgabe abgeglichen werden.
