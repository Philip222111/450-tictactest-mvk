# Nachweise zu den drei Detailaufträgen

Durchgeführt am **4. November 2026**. Grundlage: Web-App-Aufträge 1–3 der
Berufsbildungsschule Winterthur, Version `261103-71bf6d91` vom 3. November 2026.
Die erste, anschliessend erweiterte Iteration steht historisch in `CLOUD_NACHWEIS.md`.

**Aktuelle Web-App:** <http://ec2-54-90-29-23.compute-1.amazonaws.com>

## Auftrag 1: lokal nur aus Release-Assets

- [Release 1.3.0](https://github.com/Philip222111/450-tictactest-mvk/releases/tag/v1.3.0)
  veröffentlicht JAR, Frontend-ZIP, Tools-ZIP, Manifest und Prüfsummen.
- Die heruntergeladenen Assets wurden geprüft und read-only in einen lokalen
  Linux-Container eingebunden. Es wurde dort kein Anwendungscode ausgecheckt
  oder kompiliert. Java und Python sind Laufzeitvoraussetzungen.
- Frontend auf localhost:8000, ttyd auf localhost:7681. HTML, `config.js` und beide
  Versionsabfragen lieferten HTTP 200 und Version `1.3.0`.
- `scripts/check_terminal.py` spielte über das echte ttyd-WebSocket/PTY-Protokoll
  mit 0, 4 und 8 eine vollständige Partie bis `winner is: CROSS`.
- Zwei gleichzeitige Terminalverbindungen erzeugten auf EC2 genau zwei Java-
  Prozesse. `abc` beendete nur den betroffenen Prozess mit NumberFormatException.
- Native Windows-ConPTY-Ausgabe war beim Beenden unzuverlässig. Der getestete
  Linux-Weg und die genaue lokale Anleitung sind in [webkonsole.md](webkonsole.md)
  beschrieben; ein Browser-Screenshot wird hier nicht vorgetäuscht.

## Auftrag 2: zwei manuelle Releases ohne Infrastruktur-Neuerstellung

| Release | Veröffentlichung | Manuelles Deployment | Ergebnis |
|---|---|---|---|
| A: 1.3.0 | [Release-Workflow](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41808927372) | heruntergeladene Assets → `python scripts/deploy_cloud.py`, FORCE=true | Backend 1.3.0, Frontend 1.3.0 |
| B: 1.3.1 | [Release-Workflow](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41809856492) | derselbe S3-/SSM-Ablauf, goldene Frontend-Schaltfläche | Backend 1.3.1, Frontend 1.3.1 |

`AUTO_DEPLOY=false` war für diese beiden Übungen gesetzt; danach wurde es
auf true gesetzt. Zwischen den beiden erfolgreichen manuellen Installationen
gab es **kein tofu apply**, keine neue EC2 und keine neue Adresse. Ein
anschliessender `tofu plan` meldete `No changes`. Die originalen JARs stammen
aus den Release-Assets, nicht aus einem lokalen Deployment-Build.

Ein anfänglich fehlendes Manifest-Prüfsummen-Asset in 1.3.1 führte beim ersten
Versuch zu einem fehlgeschlagenen SSM-Abruf, bevor die Anwendung verändert wurde.
Nach Ergänzung der Prüfsumme gelang der manuelle Deploy. Die spätere Veröffentlichung
prüft nun acht vollständige Assets im Draft vor deren Freigabe.

### Robustheit und Infrastruktur-Änderung

1. **Stop/Start tatsächlich ausgeführt:** Instanz `i-0e9c89d71a5e61c34` gestoppt
   und gestartet. Elastic IP `98.87.74.14` blieb erhalten. Ohne App-Deployment
   liefen automatisch wieder Backend 1.3.1 und Frontend 1.3.2.
2. **Dienstkonfiguration geändert:** `Environment=TICTACTEST_DEPLOYMENT=classroom`
   ergänzt. Plan: ausschliesslich Updates von EC2-user_data, SSM-Dokument und
   SSM-Association; keine Creates/Deletes. Nach Apply: gleiche Instanz und EIP,
   Variable in systemd vorhanden, Backend 1.3.3 und Frontend 1.3.2 unverändert.
3. **Vollständiger destroy/apply tatsächlich ausgeführt:** geprüfter Plan mit
   zehn Löschungen angewendet, danach zehn Ressourcen neu erstellt. Die privaten
   Bootstrap-Buckets, Release-Assets, vorhandene VPC und LabInstanceProfile
   wurden nicht gelöscht. Folgende Werte änderten sich:

| Wert | Vorher | Nachher |
|---|---|---|
| EC2-ID | i-0e9c89d71a5e61c34 | i-0b1c2b22f597d29ea |
| Elastic IP | 98.87.74.14 | 54.90.29.23 |
| AWS-DNS | ec2-98-87-74-14.compute-1.amazonaws.com | ec2-54-90-29-23.compute-1.amazonaws.com |

Die Runtime wurde beim Neuaufbau eingerichtet. Die neue Instanz enthielt noch
kein App-JAR. `INSTANCE_ID` und `APP_URL` in GitHub wurden aus den neuen Outputs
übernommen; der Artefakt-Bucket blieb derselbe. Anschliessend wurde das bereits
veröffentlichte 1.3.4 **ohne Neubau** wiederhergestellt:
[erfolgreicher Wiederaufbau-Deploy](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41814089137).

**Verbleibende Plattformprüfung:** Ein echter „End Lab“/„Start Lab“-Wechsel in
der Learner-Lab-Oberfläche wurde nicht ausgeführt. Der EC2-Stop/Start wurde
getestet, ersetzt aber keinen Nachweis für das Verhalten der Schulplattform.
Beim nächsten Lab-Start gleiche URL/Versionen prüfen und abgelaufene Credentials
erneuern. Das kann nur die angemeldete Person in der Lab-Oberfläche erledigen.

## Auftrag 3: Trennung bei echten Releases

| Fall | Lauf | Laufende Versionen danach | Zusätzlicher Nachweis |
|---|---|---|---|
| Nur Frontend: 1.3.2 | [erfolgreich](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41811019638) | Backend 1.3.1, Frontend 1.3.2 | Backend-PID 2792 und Startzeit 09:51:55 UTC identisch; JAR-Hash unverändert; config.js erhalten; obsolete-proof.txt danach HTTP 404 |
| Nur Backend: 1.3.3 | [erfolgreich](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41811975737) | Backend 1.3.3, Frontend 1.3.2 | Inode und Zeitstempel des Frontend-Verweises sowie SHA-256 aller Frontend-Dateien identisch |
| Beide: 1.3.4 | [erfolgreich](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41813045396) | Backend 1.3.4, Frontend 1.3.4 | Beide Komponenten durch Release-Assets ersetzt, beide HTTP-Versionen geprüft |
| Push auf main ohne Tag | [CI](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41812460442), Commit 6e9e07e | Backend 1.3.3, Frontend 1.3.2 blieben aktiv | Backend-Prozess, JAR, Konfiguration und Deployment-State vor/nach Push identisch; nur CI-/Container-Workflows gestartet |
| Nur Dokumentation: 1.3.5 | [erfolgreich](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41815425226) | Backend 1.3.4, Frontend 1.3.4 bleiben aktiv | changed=false für beide; PID 26394/Startzeit 10:25:50 UTC, JAR/Config-Hashes und Frontend-Inode/Zeitstempel/Dateien unverändert |

Die Prüfung bezieht sich auf vollständige Release-Tag-Differenzen. Eine neue
VERSION-Datei allein zählt nicht als Backend-Änderung. Das verhindert einen
unnötigen Neustart bei Frontend- oder Dokumentations-Releases.

Nach dem Neuaufbau: cloud-init meldete `done`, nginx und tictactest sind
`enabled` und `active`. Ein weiterer echter WebSocket-Partietest bestand.
Die AWS-Abfrage auf der EC2 lieferte eine LabRole-Session der neuen Instanz;
eine statische AWS-Credentials-Datei war nicht vorhanden. Die neue SSH-Host-ID
wurde über den authentisierten SSM-Kanal verifiziert und lokal hinterlegt.

### Rollback und Wiederherstellung

- [Manuell v1.2.0 gewählt](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41813373990):
  Backend und Frontend zeigten danach 1.2.0 an.
- [Manuell zurück auf v1.3.4](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/41813428076):
  beide Versionen wieder 1.3.4.
- Für die ursprünglichen Releases 1.0.0, 1.0.1, 1.1.0 und 1.2.0 wurden fehlende
  Frontend-/Tools-/Manifest-Assets einmalig als **Kompatibilitätsmigration**
  ergänzt. Ihre Release-Notes kennzeichnen die Herkunft aus Frontend 1.3.0.
  Die bestehenden JARs und ihre Prüfsummen wurden nicht ersetzt. Diese Migration
  behauptet nicht, dass die alten Releases ursprünglich schon ein Frontend hatten.

### Fehlerfälle und Secrets

- Privates Testartefakt v9.9.9: gültige SHA-256 und passende Manifest-Version,
  aber nicht vorhandene Java-Mainklasse. SSM-Installer schlug nach rund 8,6 s
  fehl. Gesunde JAR-Prüfsumme, Konfiguration, Versionsdateien und Prozess-ID
  blieben identisch; es war kein Wiederanlauf der gesunden App erforderlich.
  Dies war ein kontrolliertes privates Fixture, kein publizierter kaputter Release.
- Authentisierungsprobe mit absichtlich ungültigen temporären Credentials:
  `InvalidClientTokenId`, bevor S3 oder SSM verändert wurden. Der Workflow
  enthält dieselbe STS-Prüfung als ersten Schritt. Eine tatsächliche Erneuerung
  der nächsten Lab-Sitzung bleibt naturgemäss manuell.
- SSH-Secrets aus der ersten Iteration wurden aus GitHub entfernt. Die finale
  Pipeline benötigt nur die drei temporären AWS-Secrets; die EC2 verwendet ihr
  Instance Profile. Kein privater SSH-Key und kein State wird an CI ausgeliefert.
- Die beobachteten GitHub-500/502-Schreibfehler sind in den ersten Versuchen der
  Release-Läufe sichtbar. Die endgültig verlinkten Läufe sind erfolgreich;
  vollständige Assets werden jetzt vor Veröffentlichung im Draft geprüft.

Secrets-Konzept, alle manuellen Schritte, Änderungspfade, Diagramme und
Promotion-Strategie: [deployment.md](deployment.md).
