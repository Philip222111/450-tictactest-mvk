# PR-Gates und Schutz von main

Der erforderliche Check `build-and-test` fuehrt JUnit, jqwik, Pioneer,
JaCoCo (mindestens 90 % Branch-Coverage) und PIT aus. PIT hat keinen eigenen
Mindestscore; der Bericht macht ueberlebende Mutationen sichtbar.
`infrastructure-tests` prueft Coverage-Historie und Versionsaktualisierung.
Beide Jobs laufen bei jedem PR, ohne Pfadfilter. Der optionale Containercheck
ist wegen seines Pfadfilters kein erforderlicher Statuscheck.

## Schutzregeln

Die vorbereitete `.github/branch-protection.json` verlangt PRs, einen aktuellen
Branch mit beiden erfolgreichen Checks, geloeste Review-Kommentare und lineare
Historie. Force-Push und Loeschen von main sind gesperrt; Administratoren sind
eingeschlossen. Als Einzelarbeit werden null fremde Freigaben verlangt: eine
verbindliche fremde Freigabe wuerde den alleinigen Autor blockieren. Im Team
wird die Anzahl auf mindestens eins erhoeht. Merge per Squash verwenden.

Die Datei allein aktiviert keine GitHub-Regel. Mit GitHub CLI und Adminrechten:

```sh
gh api --method PUT repos/Philip222111/450-tictactest-mvk/branches/main/protection --input .github/branch-protection.json
gh api repos/Philip222111/450-tictactest-mvk/branches/main/protection
```

Vor Anwendung bestehende Regeln lesen und mit der Vorlage vergleichen, damit
strengere vorhandene Regeln erhalten bleiben. Private Repositories brauchen
fuer Branch Protection einen unterstuetzten GitHub-Tarif. Ein API-Fehler ist
kein Nachweis einer aktiven Regel. Das aktive GitHub-Ruleset Main setzt diese Regeln fuer den Default-Branch um.
Am 21. Oktober 2026 wurden beide Pflichtchecks, Aktualitaetspruefung und
Review-Kommentaraufloesung per API kontrolliert beziehungsweise aktiviert.
Die JSON-Datei bleibt eine alternative Vorlage fuer klassische Branch Protection;
auf diesem Repository wird das Ruleset verwendet.

Abnahme: PR mit fehlschlagendem Test muss gesperrt sein; nach Korrektur und
erfolgreichen Checks muss Squash-Merge moeglich sein. Dies erst nach dem finalen
Push pruefen. Ein bloss gruener Workflow ohne Schutzregel erzwingt keinen Gate.

API-Referenz: https://docs.github.com/en/rest/branches/branch-protection
