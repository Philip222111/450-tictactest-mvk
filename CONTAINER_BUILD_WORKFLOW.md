# Automatischer Devcontainer-Build und Release

Der Workflow [`.github/workflows/container.yml`](.github/workflows/container.yml)
prüft die Container-Definition und veröffentlicht offizielle Versionen in der
GitHub Container Registry (GHCR).

## Validierung

Bei Pull Requests, relevanten Änderungen auf `main` und manuellen Starts wird
das Alpine-Dockerfile für `linux/amd64` gebaut, aber nicht gepusht. Fehler an
Java 25, Gradle oder der Dockerfile-Syntax werden dadurch vor einer Freigabe
erkannt. Ein normaler Branch kann weder `latest` noch `stable` verändern.

## Offizielle Freigabe

1. Devcontainer-Änderungen per Pull Request nach `main` bringen.
2. Einen neuen SemVer-Wert gemäß [DEVCONTAINER.md](DEVCONTAINER.md) wählen.
3. In GitHub unter **Releases → Draft a new release** einen Tag wie
   `devcontainer-v1.0.0` auf dem betreffenden `main`-Commit erstellen.
4. Das Release veröffentlichen.

Nur das Ereignis `release: published` startet den Registry-Upload. Der
Workflow kontrolliert Tagformat und Zugehörigkeit zu `main`, meldet sich mit
dem automatisch bereitgestellten `GITHUB_TOKEN` bei GHCR an und veröffentlicht
SemVer-, `stable`-, `latest`- und SHA-Tags.

Das resultierende Image wird anhand seines unveränderlichen Digests wieder
heruntergeladen. `java -version` und `gradle --version` müssen erfolgreich
sein, bevor der Ablauf fortgesetzt wird.

## Automatische Übernahme

Nach erfolgreicher Prüfung führt
`scripts/update_devcontainer_version.py vX.Y.Z` zwei kontrollierte Änderungen
aus: `.devcontainer/devcontainer.json` wird auf den unveränderlichen
SemVer-Tag des neuen GHCR-Images gesetzt. Die CI referenziert dauerhaft
`stable`; dieser Tag wird bereits beim geprüften Release atomar auf dieselben
Image-Inhalte aktualisiert. Dadurch muss der Workflow seine eigene
Workflow-Datei nicht verändern.

Der Workflow committet diese Änderungen auf
`automation/devcontainer-vX.Y.Z` und eröffnet einen Pull Request nach `main`.
Reviews und Branch Protection bleiben dadurch wirksam. Erst nach erfolgreicher
CI und Merge wird die neue Version zur lokalen Standardumgebung des
Repositorys; die CI nutzt sie bereits über den freigegebenen `stable`-Tag.

## Berechtigungen

Die Validierung benötigt `contents: read`. Nur der Release-Job erhält:

- `packages: write` für GHCR,
- `contents: write` für den Aktualisierungsbranch,
- `pull-requests: write` für den Pull Request.

Zusätzlich muss das Repository in den Package-Einstellungen Schreibzugriff auf
das GHCR-Package besitzen. Persönliche Tokens gehören nicht ins Repository.

## Manuelle Erstveröffentlichung

Der historische `latest`-Upload erfüllte die manuelle Erstveröffentlichung.
Neue Versionen werden nicht mehr von Hand überschrieben, sondern ausschließlich
über den beschriebenen Releaseprozess publiziert. Falls ein lokaler Nachweis
benötigt wird, kann das Image nach `docker login ghcr.io` gebaut und mit
`docker push` hochgeladen werden; Zugangsdaten werden dabei interaktiv
bereitgestellt und niemals dokumentiert.
