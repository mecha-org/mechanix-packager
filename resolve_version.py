#!/usr/bin/env python3
"""Resolves the next release number for a package.

Usage:
    python3 /path/to/mechanix-packager/resolve_version.py --format rpm

Prints JSON to stdout: {"package_name", "format", "upstream_version", "release"}
Falls back to release "1" if Pulp is unreachable or unauthenticated.
"""

import argparse
import base64
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from packagers.nfpm import read_package_name  # noqa: E402
from common import read_upstream_version  # noqa: E402

log = logging.getLogger("resolve_version")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


def resolve_release(pkg_name: str, upstream: str, fmt: str, base_url: str) -> str:
    endpoint = (
        f"{base_url}/pulp/api/v3/content/deb/packages/?package={pkg_name}"
        if fmt == "deb"
        else f"{base_url}/pulp/api/v3/content/rpm/packages/?name={pkg_name}"
    )

    headers = {"Accept": "application/json"}
    username = os.environ.get("MECHA_PULP_USERNAME", "")
    password = os.environ.get("MECHA_PULP_PASSWORD", "")
    if username and password:
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"

    try:
        request = urllib.request.Request(endpoint, headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        log.warning("Pulp unavailable for %s (%s); falling back to release 1", fmt, exc)
        return "1"

    versions = [
        pkg["version"] if fmt == "deb" else f"{pkg['version']}-{pkg['release']}"
        for pkg in payload.get("results", [])
    ]
    revisions = [
        int(v.rsplit("-", 1)[1])
        for v in versions
        if v.startswith(f"{upstream}-") and v.rsplit("-", 1)[1].isdigit()
    ]
    next_release = (max(revisions) if revisions else 0) + 1
    log.info("Resolved %s release: %s-%s", fmt, upstream, next_release)
    return str(next_release)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--format", required=True, choices=["rpm", "deb"])
    parser.add_argument("--name", default=None, help="Defaults to the name in packaging/nfpm/nfpm.yaml")
    parser.add_argument("--upstream", default=None, help="Defaults to the version in pubspec.yaml")
    parser.add_argument("--base-url", default=None, help="Defaults to the MECHA_PULP_API_URL env var")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)

    base_url = (args.base_url or os.environ.get("MECHA_PULP_API_URL", "")).strip().rstrip("/")
    if not base_url:
        raise SystemExit("No Pulp base URL configured. Set the MECHA_PULP_API_URL env var or pass --base-url.")

    pkg_name = args.name or read_package_name()
    upstream = args.upstream or read_upstream_version()
    release = resolve_release(pkg_name, upstream, args.format, base_url)

    print(json.dumps({
        "package_name": pkg_name,
        "format": args.format,
        "upstream_version": upstream,
        "release": release,
    }))


if __name__ == "__main__":
    main()
