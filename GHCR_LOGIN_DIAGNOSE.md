# GHCR-Login: Diagnose und Behebung

## Ergebnis

Der Login mit `docker login ghcr.io -u Philip222111` wurde mit `denied: denied` abgelehnt. Bei der Passwortabfrage wurde das GitHub-Kontopasswort eingegeben. Damit ist eine konkrete Ursache bestätigt: Für den manuellen Registry-Zugriff verlangt GitHub einen Personal Access Token (classic). Für den geplanten Upload benötigt dieser `write:packages`.[^1]

Die Registry war bei der Prüfung am 9. September 2026 aus dem Workspace erreichbar. Eine Anfrage ohne Zugangsdaten an `https://ghcr.io/v2/` lieferte HTTP 401. Dies belegt eine HTTP-Antwort, jedoch keine erfolgreiche Anmeldung und keine Schreibberechtigung.

## Anmeldung korrigieren

1. Im Browser mit dem GitHub-Konto `Philip222111` anmelden.
2. [Personal Access Token (classic) mit write:packages erstellen](https://github.com/settings/tokens/new?scopes=write:packages).
3. Eine Beschreibung wie `TicTacToe GHCR Upload` und ein passendes Ablaufdatum setzen. Den Scope `write:packages` prüfen und **Generate token** wählen.
4. Den generierten Token kopieren. GitHub zeigt ihn nur bei der Erstellung vollständig an. Ein Fine-grained Token ist für GitHub Packages derzeit nicht geeignet.[^2]
5. Im selben VS-Code-Terminal ausführen:

```bash
docker login ghcr.io -u Philip222111
```

Bei `Password:` den generierten Token einfügen und Enter drücken. Docker akzeptiert bei der Passwortabfrage einen Zugangstoken; alternativ unterstützt es `--password-stdin`.[^3] Erwartetes Ergebnis ist `Login Succeeded`.

Der Token gehört ausschliesslich in die lokale Passwortabfrage, nicht in das Repository oder in Chat-Nachrichten. Er ist wie ein Passwort zu behandeln.[^2]

## Falls der Login erneut scheitert

Zunächst prüfen, ob tatsächlich der vollständige Tokenwert eingefügt wurde, ob der Token vom Konto `Philip222111` stammt, noch gültig ist und als **classic** erstellt wurde. Ein abgelaufener oder widerrufener Token muss ersetzt werden.[^2] Danach den Login mit dem korrigierten Token wiederholen.

Ein erfolgreicher Login und ein erfolgreicher Image-Upload sind getrennte Nachweise. Scheitert erst der Upload, sind die Schreibberechtigung des Tokens und die Berechtigung für das Ziel-Package zu prüfen. Scheitert später der Download in Actions, muss das Repository Zugriff auf das Package haben; der Workflow verwendet dafür `GITHUB_TOKEN` mit `packages: read`.[^1]

## Projektstand und Abschluss

Das lokale Image `ghcr.io/philip222111/450-tictactest-mvk:latest` existiert. Seine bei der Prüfung ausgegebene ID lautet `sha256:698aac8baa7536a30fad89cf3f6288b74460a0b41bb15d31dc3e7fcefd3c2b1c`. Der bereits dokumentierte Container-Testlauf war erfolgreich: 12 Tests ohne Fehler. Die vorbereitete CI-Konfiguration liegt im lokalen Commit `9c3668c` auf `task/ghcr-container-ci`.

Die Anmeldung mit PAT (classic) ist inzwischen erfolgreich. Upload, anschliessender Pull und Branch-Push sind abgeschlossen. Der separate Package-Zugriff des Repository-Tokens wurde unter **Package settings → Manage Actions access** durch Hinzufügen von `450-tictactest-mvk` mit **Read** eingerichtet. Der [Actions-Lauf](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/34343894748) ist erfolgreich. Den Abschlussstand und die Nachweise enthält [CONTAINER_GH_ACTIONS.md](CONTAINER_GH_ACTIONS.md).

## Quellen

[^1]: GitHub, [Working with the Container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry), laufende Dokumentation, abgerufen am 9. September 2026. Manuelle Authentifizierung, Token-Scopes und Actions-Zugriff.
[^2]: GitHub, [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens), laufende Dokumentation, abgerufen am 9. September 2026. Token-Erstellung, Einschränkungen und Umgang mit Zugangsdaten.
[^3]: Docker, [docker login](https://docs.docker.com/reference/cli/docker/login/), laufende Dokumentation, abgerufen am 9. September 2026. Interaktive Anmeldung und Passwortübergabe über Standardeingabe.
