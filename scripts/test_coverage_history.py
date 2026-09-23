import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from coverage_history import read_coverage, update


class CoverageHistoryTest(unittest.TestCase):
    def test_history_preserves_commits_and_deduplicates_reruns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / 'report.xml'
            report.write_text('''<report><package><counter type="INSTRUCTION" covered="999" missed="0"/></package>
                <counter type="INSTRUCTION" covered="3" missed="1"/>
                <counter type="BRANCH" covered="1" missed="1"/></report>''')
            site = root / 'site'
            with patch.dict(os.environ, COVERAGE_COMMIT='a' * 40, COVERAGE_RUN='10'):
                update(report, site)
                update(report, site)
            with patch.dict(os.environ, COVERAGE_COMMIT='b' * 40, COVERAGE_RUN='11'):
                update(report, site)
            with patch.dict(os.environ, COVERAGE_COMMIT='c' * 40, COVERAGE_RUN='9'):
                update(report, site)
            history = json.loads((site / 'coverage-history/history.json').read_text())
            self.assertEqual(len(history), 3)
            self.assertEqual([point['run_id'] for point in history], [9, 10, 11])
            self.assertEqual(history[1]['instruction'], 75)
            self.assertEqual(history[1]['branch'], 50)
            self.assertEqual(history[1]['commit'], 'a' * 40)
            self.assertIn('Branch coverage', (site / 'coverage-history/index.html').read_text())
            # Corrupt historical data must fail instead of silently resetting history.
            (site / 'coverage-history/history.json').write_text('invalid')
            with patch.dict(os.environ, COVERAGE_COMMIT='d' * 40, COVERAGE_RUN='12'):
                with self.assertRaises(json.JSONDecodeError):
                    update(report, site)

    def test_no_branches_and_empty_report(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / 'report.xml'
            report.write_text('<report><counter type="INSTRUCTION" covered="0" missed="8"/></report>')
            self.assertEqual(read_coverage(report), {'instruction': 0, 'branch': None})
            report.write_text('<report/>')
            with self.assertRaises(ValueError):
                read_coverage(report)


if __name__ == '__main__':
    unittest.main()
