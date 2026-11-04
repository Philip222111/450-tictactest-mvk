# TicTacTest in der Cloud

Die drei Aufträge sind im Code vorbereitet. AWS-Apply, manuelles Deployment und
der erste echte Actions-Lauf müssen mit gültigem AWS-Konto durchgeführt werden.
Die separaten Auftragsdateien aus Teams lagen bei der Umsetzung nicht vor;
Grundlage ist der übermittelte Auftragstext. Zusätzliche Bewertungskriterien
aus diesen Dateien gegebenenfalls abgleichen.

## 1. Unverändertes Release-JAR lokal im Browser

Die Java-Quellen bleiben unverändert. Python startet für jedes Spiel
`java -jar …`, leitet Eingaben an stdin und Ausgaben aus stdout zum Browser.
Kein Nachbau der Spiellogik, keine Änderung am Release-Artefakt. Die Konsole
entfernt lediglich ANSI-Farbcodes für die Darstellung. Acht parallele Spiele,
je maximal 48 MB Java-Heap; inaktive Sitzungen werden nach fünf Minuten entfernt.
Ein Neustart des Dienstes beendet laufende Spiele.

Im Repository-Root in PowerShell (Python 3.9+ und Java 25 erforderlich):

```powershell
New-Item -ItemType Directory -Force artifacts
$tag = 'v1.1.0'
gh release download $tag --dir artifacts --pattern "tictactest-$($tag.Substring(1)).jar" --pattern '*.sha256'
$jar = "artifacts/tictactest-$($tag.Substring(1)).jar"
$expected = ((Get-Content "$jar.sha256") -split '\s+')[0]
if ((Get-FileHash $jar -Algorithm SHA256).Hash.ToLower() -ne $expected) { throw 'Falsche Prüfsumme' }
java -version
python web/server.py --jar $jar
```

Browser: <http://127.0.0.1:8080>. Neues Spiel starten, Position 0–8 eingeben.
Beenden mit Ctrl+C. Das Originalspiel beendet sich bei belegten Positionen;
dann ein neues Spiel starten. Das ist das Verhalten des unveränderten JARs.
Falls `java -version` Java 17 zeigt, Java 25 in PATH aufnehmen oder vor dem Start
`$env:JAVA = 'C:\Pfad\zu\jdk-25\bin\java.exe'` setzen.
Alternativ zum Release-Download für Entwicklung: `./gradlew.bat jar` und
`python web/server.py --jar build/libs/tictactest-1.1.0.jar`.

## 2. Bestehende EC2 erweitern und von Hand deployen

Die bisherige IaC-Anleitung bleibt unter [infrastructure/README.md](infrastructure/README.md).
Die Erweiterung öffnet TCP 8080; SSH bleibt auf die konfigurierte /32 beschränkt.
Die Installation erfolgt bewusst separat vom EC2-Boot, damit die bestehende
Instanz weiterverwendet werden kann. Keine neue IAM-Rolle erforderlich.

1. AWS Learner Lab starten. Die drei aktuellen Credential-Werte in deinem
   lokalen AWS-Profil `learner-lab` hinterlegen, inklusive Session Token.
2. PowerShell im Repository öffnen:

```powershell
$env:AWS_PROFILE = 'learner-lab'
aws sts get-caller-identity
tofu -chdir=infrastructure init
tofu -chdir=infrastructure plan -out=web.tfplan
```

3. Plan prüfen: vorgesehen ist die zusätzliche Security-Group-Regel und Outputs.
   Falls EC2 ersetzt werden soll: nicht anwenden; insbesondere AMI-Auswahl prüfen.
   `ami_id` muss in den lokalen tfvars auf die AMI der bestehenden Instanz zeigen.
   Das Image wird explizit festgelegt, damit neue Images keine Ersetzung auslösen.
   Bestehenden State niemals löschen oder mit einem leeren State neu beginnen.
4. Geprüften Plan anwenden und Dateien übertragen (Release unter `artifacts/`
   wie in Schritt 1 herunterladen):

```powershell
tofu -chdir=infrastructure apply web.tfplan
$ec2Host = tofu -chdir=infrastructure output -raw public_ipv4
$key = "$env:USERPROFILE/.ssh/tictactest_ed25519"
ssh -i $key "ec2-user@$ec2Host" 'mkdir -p ~/tictactest-upload'
scp -i $key -r web deploy artifacts "ec2-user@${ec2Host}:tictactest-upload/"
ssh -i $key "ec2-user@$ec2Host" 'cd ~/tictactest-upload && sudo bash deploy/install.sh'
tofu -chdir=infrastructure output -raw web_url
```

5. Ausgegebene URL im Browser öffnen, vollständige Partie spielen und neu starten.
   Auf EC2 prüfen: `sudo systemctl status tictactest` und
   `sudo journalctl -u tictactest -n 30`. Amazon Linux 2023 benötigt ausgehenden
   Internetzugang für die Pakete. Das Skript installiert Corretto 25 und Python,
   prüft die JAR-Prüfsumme und richtet einen Dienst mit eigenem Benutzer ein.

Dies ist eine HTTP-Unterrichtsdemo auf Port 8080 ohne Anmeldung. Keine sensiblen
Daten eingeben. Für eingeschränkten Zugriff `web_allowed_cidrs` in tfvars setzen;
dann denselben Wert in Actions über `TF_VAR_web_allowed_cidrs` konfigurieren.
Öffentlicher Produktionsbetrieb braucht zusätzlich TLS und Zugriffsschutz.

## 3. Gemeinsamen OpenTofu-State einmalig einrichten

Actions muss denselben State wie dein PC verwenden. Dazu einen privaten S3-Bucket
in derselben Region erstellen. Das gehört vor den ersten automatischen Lauf.

1. AWS-Konsole → S3 → Bucket erstellen. Global eindeutigen Namen wählen,
   beispielsweise `tictactest-state-DEINE-EINDEUTIGE-ID`.
2. Region an die bestehende EC2 anpassen. „Alle öffentlichen Zugriffe blockieren“
   aktiviert lassen, Versionierung aktivieren, Standardverschlüsselung SSE-S3.
3. In PowerShell im Repository-Root:

```powershell
Copy-Item infrastructure/backend.tf.example infrastructure/backend.tf
tofu -chdir=infrastructure init -migrate-state -backend-config="bucket=DEIN-BUCKET" -backend-config="region=us-east-1"
tofu -chdir=infrastructure state list
tofu -chdir=infrastructure plan
```

4. Die Migration des vorhandenen lokalen States bestätigen. Die Ressourcenliste
   muss die bisherige Instanz, Security Group und Key Pair enthalten. Bei einem
   Plan, der alles neu erstellen möchte: stoppen, Bucket/Key und Migration prüfen.
   `backend.tf` bleibt lokal; Actions erstellt dieselbe Datei aus der Vorlage.
   Ab dann für lokale Applies ebenfalls diesen Backend verwenden.

Erforderliche Rechte: S3 Bucket auflisten, State lesen/schreiben, Lockdatei
lesen/schreiben/löschen; EC2 lesen/verwalten und Security-Group-Regeln
erstellen/löschen. Im Learner Lab hängen diese Rechte von den Lab-Vorgaben ab.
Bei AccessDenied die konkrete Meldung mit der Lehrperson abklären.

## 4. GitHub einmalig konfigurieren

Repository → Settings → Environments → New environment → `production`.
Dort Secrets und Variables hinterlegen. Werte niemals in den Code schreiben.

| Typ | Name | Inhalt |
| --- | --- | --- |
| Secret | `AWS_ACCESS_KEY_ID` | aktueller AWS Access Key |
| Secret | `AWS_SECRET_ACCESS_KEY` | aktueller AWS Secret Key |
| Secret | `AWS_SESSION_TOKEN` | aktueller Lab Session Token; bei langfristigen Keys leer lassen |
| Secret | `EC2_SSH_KEY` | kompletter privater Schlüssel für die bestehende EC2 |
| Secret | `EC2_PUBLIC_KEY` | komplette zugehörige ursprüngliche `.pub`-Datei, inklusive Kommentar |
| Secret | `EC2_KNOWN_HOSTS` | verifizierter known_hosts-Eintrag der EC2-IP |
| Variable | `AWS_REGION` | Region aus deinen lokalen tfvars, z. B. `us-east-1` |
| Variable | `AMI_ID` | dieselbe festgelegte `ami_id` wie lokal; für die bestehende Instanz `ami-0952e94e8e3ae87bf` in `us-east-1` |
| Variable | `SSH_CIDR` | dieselbe vertrauenswürdige /32 wie lokal |
| Variable | `TOFU_STATE_BUCKET` | Name des oben erstellten Buckets |
| Variable | `INSTANCE_TYPE` | derselbe Typ wie lokal, z. B. `t2.micro` |
| Variable | `INSTANCE_NAME` | derselbe Name wie lokal, standardmässig `tictactest-dev` |
| Variable | `SUBNET_ID` | nur bei lokal explizit gesetztem Subnetz erforderlich |

Abweichende lokale Variablen wie `environment` auch im Workflow als `TF_VAR_…`
übernehmen. Der private Schlüssel muss für unbeaufsichtigtes SSH ohne interaktive
Passworteingabe nutzbar sein. Öffentlichen Schlüssel exakt übernehmen, damit
OpenTofu keinen unnötigen Austausch des Key Pairs plant.

Host-Key prüfen: Über die bereits verifizierte SSH-Verbindung auf EC2
`sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` ausführen. Lokal
`ssh-keygen -F DEINE-EC2-IP` zeigt den gespeicherten Eintrag. Fingerprint mit
`ssh-keygen -lf "$env:USERPROFILE/.ssh/known_hosts"` vergleichen und den passenden
Eintrag als `EC2_KNOWN_HOSTS` hinterlegen. Nicht blind `ssh-keyscan` vertrauen.
Bei geänderter IP oder ersetzter EC2 diesen Eintrag neu verifizieren.

Die temporären Lab-Credentials laufen ab. Vor späteren Releases alle drei
AWS-Secrets erneuern und sicherstellen, dass das Lab und die Instanz laufen.

## 5. Automatisches Deployment auslösen

Änderungen inklusive des bisher unversionierten `infrastructure/`-Ordners und
dessen Lockdatei in Git aufnehmen, prüfen und auf main bringen. State, tfvars,
Pläne, private Schlüssel und Release-Downloads bleiben ausgeschlossen.

Für das nächste Release den bestehenden Prozess aus [RELEASE.md](RELEASE.md)
verwenden: VERSION und CHANGELOG aktualisieren, Tag `vMAJOR.MINOR.PATCH` pushen.
Der Release-Workflow testet/baut das JAR und veröffentlicht es. Anschliessend
ruft er `deploy.yml` direkt als wiederverwendbaren Workflow auf. Ein mit
GITHUB_TOKEN erzeugtes Release startet normalerweise keinen neuen Workflow;
deshalb reicht der zusätzliche `release: published`-Trigger allein nicht.
Manuell veröffentlichte Releases werden ebenfalls unterstützt.

Zum ersten Test: Actions → Deploy release → Run workflow → einen Release-Tag
angeben, der bereits diese Dateien enthält. Ein altes Release vor dieser
Implementierung kann noch nicht deployt werden, weil dessen Git-Stand weder
Web-Konsole noch Deploy-Skripte enthält.

Was „nur geändert“ bedeutet:

- OpenTofu plant bei jedem Release gegen den gemeinsamen State. Es wendet nur
  die tatsächlichen Unterschiede an; Löschungen/Ersetzungen blockiert Actions.
- `rsync -rc --itemize-changes` vergleicht Inhalte statt Zeitstempel und
  überträgt nur geänderte Dateien. Das Ziel ist ausschliesslich der Uploadordner.
- Das Installationsskript vergleicht nochmals per `cmp`. Bei identischen
  Dateien erfolgt kein Neustart; bei Änderungen an JAR, Web oder Service schon.
- Neue JAR-Versionen werden als originale Release-Dateien heruntergeladen und
  per SHA-256 geprüft; es findet kein Neubau im Deployment statt.
- Die IP des jeweiligen GitHub-Runners erhält vorübergehend SSH-Zugang /32.
  Der abschliessende Schritt entfernt genau diese Regel auch bei Fehlern.
  Bei hart abgebrochenen Runnern in AWS nach einer verbliebenen Regel schauen.

Erstinstallation überträgt alles. Reine Dokumentationsänderungen bei identischem
JAR verursachen keinen Neustart. Ein neues VERSION-Feld verändert den
JAR-Manifestinhalt und rechtfertigt daher ein JAR-Update. Infrastruktur- und
Dateiprüfungen laufen trotzdem; „unverändert“ bedeutet keine Ressourcenänderung
und keine erneute Nutzdatenübertragung.

## 6. Nachweise und Fehlerdiagnose

- Lokal: vollständiges Spiel, zweites getrenntes Spiel, Neustart und ungültige
  Eingabe prüfen. Screenshot der Browserkonsole erstellen.
- Cloud: URL und erfolgreiche Partie, `systemctl status`, Actions-Protokoll
  mit Plan und rsync-Ausgabe dokumentieren. Keine Credentials fotografieren.
- Dasselbe Release erneut deployen: `No changes` und keine geänderten Nutzdateien;
  Dienststartzeit mit `systemctl show tictactest -p ActiveEnterTimestamp` vergleichen.
- Nur HTML ändern und neues Release erstellen: HTML wird aktualisiert; aufgrund
  neuer Versionsnummer kann auch das JAR abweichen. Bei unverändertem JAR bleibt
  dessen Inhalt unverändert. Nur IaC ändern: Plan zeigt die konkrete Änderung.
- SSH-Fehler: Lab läuft? IP korrekt? CIDR/temporäre Regel vorhanden? Host-Key korrekt?
- Healthcheck scheitert: Journal prüfen, Corretto-25-Pfad prüfen, Paketinstallation
  und `artifacts`-Prüfsumme kontrollieren.
- Fehlgeschlagenes Datei-Deployment: gewünschten bisherigen Release-Tag erneut
  über Actions deployen. Das ist kein automatisches Infrastruktur-Rollback.

## Technische Quellen

Lokal geprüft am 4. November 2026: Gradle `build` inklusive Java-Tests und
Coverage-Gate erfolgreich; HTTP-Integrationstest mit echtem JAR erfolgreich
(vollständige Partie, getrennte Sitzungen, ungültiger Zug, unbekannte Sitzung).
OpenTofu `fmt -check` und `validate`, YAML-Parsing und `git diff --check`
erfolgreich. AWS-Apply, Linux-Service und GitHub-Deployment sind noch nicht
im echten Cloud-Betrieb getestet.

Integrationstest wiederholen (Java 25 muss über `JAVA` oder PATH verfügbar sein):

```powershell
$env:TEST_JAR = (Resolve-Path build/libs/tictactest-1.1.0.jar).Path
python -m unittest discover -s web -p test_server.py
```

- [OpenTofu S3-Backend und native Sperrdatei](https://opentofu.org/docs/language/settings/backends/s3/)
- [GitHub Workflow-Ereignisse](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Corretto 25 auf Amazon Linux 2023](https://docs.aws.amazon.com/corretto/latest/corretto-25-ug/amazon-linux-install.html)
