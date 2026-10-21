# TicTacTest - Abgabe und Nachweise

Abgabe: 25. Oktober 2026, 23:59 Uhr (Europe/Zurich). Bewertet wird der zum
Abgabetermin gepushte Stand auf main. Muendliches Code-Review:
28. Oktober oder 4. November, 10-15 Minuten. Notebook mit Abgabestand mitbringen.

## Projekt und Konzepte

- [Repository](https://github.com/Philip222111/450-tictactest-mvk)
- [Testkonzept und Technologien](TESTKONZEPT.md)
- [Release- und Versionierungskonzept](RELEASE.md)
- [Devcontainer und automatisierte Freigabe](CONTAINER_BUILD_WORKFLOW.md)
- [Coverage-Zeitreihe mit Architekturdiagramm](COVERAGE.md)
- [PR-Gates und Main-Ruleset](BRANCH_PROTECTION.md)
- [Vorbereitung auf das Code-Review](PRUEFUNG.md)

## Technische Abnahme am 21. Oktober 2026

112 Testausfuehrungen, 100 % Branch-Coverage, 79/79 erkannte PIT-Mutationen;
fuenf Python-Infrastrukturtests, actionlint und der JAR-Smoke-Test bestanden.
SonarLint Language Server 6.1.1.79808 analysierte alle 13 Java-Dateien ohne
offene Findings. Die gezielten Ausnahmen fuer Konsolen-UI und JVM-main-Argument
sind direkt im Code und im Testkonzept begruendet.

- [Umsetzungs-PR #7](https://github.com/Philip222111/450-tictactest-mvk/pull/7)
- [Automations- und SonarLint-Korrektur #8](https://github.com/Philip222111/450-tictactest-mvk/pull/8)
- [CI-Laeufe und Berichtsartefakte](https://github.com/Philip222111/450-tictactest-mvk/actions/workflows/ci.yml)
- [Coverage-Verlauf](https://philip222111.github.io/450-tictactest-mvk/coverage-history/index.html)
- [Aktueller Detailbericht](https://philip222111.github.io/450-tictactest-mvk/report/index.html)
- [Dauerhafte Messdaten](https://github.com/Philip222111/450-tictactest-mvk/blob/coverage-history/coverage-history/history.json)
- [Anwendungsrelease 1.1.0 mit JAR und SHA-256](https://github.com/Philip222111/450-tictactest-mvk/releases/tag/v1.1.0)
- [Devcontainer-Release 1.0.3](https://github.com/Philip222111/450-tictactest-mvk/releases/tag/devcontainer-v1.0.3)
- [Container-Workflows](https://github.com/Philip222111/450-tictactest-mvk/actions/workflows/container.yml)

Das aktive Main-Ruleset verlangt PRs, die Checks configuration, build-and-test
und infrastructure-tests sowie einen aktuellen Branch und geloeste
Review-Kommentare. Lineare Historie ist vorgeschrieben; Force-Push und
Loeschen sind gesperrt. Fremde Freigaben sind fuer die Einzelarbeit nicht noetig.

## Bewusste Abweichung

Das Repository bleibt auf ausdruecklichen Wunsch oeffentlich. Die formale
Anforderung einer privaten Abgabe ist damit nicht erfuellt. Die persoenliche
muendliche Pruefung und eine eventuell notwendige Einreichung auf Teams fuehren
die Lernenden selbst durch. Der technische Projektstand ersetzt diese nicht.

- [Anwendungsrelease mit erneutem Download- und Starttest](https://github.com/Philip222111/450-tictactest-mvk/actions/runs/39577400974) erfolgreich.
- [Automatischer Versions-PR #9](https://github.com/Philip222111/450-tictactest-mvk/pull/9) aktualisiert VS Code und CI auf das gepruefte GHCR-Image v1.0.3.
