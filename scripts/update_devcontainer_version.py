"""Update every consumer to one already published Devcontainer release."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


IMAGE = "ghcr.io/philip222111/450-tictactest-mvk-devcontainer"
SEMVER = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
IMAGE_REFERENCE = re.compile(rf"{re.escape(IMAGE)}:([^\s\"']+)")


def update(version: str, repository: Path) -> list[Path]:
    """Pin the version file, local Devcontainer, and all workflow consumers."""
    if not SEMVER.fullmatch(version):
        raise ValueError("Version must use the form v1.2.3")

    changed: list[Path] = []
    version_path = repository / ".devcontainer" / "IMAGE_VERSION"
    _write_if_changed(version_path, f"{version}\n", changed)

    devcontainer_path = repository / ".devcontainer" / "devcontainer.json"
    configuration = json.loads(devcontainer_path.read_text(encoding="utf-8"))
    configuration.pop("build", None)
    configuration["image"] = f"{IMAGE}:{version}"
    _write_if_changed(
        devcontainer_path,
        json.dumps(configuration, indent=4, ensure_ascii=False) + "\n",
        changed,
    )

    workflows = repository / ".github" / "workflows"
    for workflow in sorted((*workflows.glob("*.yml"), *workflows.glob("*.yaml"))):
        text = workflow.read_text(encoding="utf-8")
        if IMAGE not in text:
            continue
        updated = IMAGE_REFERENCE.sub(f"{IMAGE}:{version}", text)
        _write_if_changed(workflow, updated, changed)

    return changed


def _write_if_changed(path: Path, content: str, changed: list[Path]) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        changed.append(path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: update_devcontainer_version.py v1.2.3")
    root = Path(__file__).resolve().parents[1]
    for changed_path in update(sys.argv[1], root):
        print(changed_path.relative_to(root).as_posix())
