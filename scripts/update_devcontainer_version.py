"""Update all consumers to an already published Devcontainer release."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


IMAGE = "ghcr.io/philip222111/450-tictactest-mvk-devcontainer"
SEMVER = re.compile(r"^v\d+\.\d+\.\d+$")


def update(version: str, repository: Path) -> None:
    """Pin the local Devcontainer and CI to the same immutable SemVer tag."""
    if not SEMVER.fullmatch(version):
        raise ValueError("Version must use the form v1.2.3")

    devcontainer_path = repository / ".devcontainer" / "devcontainer.json"
    configuration = json.loads(devcontainer_path.read_text(encoding="utf-8"))
    configuration.pop("build", None)
    configuration["image"] = f"{IMAGE}:{version}"
    devcontainer_path.write_text(
        json.dumps(configuration, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: update_devcontainer_version.py v1.2.3")
    update(sys.argv[1], Path(__file__).resolve().parents[1])
