"""Tests for the automatic Devcontainer version update."""

import json
import tempfile
import unittest
from pathlib import Path

from update_devcontainer_version import IMAGE, update


class UpdateDevcontainerVersionTest(unittest.TestCase):
    """Verify synchronized, validated updates without touching the repository."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary_directory.name)
        (self.repository / ".devcontainer").mkdir()
        (self.repository / ".github" / "workflows").mkdir(parents=True)
        (self.repository / ".devcontainer" / "devcontainer.json").write_text(
            json.dumps({"name": "test", "build": {"dockerfile": "Dockerfile"}}),
            encoding="utf-8",
        )
        (self.repository / ".github" / "workflows" / "ci.yml").write_text(
            f"jobs:\n  test:\n    container:\n      image: {IMAGE}:v1.0.0\n",
            encoding="utf-8",
        )
        (self.repository / ".github" / "workflows" / "unrelated.yml").write_text(
            "name: unrelated\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_updates_every_released_image_consumer(self) -> None:
        changed = update("v1.2.3", self.repository)
        configuration = json.loads(
            (self.repository / ".devcontainer" / "devcontainer.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("build", configuration)
        self.assertEqual(f"{IMAGE}:v1.2.3", configuration["image"])
        self.assertEqual(
            "v1.2.3\n",
            (self.repository / ".devcontainer" / "IMAGE_VERSION").read_text(
                encoding="utf-8"
            ),
        )
        self.assertIn(
            f"{IMAGE}:v1.2.3",
            (self.repository / ".github" / "workflows" / "ci.yml").read_text(
                encoding="utf-8"
            ),
        )
        self.assertEqual(3, len(changed))

    def test_is_idempotent_and_does_not_touch_unrelated_workflows(self) -> None:
        update("v1.2.3", self.repository)
        self.assertEqual([], update("v1.2.3", self.repository))
        self.assertEqual(
            "name: unrelated\n",
            (self.repository / ".github" / "workflows" / "unrelated.yml").read_text(
                encoding="utf-8"
            ),
        )

    def test_rejects_mutable_or_invalid_versions(self) -> None:
        for version in ("latest", "stable", "1.2.3", "v01.2.3", "v1.2"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                update(version, self.repository)


if __name__ == "__main__":
    unittest.main()
