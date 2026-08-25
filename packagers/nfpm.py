"""nfpm packager"""

import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from common import REPO_ROOT

FORMATS = ["rpm", "deb", "apk", "archlinux"]

NFPM_CONFIG = REPO_ROOT / "packaging" / "nfpm" / "nfpm.yaml"

log = logging.getLogger("packagers.nfpm")


def read_package_name() -> str:
    if not NFPM_CONFIG.exists():
        raise SystemExit(f"{NFPM_CONFIG} not found - run this from an app repo's root")
    match = re.search(r"^name:\s*(\S+)", NFPM_CONFIG.read_text(), re.MULTILINE)
    if not match:
        raise SystemExit(f"No name field found in {NFPM_CONFIG}")
    return match.group(1)


def build(fmt: str, version: str, release: str, arch: str, output_dir: Path, staged_bundle: Path) -> None:
    
    if not NFPM_CONFIG.exists():
        raise SystemExit(f"{NFPM_CONFIG} not found")
    if shutil.which("nfpm") is None:
        raise SystemExit("nfpm not found on PATH. Install it: https://nfpm.goreleaser.com/install/")

    log.info("Building %s package (version %s, release %s)...", fmt, version, release)
    env = {**os.environ, "PKG_VERSION": version, "PKG_RELEASE": release, "PKG_ARCH": arch}
    result = subprocess.run(
        ["nfpm", "pkg", "--config", str(NFPM_CONFIG), "--packager", fmt, "--target", str(output_dir)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        log.debug("nfpm: %s", line)
    if result.returncode != 0:
        log.error("nfpm failed for %s:\n%s", fmt, result.stderr.strip())
        raise SystemExit(result.returncode)
    log.info("Built %s package", fmt)
