# Devcontainer: Build, Freigabe und Versions-PR

## Architektur

`.devcontainer/Dockerfile` definiert Temurin Java 25 auf Ubuntu Noble,
Gradle 9.7.0 und vscode mit UID/GID 1000. Ubuntu/glibc unterstuetzt die
Node-Laufzeit der GitHub Actions. VS Code verwendet das freigegebene GHCR-Image;
CI nutzt dasselbe Image mit root fuer die vom Runner gemounteten Verzeichnisse.

`.devcontainer/IMAGE_VERSION` ist die zentrale offizielle Container-Version.
Der CI-Job configuration validiert sie und liefert den Image-Namen an
build-and-test. `.devcontainer/devcontainer.json` wird beim Release synchron
aktualisiert. Die Anwendungsdatei VERSION ist davon unabhaengig.

## Automatisierung in container.yml

| Ausloeser | Job und Ergebnis |
| --- | --- |
| PR mit Container-/Workflow-Aenderungen | validate testet Versionsskript und Docker-Build, ohne Upload |
| Push auf main | candidate testet das Skript, baut und veroeffentlicht ein SHA-Image auf GHCR; danach Java, Gradle und UID/GID-Pruefung |
| Veroeffentlichtes Release devcontainer-vMAJOR.MINOR.PATCH | publish validiert Tag, main-Zugehoerigkeit und steigende Version, testet den Container mit dem Projekt und veroeffentlicht das gepruefte Image |
| Manueller Workflow-Start | validate baut zur Kontrolle, ohne Veroeffentlichung |

Nach dem offiziellen Push wird das Image anhand seines Digests gestartet.
Ein Versions-Branch aktualisiert IMAGE_VERSION und devcontainer.json.
Der Workflow erstellt genau einen PR pro Version und startet dessen CI explizit,
weil mit GITHUB_TOKEN erstellte PRs selbst keine weiteren Workflows ausloesen.
Er wartet auf den CI-Lauf fuer exakt den Commit des Versions-PRs. Merge erfolgt
erst nach den aktiven erforderlichen Checks; kein automatischer Bypass.

Versions-PRs brauchen keine Workflow-Aenderung: Die CI liest die zentrale Datei.
Das Standard-GITHUB_TOKEN darf Workflow-Dateien nicht umschreiben. Das erste
reale Release 1.0.2 zeigte diese Grenze nach erfolgreichem Image-Push. Die
Korrektur in PR #8 und das anschliessende Release 1.0.3 erproben den Ablauf.
Bereits veroeffentlichte Image-Versionen werden nicht ueberschrieben.

## Einmalige GitHub-Einrichtung

- Das Repository muss Actions ausfuehren und ins verknuepfte GHCR-Package schreiben duerfen.
- Actions muss Pull Requests erstellen duerfen (bereits aktiviert).
- Main-Ruleset verlangt configuration, build-and-test und infrastructure-tests.
- Die Jobs erhalten nur ihre benoetigten Rechte: packages:write fuer Upload,
  contents:write und pull-requests:write fuer den Versions-PR sowie actions:write fuer den expliziten CI-Start.

Der GHCR-Login im Workflow verwendet GITHUB_TOKEN. Entwickler benoetigen fuer
den privaten Package-Pull eine eigene GHCR-Anmeldung mit Leserechten. Keine
Tokens ins Repository schreiben. Die oeffentliche Repository-Sichtbarkeit
macht das GHCR-Package nicht automatisch oeffentlich.

## Freigabe durchfuehren

Zuerst Dockerfile-Aenderungen per geprueftem PR nach main uebernehmen.
Dann einen neuen annotierten Tag erstellen und pushen, beispielsweise:

```sh
git switch main
git pull --ff-only
git tag -a devcontainer-v1.0.4 -m "Devcontainer v1.0.4"
git push origin devcontainer-v1.0.4
```

Auf GitHub ein regulaeres Release fuer diesen Tag veroeffentlichen. Den
Container-Workflow und den automatisch erzeugten Versions-PR kontrollieren.
Erst nach gruener CI mergen. Entwickler ziehen danach main und verwenden
in VS Code Rebuild Container. Aktuelle Freigaben und Links stehen in ABGABE.md.

## Lokale und reale Nachweise

Lokal wurden Docker-Build, Java 25.0.4.1, Gradle 9.7.0, UID/GID 1000:1000 und
ein frischer Linux-Build mit 112 Tests, 100 % Branch-Coverage und 79/79
PIT-Mutationen geprueft. Fuenf Python-Tests und actionlint bestanden ebenfalls.
Das von GitHub veroeffentlichte Image 1.0.2 wurde authentifiziert heruntergeladen
und gestartet; der Release-Workflow pruefte es zuvor bereits per Digest.

Fuer reproduzierbare Vergleiche Basisimage und JDK-Patchstand beachten: Der
Dockerfile verwendet einen beweglichen Basisimage-Tag. SemVer-Tags werden
vom Workflow nicht erneut veroeffentlicht, sind aber kein Registry-seitiges
Unveraenderlichkeitsversprechen. Ein Fehler nach dem Image-Push kann deshalb
einen roten Lauf trotz vorhandenen Images ergeben; mit neuer Patchversion
korrigieren und die nachfolgenden PR-/CI-Schritte erneut nachweisen.
