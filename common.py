"""Helpers shared by package.py, resolve_version.py, and every packager.

REPO_ROOT is the cwd this tool is invoked from - the app repo being
packaged.
"""

import re
import shutil
from pathlib import Path

REPO_ROOT = Path.cwd()
STAGE_DIR = REPO_ROOT / "stage"


def read_upstream_version() -> str:
    pubspec = REPO_ROOT / "pubspec.yaml"
    if pubspec.exists():
        match = re.search(r"^version:\s*(\S+)", pubspec.read_text(), re.MULTILINE)
        if not match:
            raise SystemExit(f"No version field found in {pubspec}")
        return match.group(1).split("+")[0]

    cargo_toml = REPO_ROOT / "Cargo.toml"
    if cargo_toml.exists():
        package_section = re.search(r"^\[package\](.*?)(?=^\[|\Z)", cargo_toml.read_text(), re.MULTILINE | re.DOTALL)
        if not package_section:
            raise SystemExit(f"No [package] section found in {cargo_toml}")
        match = re.search(r'^version\s*=\s*"([^"]+)"', package_section.group(1), re.MULTILINE)
        if not match:
            raise SystemExit(f"No version field found in {cargo_toml}'s [package] section")
        return match.group(1)

    raise SystemExit(f"No pubspec.yaml or Cargo.toml found in {REPO_ROOT} - run this from an app repo's root")


def find_bundle_dir() -> Path:
    matches = sorted(REPO_ROOT.glob("build/elinux/*/release/bundle"))
    if not matches:
        raise SystemExit(
            "No build bundle found under build/elinux/*/release/bundle. "
            "Run `flutter-elinux build elinux --release` first."
        )
    return matches[0]


def stage_bundle(bundle_dir: Path) -> Path:
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True)
    dest = STAGE_DIR / "bundle"
    shutil.copytree(bundle_dir, dest)
    return dest
