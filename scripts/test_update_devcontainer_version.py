"""Tests for the automatic Devcontainer version update."""

import json
import tempfile
import unittest
from pathlib import Path

from update_devcontainer_version import IMAGE, update


class UpdateDevcontainerVersionTest(unittest.TestCase):
    """Verify synchronized, validated updates without touching the repository."""

    def setUp(self) -> None:
        """Create the minimal repository layout used by the update script."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary_directory.name)
        (self.repository / ".devcontainer").mkdir()
        (self.repository / ".devcontainer" / "devcontainer.json").write_text(
            json.dumps({"name": "test", "build": {"dockerfile": "Dockerfile"}}),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        """Remove the isolated test repository."""
        self.temporary_directory.cleanup()

    def test_updates_local_image_to_released_version(self) -> None:
        """The local environment must use the released immutable SemVer tag."""
        update("v1.2.3", self.repository)

        configuration = json.loads(
            (self.repository / ".devcontainer" / "devcontainer.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("build", configuration)
        self.assertEqual(f"{IMAGE}:v1.2.3", configuration["image"])

    def test_rejects_non_semantic_version(self) -> None:
        """Mutable tags such as latest must never be selected by the updater."""
        with self.assertRaises(ValueError):
            update("latest", self.repository)


if __name__ == "__main__":
    unittest.main()
