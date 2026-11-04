import unittest
from release_assets import changes


class ReleasePathsTest(unittest.TestCase):
    def test_components(self):
        self.assertEqual(changes(['frontend/style.css']), {'backend': False, 'frontend': True})
        self.assertEqual(changes(['src/main/java/Main.java']), {'backend': True, 'frontend': False})
        self.assertEqual(changes(['frontend/app.js', 'build.gradle']), {'backend': True, 'frontend': True})
        self.assertEqual(changes(['VERSION', 'CHANGELOG.md', 'docs/deployment.md']), {'backend': False, 'frontend': False})
        self.assertEqual(changes(['deploy/deploy.yml']), {'backend': True, 'frontend': True})
