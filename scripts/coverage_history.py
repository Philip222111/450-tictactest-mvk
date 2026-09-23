"""Build a static coverage timeline using only the Python standard library."""

import json
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def read_coverage(report):
    """Liest die aggregierte Instruction- und Branch-Coverage aus JaCoCo-XML."""
    # Nur Zähler direkt unter <report> verwenden; Paket-/Klassenzähler wären doppelt.
    counters = {c.attrib['type']: c.attrib for c in ET.parse(report).getroot().findall('counter')}
    result = {}
    for metric in ('INSTRUCTION', 'BRANCH'):
        counter = counters.get(metric, {'covered': '0', 'missed': '0'})
        covered, missed = int(counter['covered']), int(counter['missed'])
        if metric == 'INSTRUCTION' and covered + missed == 0:
            raise ValueError('JaCoCo report contains no instructions')
        result[metric.lower()] = round(100 * covered / (covered + missed), 2) if covered + missed else None
    return result


def chart(history, metric, title):
    """Erzeugt ein eigenständiges SVG-Liniendiagramm für eine Coverage-Metrik."""
    # Bei vielen Messpunkten wächst die Zeichenfläche und bleibt horizontal scrollbar.
    width = max(760, 75 * len(history))
    elements = [f'<h2>{title}</h2><div class="chart"><svg role="img" aria-label="{title}" viewBox="0 0 {width} 300" style="min-width:{width}px">']
    for value in range(0, 101, 20):
        # Feste Hilfslinien von 0 bis 100 Prozent erleichtern den Vergleich.
        y = 250 - value * 2
        elements.append(f'<path d="M50 {y} H{width-20}" stroke="#ddd"/><text x="5" y="{y+5}">{value}%</text>')
    segment = []
    for i, point in enumerate(history):
        # Die x-Position verteilt alle Commits gleichmäßig über die Zeichenfläche.
        x = 65 + i * (width - 100) / max(1, len(history) - 1)
        value = point[metric]
        if value is None:
            # Fehlende Branch-Werte unterbrechen die Linie, statt 0 % vorzutäuschen.
            if segment:
                elements.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="#159947" stroke-width="3"/>')
            segment = []
            continue
        y = 250 - value * 2
        segment.append(f'{x},{y}')
        label = escape(f'{point["date"]} · {point["commit"][:7]} · {value}%')
        elements.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#159947"><title>{label}</title></circle>')
        elements.append(f'<text x="{x}" y="280" text-anchor="middle">{escape(point["commit"][:7])}</text>')
    if segment:
        elements.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="#159947" stroke-width="3"/>')
    return ''.join(elements) + '</svg></div>'


def update(report, output):
    """Ergänzt die Historie und schreibt JSON, Diagramme sowie die HTML-Seite."""
    # Alle dauerhaft veröffentlichten Dateien liegen unter coverage-history/.
    directory = output / 'coverage-history'
    directory.mkdir(parents=True, exist_ok=True)
    data_file = directory / 'history.json'
    # Eine vorhandene Historie wird vollständig übernommen und nicht neu initialisiert.
    history = json.loads(data_file.read_text()) if data_file.exists() else []
    commit = os.environ['COVERAGE_COMMIT']
    # Ein erneuter Lauf desselben Commits darf keinen zweiten Messpunkt erzeugen.
    if not any(point['commit'] == commit for point in history):
        history.append(dict(date=datetime.now(timezone.utc).isoformat(), commit=commit,
                            run_id=int(os.environ['COVERAGE_RUN']), **read_coverage(report)))
    history.sort(key=lambda point: point['run_id'])
    data_file.write_text(json.dumps(history, indent=2) + '\n')

    # Neueste Messwerte stehen in der Tabelle oben; Diagramme bleiben chronologisch.
    rows = ''.join('<tr>' + ''.join(f'<td>{escape(str(value))}</td>' for value in (
        p['date'], p['commit'][:7], f'{p["instruction"]}%',
        'n/a' if p['branch'] is None else f'{p["branch"]}%')) + '</tr>' for p in reversed(history))
    page = '''<!doctype html><html lang="de"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TicTacToe Coverage-Verlauf</title>
<style>body{font:16px system-ui;margin:2rem auto;padding:0 1rem;max-width:1100px;color:#203028}
.chart{overflow-x:auto}svg{width:100%;font-size:12px}table{border-collapse:collapse;width:100%}
td,th{padding:.6rem;text-align:left;border-bottom:1px solid #ddd}a{color:#087534}</style>
<h1>Coverage-Verlauf auf main</h1>
<p>JaCoCo: abgedeckte / gesamte Elemente × 100. Messpunkte nach Workflow-Reihenfolge.
Ohne Branches: n/a. Details eines Messpunkts erscheinen beim Berühren mit der Maus.</p>
<p><a href="../report/index.html">Aktueller JaCoCo-Report</a> · <a href="history.json">Historie als JSON</a></p>'''
    page += chart(history, 'instruction', 'Instruction coverage')
    page += chart(history, 'branch', 'Branch coverage')
    page += '<h2>Messwerte</h2><div class="chart"><table><tr><th>Datum (UTC)</th><th>Commit</th><th>Instruction</th><th>Branch</th></tr>' + rows + '</table></div></html>'

    # Die Detailseite enthält Diagramme und Tabelle; die Root-Seite leitet dorthin um.
    (directory / 'index.html').write_text(page)
    (output / 'index.html').write_text('<!doctype html><html lang="de"><meta charset="utf-8"><title>Coverage</title><meta http-equiv="refresh" content="0;url=coverage-history/index.html"><a href="coverage-history/index.html">Coverage-Verlauf</a></html>')


if __name__ == '__main__':
    # Kommandozeilenargumente: JaCoCo-XML und Zielverzeichnis der statischen Website.
    update(Path(sys.argv[1]), Path(sys.argv[2]))
