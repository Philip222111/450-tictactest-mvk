# Erste AWS-Infrastruktur mit OpenTofu

**Erweiterung ab November 2026:** Die aktuelle Web-Konsole, Port 8080,
S3-State-Migration und Release-Deployments sind in [CLOUD.md](../CLOUD.md)
dokumentiert. Die folgenden Abschnitte beschreiben den ursprünglichen IaC-Auftrag.

Dieses Lernprojekt stellt eine Amazon-Linux-2023-Instanz mit SSH-Zugang bereit.
Die Java-Anwendung wird noch nicht installiert. Es werden keine IAM-Rollen,
VPCs, NAT Gateways, Load Balancer oder CI/CD-Deployments erstellt.

## Bestand und Aufbau

Bei der Umsetzung vorgefunden: Java 25, Gradle Wrapper, JUnit/AssertJ, JaCoCo,
PIT, GitHub-Actions-Workflows und ein Java-Devcontainer mit veröffentlichtem
GHCR-Image. Anwendung, Tests, Workflows und Devcontainer bleiben unverändert.
AWS CLI 2.27.33 ist auf dem Windows-Host verfügbar. OpenTofu war nicht im PATH.

| Datei | Aufgabe |
| --- | --- |
| `versions.tf` | OpenTofu-Version und offizieller Provider `hashicorp/aws` |
| `providers.tf` | Region und gemeinsame Tags, keine Credentials |
| `variables.tf` | Typisierte Eingaben, Prüfung von SSH-CIDR und öffentlichem Schlüssel |
| `main.tf` | Bestehendes Subnetz und AMI lesen; Key Pair, Security Group und EC2 erstellen |
| `outputs.tf` | Instance ID, öffentliche IP, DNS und SSH-Befehl |
| `terraform.tfvars.example` | Sichere Vorlage für lokale Einstellungen |
| `.terraform.lock.hcl` | Nach `init`: genaue Provider-Version und Prüfsummen, gehört in Git |

## Grundlagen

Infrastructure as Code (IaC) beschreibt den gewünschten Zustand der Infrastruktur
in versionierbaren Dateien. OpenTofu vergleicht Konfiguration, State und AWS und
berechnet daraus Änderungen. Das erleichtert Wiederholbarkeit und Code-Reviews.

OpenTofu ist ein unter der MPL 2.0 entwickelter Open-Source-Fork von Terraform.
Beide verwenden HCL und ähnliche Workflows; neuere Funktionen können abweichen.
Dieses Projekt wird mit `tofu` verwaltet. Nicht zwischen Werkzeugen und
State-Versionen wechseln, ohne die Kompatibilität zu prüfen.

Ein **Provider** übersetzt HCL in API-Aufrufe, hier für AWS. Eine **Resource**
verwaltet ein Objekt, etwa `aws_instance`. Eine **Data Source** liest vorhandene
Objekte, hier Netzwerk und AMI. Eine **Variable** ist ein konfigurierbarer Eingang;
ein **Output** gibt ein Ergebnis aus. Der **State** ordnet die HCL-Ressourcen den
realen AWS-Objekten zu. Er liegt hier lokal in `terraform.tfstate`.

## Werkzeuge vorbereiten

Im Repository-Root befindet sich dieser Ordner `infrastructure/`.
Die folgenden PowerShell-Beispiele werden darin ausgeführt:

```powershell
cd infrastructure
tofu version
aws --version
```

Falls OpenTofu fehlt, nach den lokalen Berechtigungsregeln installieren:

```powershell
winget install --exact --id OpenTofu.Tofu
```

Danach Terminal neu öffnen und `tofu version` prüfen. AWS CLI v2 bei Bedarf mit
dem offiziellen Windows-MSI installieren. Auf Linux/Devcontainer die offiziellen
Linux-Anleitungen verwenden. Der vorhandene Java-Devcontainer enthält diese
Werkzeuge nicht; seine Änderung ist für diesen Auftrag nicht nötig. Im Container
müssen Credentials und Schlüssel separat ausserhalb des Repositories verfügbar
sein; ein Windows-SSH-Pfad ist darin nicht automatisch erreichbar.

Installationsquellen:
[OpenTofu Windows](https://opentofu.org/docs/intro/install/windows/),
[OpenTofu Linux/Standalone](https://opentofu.org/docs/intro/install/standalone/),
[AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

## Learner Lab und Credentials

1. Lab starten und warten, bis es bereit ist.
2. In den Lab-Details die tatsächlich zugelassenen Regionen und Instanztypen prüfen.
   `eu-central-1` und `t2.micro` sind Vorgaben, keine Zusicherung des Labs.
   Falls nötig beispielsweise `us-east-1` oder `t3.micro` lokal konfigurieren.
3. Die temporären Lab-Credentials ausschliesslich ausserhalb des Repositories
   ablegen, zum Beispiel in `~/.aws/credentials`:

```ini
[learner-lab]
aws_access_key_id = <Access Key aus dem Lab>
aws_secret_access_key = <Secret Key aus dem Lab>
aws_session_token = <Session Token aus dem Lab>
```

Das sind Platzhalter, keine echten Zugangsdaten. Die Datei mit restriktiven
Dateirechten schützen. Nicht im Editor-Chat, in Logs oder Screenshots teilen.
Alternativ unterstützt der Provider die Umgebungsvariablen `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY` und `AWS_SESSION_TOKEN`. Keine echten Werte in eingecheckte
Skripte schreiben; bei temporären Credentials ist der Session Token erforderlich.

```powershell
$env:AWS_PROFILE = 'learner-lab'
$env:AWS_DEFAULT_REGION = 'eu-central-1' # an Lab und terraform.tfvars angleichen
aws sts get-caller-identity
```

Alte AWS-Credential-Umgebungsvariablen können das Profil übersteuern: vor der
Nutzung prüfen, ohne deren Werte auszugeben. Abgelaufene Credentials vollständig
erneuern. Die Konfiguration erstellt keine IAM-Ressourcen und umgeht keine
Lab-Beschränkungen.

## SSH-Schlüssel und lokale Variablen

Schlüssel im persönlichen SSH-Verzeichnis erzeugen, niemals im Repository.
Bei vorhandener Datei einen anderen Namen wählen, nicht überschreiben.
Eine Passphrase verwenden:

```powershell
New-Item -ItemType Directory -Force "$HOME/.ssh" | Out-Null
ssh-keygen -t ed25519 -a 64 -f "$HOME/.ssh/tictactest_ed25519" -C 'TicTacTest Learner Lab'
Copy-Item terraform.tfvars.example terraform.tfvars
```

Unter Linux/macOS stattdessen `mkdir -p ~/.ssh` und `cp` verwenden; danach
`chmod 600 ~/.ssh/tictactest_ed25519`. Unter Windows die privaten Dateirechte
auf das eigene Benutzerkonto beschränken, falls OpenSSH zu offene Rechte meldet.
Amazon Linux unterstützt Ed25519. Nur die `.pub`-Datei wird mittels
`aws_key_pair.ssh` an AWS übermittelt. Der private Schlüssel bleibt lokal und
wird weder von OpenTofu gelesen noch erzeugt.

In `terraform.tfvars` mindestens `allowed_ssh_cidr` durch die eigene öffentliche
IPv4-Adresse mit `/32` ersetzen, etwa aus den Netzwerk-/Routerinformationen.
Die Beispieladresse `203.0.113.10/32` ist nicht für echte Verbindungen nutzbar.
Bei VPN oder wechselnder IP muss die tatsächlich sichtbare Ausgangsadresse
verwendet und ein erneuter Plan erstellt werden. Andere CIDR-Grössen werden
abgewiesen. Einen abweichenden öffentlichen Schlüsselpfad ebenfalls eintragen.

Ohne `subnet_id` liest OpenTofu das Default-VPC und wählt anhand der sortierten
IDs ein vorhandenes Default-Subnetz. Vor dem Deployment prüfen, ob dessen
Routing eine Route `0.0.0.0/0` zu einem Internet Gateway enthält und die Network
ACL SSH und Antwortverkehr erlaubt. Die öffentliche IP allein reicht nicht.
Alternativ `subnet_id` auf ein vorhandenes öffentliches Lab-Subnetz setzen;
die Security Group wird automatisch im zugehörigen VPC erstellt. Fehlt ein
geeignetes Netz, Lab-Anleitung/Lehrperson konsultieren. Es wird keines erstellt.
Öffentliche DNS-Namen setzen aktivierte DNS-Unterstützung und DNS-Hostnamen im
VPC voraus; andernfalls kann die IP für SSH verwendet werden.

## Workflow und Freigabe

```powershell
tofu fmt -recursive
tofu init
tofu validate
tofu plan -out=review.tfplan
tofu show review.tfplan
```

`init` lädt den Provider und schreibt dessen Lockdatei. `validate` prüft Struktur
und Provider-Schema; es bestätigt keine AWS-Berechtigungen oder Erreichbarkeit.
`plan` benötigt gültige Credentials, einen öffentlichen Schlüssel und gültige
Eingaben. Für die erste Bereitstellung werden drei verwaltete Ressourcen erwartet:

- Ein EC2-Key-Pair aus dem lokalen öffentlichen Schlüssel.
- Eine Security Group mit SSH nur von der konfigurierten `/32` und IPv4-Egress.
- Eine EC2-Instanz mit öffentlicher IPv4 und einem verschlüsselten 8-GiB-gp3-
  Rootvolume, das beim Löschen der Instanz mitgelöscht wird.

Das Rootvolume wird innerhalb der Instanzressource verwaltet. VPC, Subnetz und
Amazon-Linux-AMI werden nur gelesen. Die AMI wird regionsabhängig über den
Amazon-Eigentümer und den Namen von Amazon Linux 2023 x86_64 mit Kernel 6.1
ermittelt. Eine neue AMI kann bei späteren Plänen einen Instanzersatz auslösen:
Plan auf Löschungen/Ersatz und Kosten prüfen. IMDSv2 ist vorgeschrieben.

**`apply` und `destroy` erst nach ausdrücklicher Freigabe des Benutzers ausführen.**
Nach Prüfung und Freigabe des konkreten Plans:

```powershell
tofu apply review.tfplan
tofu output
```

Ein gespeicherter Plan wird ohne erneute interaktive Bestätigung angewendet.
Deshalb erst nach Freigabe ausführen. Nach Änderungen an Konfiguration oder
Eingaben einen neuen Plan erstellen und erneut prüfen. Keine Plan-Datei teilen.

## SSH-Verbindung testen

```powershell
tofu output -raw public_ipv4
tofu output -raw ssh_command
$instanceIp = tofu output -raw public_ipv4
Test-NetConnection -ComputerName $instanceIp -Port 22
ssh -i "$HOME/.ssh/tictactest_ed25519" "ec2-user@$instanceIp"
```

Bei einem abweichenden privaten Schlüsselpfad den Befehl anpassen. Der Output
zeigt den dokumentierten Standardpfad. Benutzer ist für diese AMI `ec2-user`.
Beim ersten Verbindungsaufbau den Host-Fingerprint über eine vertrauenswürdige
Quelle, etwa die EC2-Systemausgabe, abgleichen. Host-Key-Prüfung nicht abschalten.
Nach Anmeldung mit `whoami`, `hostname` und `cat /etc/os-release` prüfen, danach
`exit`. Booten kann einige Minuten dauern. Porttests auf Linux/macOS können
beispielsweise mit `nc -vz <IP> 22` erfolgen.

## Fehler im Learner Lab

| Meldung/Symptom | Vorgehen |
| --- | --- |
| `ExpiredToken` / `InvalidClientTokenId` | Lab starten, alle drei temporären Credential-Werte erneuern und Identität prüfen |
| `UnauthorizedOperation` / `AccessDenied` | Betroffene Aktion aus der Fehlermeldung festhalten, Lab-Vorgaben prüfen und Lehrperson fragen; keine Rechte umgehen |
| Kein Default-VPC / leere Subnetzliste | Vorhandenes freigegebenes öffentliches Subnetz über `subnet_id` konfigurieren |
| Instanztyp oder Region nicht erlaubt | Lab-Freigaben prüfen, erlaubte Region bzw. t2.micro/t3.micro wählen |
| Keine passende AMI | Region und EC2-DescribeImages-Berechtigung sowie aktuelle Amazon-Linux-Verfügbarkeit prüfen |
| Key-Pair-Import nicht erlaubt | Lehrperson um Freigabe der vorgesehenen Aktion bitten; keine zusätzliche IAM-Rolle erstellen |
| Timeout bei SSH | Lab/Instanzstatus, aktuelle IP, `/32`, Routing, Internet Gateway und NACL prüfen |
| `Permission denied (publickey)` | `ec2-user`, passenden privaten Schlüssel und registrierten öffentlichen Schlüssel prüfen |

Plan und Bereitstellung waren nach ausdrücklicher Freigabe erfolgreich. Es liegen
keine beobachteten AWS-Berechtigungsfehler vor. Bei einem späteren Fehler nur Aktion,
Fehlercode und anonymisierten Kontext dokumentieren, keine Credentials.

## Git und Sicherheit

In Git gehören die `.tf`-Dateien, diese Anleitung, die Beispielvariablen und
`.terraform.lock.hcl`. Die bisherige `.gitignore` ignoriert allgemein versteckte
Dateien; für die Lockdatei wurde deshalb eine ausdrückliche Ausnahme ergänzt.
Die bestehenden Regeln bleiben erhalten.

Nicht in Git: `.terraform/`, Lock-Info für laufende Operationen, State samt
Backups, gespeicherte Pläne, lokale `.tfvars`/`.tfvars.json`, AWS-Credentials,
Session Tokens, private Schlüssel und lokale Secret-Dateien. `.gitignore`
schützt nur nicht erfasste Dateien und ist kein Credential-Scanner. Vor Commits
`git diff --cached` lokal prüfen; echte Secrets bei versehentlicher Veröffentlichung
sofort widerrufen/erneuern und die Git-Historie bereinigen.

State und Plan können sensible Attributwerte enthalten, selbst wenn Outputs
als sensibel markiert sind. Lokal mit restriktiven Zugriffsrechten und ausserhalb
öffentlicher Freigaben sichern; nicht löschen, solange Ressourcen existieren.
Dieses Repository liegt unter OneDrive: lokale States, Pläne und Variablen können
trotz `.gitignore` synchronisiert werden. Für echte Deployments vorzugsweise
einen Checkout ausserhalb synchronisierter Ordner verwenden. Ein gemeinsam
gesicherter Remote-State mit Zugriffskontrolle und Locking ist eine spätere
Erweiterung und wird hier nicht angelegt.

Ein weltweit offener SSH-Port ermöglicht ständige Anmeldeversuche und vergrössert
die Angriffsfläche. Hier wird nur die einzelne vertrauenswürdige IPv4 zugelassen.
Ausgehender IPv4-Verkehr ist für DNS und Updates freigegeben; weitere eingehende
Ports werden nicht geöffnet.

## Kostenkontrolle und Löschen

Auch kleine Instanzen können Kosten verursachen. EC2-Laufzeit, EBS-Speicher,
öffentliche IPv4-Adressen und Datentransfer sind nicht automatisch kostenlos.
Lab-Guthaben und Budgetanzeigen regelmässig prüfen; nur eine kleine Instanz
verwenden und Testressourcen nach der Nutzung entfernen. Stoppen allein entfernt
das EBS-Volume nicht. Keine Kostenfreiheit aufgrund des Namens `micro` annehmen.

Zuerst einen Löschplan prüfen:

```powershell
tofu plan -destroy -out=destroy.tfplan
tofu show destroy.tfplan
```

Erst nach ausdrücklicher Freigabe entweder den geprüften Löschplan mit
`tofu apply destroy.tfplan` anwenden oder `tofu destroy` ausführen und den dort
erneut angezeigten Plan prüfen/bestätigen. `destroy` entfernt die von diesem
State verwalteten Ressourcen einschliesslich Rootvolume; gespeicherte Daten
gehen verloren. Bestehende Netzwerke werden nicht gelöscht. Anschliessend in der
AWS-Konsole kontrollieren, dass keine Testinstanz oder zugehörigen Volumes mehr
vorhanden sind. Die Credentials müssen auch zum Löschen gültig sein.

## Ausblick

Später kann die Anwendung containerisiert und auf der Instanz gestartet werden.
Das bestehende Konsolenspiel benötigt für eine Online-Anwendung zunächst eine
geeignete Webschnittstelle. Darauf aufbauend sind automatisierte Deployments
aus einer Registry und eine CI/CD-Pipeline mit geprüften Plänen möglich.
Für dev, staging und prod sind getrennte States, Ressourcen und geeignete
Zugriffskontrollen nötig; ein anderes Environment-Tag allein trennt sie nicht.
Diese Erweiterungen sind hier ausschliesslich dokumentiert.

## Durchgeführte Prüfungen (28. Oktober 2026)

- OpenTofu 1.13.2 für Windows temporär ausserhalb des Repositories geladen;
  ZIP-Prüfsumme mit der veröffentlichten SHA-256-Liste verglichen. Keine
  Systeminstallation oder PATH-Änderung vorgenommen.
- `tofu fmt -check -recursive`: erfolgreich.
- `tofu init -backend=false`: erfolgreich; signierter AWS-Provider 6.70.0 geladen
  und `.terraform.lock.hcl` erzeugt.
- `tofu validate`: erfolgreich, einschliesslich Prüfung gegen das Provider-Schema.
- `git diff --check`: erfolgreich. Git-Ausschlüsse für State, Pläne, lokale
  Variablen, private Schlüssel und Arbeitsverzeichnis geprüft; Beispiel und
  Provider-Lockdatei sind nicht ausgeschlossen.
- Im aktuell von Git erfassten Dateibestand keine Treffer bei einer Mustersuche
  nach typischen AWS-Key-IDs, Credential-Zuweisungen und privaten PEM-/OpenSSH-
  Schlüsseln. Das ist keine vollständige Prüfung aller Secret-Formate oder der
  gesamten Git-Historie.

Nach Vorbereitung von lokalen Variablen, SSH-Schlüssel und Lab-Credentials wurde
ein gespeicherter Plan geprüft: drei Ressourcen erstellen, keine Änderungen oder
Löschungen. Nach ausdrücklicher Benutzerfreigabe wurde dieser Plan erfolgreich
angewendet: EC2-Instanz, Key Pair und Security Group in `us-east-1` erstellt.
Der TCP-Verbindungstest auf Port 22 der öffentlichen Instanz-IP war erfolgreich.
Der Benutzer hat die SSH-Anmeldung mit seinem privaten Schlüssel erfolgreich
getestet: `whoami` lieferte `ec2-user`, `/etc/os-release` bestätigte Amazon Linux
2023 (Version 2023.12.20261026). `destroy` wurde nicht ausgeführt. State, Plan und lokale Variablen
werden wie vorgesehen von Git ausgeschlossen. Die unveränderten
Java-Tests wurden für diese reine Infrastruktur-Ergänzung nicht erneut gestartet.
Für weitere Aufrufe `tofu` regulär installieren; die temporäre Prüfkopie ist
kein dauerhaft eingerichtetes Entwicklungswerkzeug.

Technische Referenzen: [AWS-Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs),
[Amazon Linux 2023 AMIs](https://docs.aws.amazon.com/linux/al2023/ug/ec2.html),
[EC2-Schlüsselpaare](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html).
