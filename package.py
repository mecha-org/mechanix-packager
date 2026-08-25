#!/usr/bin/env python3
"""Builds packages for apps.

Usage:
    flutter-elinux build elinux --release
    python3 /path/to/mechanix-packager/package.py                    # rpm + deb, release "1", into ./dist
    python3 /path/to/mechanix-packager/package.py ./out --formats rpm  # just rpm, into ./out
"""

import argparse
import logging
import platform
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import packagers  # noqa: E402
from common import REPO_ROOT, STAGE_DIR, find_bundle_dir, read_upstream_version, stage_bundle  # noqa: E402

log = logging.getLogger("package")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output_dir", nargs="?", default="./dist", help="Where to write the built packages")
    parser.add_argument("--formats", default="rpm,deb", help="Comma-separated list of formats to build")
    parser.add_argument("--version", default=None, help="Upstream version; defaults to pubspec.yaml")
    parser.add_argument("--release", default="1", help="Package release/revision; defaults to 1")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show each packager's own output")
    args = parser.parse_args()

    configure_logging(args.verbose)

    version = args.version or read_upstream_version()
    arch = platform.machine()
    log.info("Version: %s  Release: %s  Arch: %s", version, args.release, arch)

    staged_bundle = stage_bundle(find_bundle_dir()) if (REPO_ROOT / "pubspec.yaml").exists() else None

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        for fmt in args.formats.split(","):
            packager = packagers.resolve(fmt)
            packager.build(fmt, version, args.release, arch, output_dir, staged_bundle)
    finally:
        shutil.rmtree(STAGE_DIR, ignore_errors=True)

    log.info("Packaging complete")


if __name__ == "__main__":
    main()
