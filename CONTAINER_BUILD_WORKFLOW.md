# Container automatisch bauen und veröffentlichen

Der Workflow [container.yml](.github/workflows/container.yml) baut das eigene CI-Image und veröffentlicht es in der GitHub Container Registry. Er läuft auf einem Ubuntu-Runner und benötigt deshalb kein bereits vorhandenes CI-Image zum Starten.

## Auslöser

- Push mit Änderungen unter `.github/container/` oder an `.github/workflows/container.yml`, auf jedem Branch.
- Manueller Start über `workflow_dispatch`.

Für den manuellen Start in der GitHub-Oberfläche muss der Workflow zunächst auf dem Standardbranch vorhanden sein. Danach unter **Actions → Container bauen und veröffentlichen → Run workflow** den gewünschten Branch auswählen. Auf dem Entwicklungsbranch wurde der erste Lauf durch den Push der Workflow-Datei ausgelöst.

## Vorgefertigte Actions

| Action | Aufgabe |
| --- | --- |
| `actions/checkout@v4` | Quellstand auschecken |
| `docker/setup-buildx-action@v4` | Docker-Buildx-Builder einrichten |
| `docker/login-action@v4` | Bei `ghcr.io` anmelden |
| `docker/build-push-action@v7` | Image bauen und veröffentlichen |

Der Build verwendet `.github/container/Dockerfile` mit dem Kontext `.github/container` und der Plattform `linux/amd64`. `pull: true` prüft das Basisimage auf Aktualisierungen; `no-cache: true` führt die Build-Schritte neu aus.

## Tags und Prüfung

Jeder erfolgreiche Upload veröffentlicht zwei Tags:

```text
ghcr.io/philip222111/450-tictactest-mvk:latest
ghcr.io/philip222111/450-tictactest-mvk:sha-<vollständige Commit-SHA>
```

`latest` wird bei jedem veröffentlichten Build ersetzt, auch bei einem Start auf einem Entwicklungsbranch. Die bestehende Test-Pipeline verwendet diesen Tag bei ihrem nächsten Container-Start. Ein parallel bereits gestarteter Testlauf verwendet möglicherweise noch das vorherige Image.

Anschliessend lädt der Veröffentlichungsworkflow das neue Image anhand seines Digests herunter und führt darin `java -version` aus. Der Digest erscheint in der Zusammenfassung des Workflow-Laufs. Diese Prüfung bestätigt Download und Java-Start; die Projekttests bleiben Aufgabe von `ci.yml`.

Die gemeinsame Concurrency-Gruppe verhindert gleichzeitig laufende Veröffentlichungsjobs dieses Workflows. Ein laufender Upload wird durch einen neuen Start nicht abgebrochen.

## Berechtigungen

Der Workflow verwendet `GITHUB_TOKEN` mit `contents: read` und `packages: write`. Ein persönlicher Token als Repository-Secret ist nicht notwendig. Zusätzlich muss das Repository beim bestehenden privaten Package unter **Package settings → Manage Actions access** die Rolle **Write** besitzen. Die bisherige Rolle **Read** genügt nur für die Test-Pipeline.

## Nachweis

Der erste automatische Lauf für Commit `424d1f9` am 9. September 2026 ist [erfolgreich abgeschlossen](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/34344842658). Build, Veröffentlichung beider Tags, Download anhand des Digests und Java-Start im veröffentlichten Image waren erfolgreich. Damit sind die benötigten Schreibrechte praktisch bestätigt.

## Quellen

- Docker: [Docker Build GitHub Actions](https://docs.docker.com/build/ci/github-actions/).
- Docker: [Manage tags and labels with GitHub Actions](https://docs.docker.com/build/ci/github-actions/manage-tags-labels/).
- GitHub: [Package-Zugriff und Sichtbarkeit](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).
