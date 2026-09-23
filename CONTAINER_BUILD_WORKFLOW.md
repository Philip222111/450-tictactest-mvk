# Container automatisch bauen und veröffentlichen

Der Workflow [container.yml](.github/workflows/container.yml) baut das CI-Image
und das interaktive Devcontainer-Image und veröffentlicht beide in der GitHub
Container Registry. Er läuft auf einem Ubuntu-Runner und benötigt deshalb kein
bereits vorhandenes Projekt-Image zum Starten.

## Auslöser

- Push mit Änderungen unter `.github/container/`, `.devcontainer/` oder an
  `.github/workflows/container.yml`, auf jedem Branch.
- Manueller Start über `workflow_dispatch`.

Für den manuellen Start in der GitHub-Oberfläche muss der Workflow zunächst auf dem Standardbranch vorhanden sein. Danach unter **Actions → Container bauen und veröffentlichen → Run workflow** den gewünschten Branch auswählen. Auf dem Entwicklungsbranch wurde der erste Lauf durch den Push der Workflow-Datei ausgelöst.

## Vorgefertigte Actions

| Action | Aufgabe |
| --- | --- |
| `actions/checkout@v4` | Quellstand auschecken |
| `docker/setup-buildx-action@v4` | Docker-Buildx-Builder einrichten |
| `docker/login-action@v4` | Bei `ghcr.io` anmelden |
| `docker/build-push-action@v7` | Image bauen und veröffentlichen |

Der CI-Build verwendet `.github/container/Dockerfile` mit dem Kontext
`.github/container`. Der Devcontainer-Build verwendet `.devcontainer/Dockerfile`
mit dem Repository als Kontext. Beide Builds zielen auf `linux/amd64`. `pull:
true` prüft die Basisimages auf Aktualisierungen; `no-cache: true` führt die
Build-Schritte neu aus.

## Tags und Prüfung

Jeder erfolgreiche Upload veröffentlicht je zwei Tags:

```text
ghcr.io/philip222111/450-tictactest-mvk:latest
ghcr.io/philip222111/450-tictactest-mvk:sha-<vollständige Commit-SHA>
ghcr.io/philip222111/450-tictactest-mvk-devcontainer:latest
ghcr.io/philip222111/450-tictactest-mvk-devcontainer:sha-<vollständige Commit-SHA>
```

`latest` wird bei jedem veröffentlichten Build ersetzt, auch bei einem Start auf einem Entwicklungsbranch. Die bestehende Test-Pipeline verwendet diesen Tag bei ihrem nächsten Container-Start. Ein parallel bereits gestarteter Testlauf verwendet möglicherweise noch das vorherige Image.

Anschliessend lädt der Veröffentlichungsworkflow beide Images anhand ihrer
Digests herunter und führt jeweils `java -version` aus. Beide Digests erscheinen
in der Zusammenfassung des Workflow-Laufs. Diese Prüfung bestätigt Download und
Java-Start; die Projekttests bleiben Aufgabe von `ci.yml`.

Die gemeinsame Concurrency-Gruppe verhindert gleichzeitig laufende Veröffentlichungsjobs dieses Workflows. Ein laufender Upload wird durch einen neuen Start nicht abgebrochen.

## Berechtigungen

Der Workflow verwendet `GITHUB_TOKEN` mit `contents: read` und `packages: write`. Ein persönlicher Token als Repository-Secret ist nicht notwendig. Zusätzlich muss das Repository beim bestehenden privaten Package unter **Package settings → Manage Actions access** die Rolle **Write** besitzen. Die bisherige Rolle **Read** genügt nur für die Test-Pipeline.

## Nachweis

Der erste automatische Lauf für das CI-Image (Commit `424d1f9`) am 9. September
2026 ist [erfolgreich abgeschlossen](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/34344842658).
Build, Veröffentlichung der beiden CI-Tags, Digest-Download und Java-Start waren
erfolgreich. Das zusätzliche Devcontainer-Image wird erstmals durch einen Lauf
der erweiterten Workflow-Version veröffentlicht; dessen Ergebnis ist separat im
zugehörigen Actions-Lauf zu prüfen.

## Quellen

- Docker: [Docker Build GitHub Actions](https://docs.docker.com/build/ci/github-actions/).
- Docker: [Manage tags and labels with GitHub Actions](https://docs.docker.com/build/ci/github-actions/manage-tags-labels/).
- GitHub: [Package-Zugriff und Sichtbarkeit](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).
