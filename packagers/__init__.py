"""Packager registry - the extension point for a new packaging format.

A packager module exposes:
    FORMATS: list[str]
    build(fmt, version, release, arch, output_dir, staged_bundle) -> None
        Raises SystemExit on failure.

Add a new format: write packagers/<name>.py implementing that, register it
below. package.py and common.py don't change.
"""

from . import nfpm as _nfpm

_REGISTERED = [_nfpm]


def resolve(fmt: str):
    for packager in _REGISTERED:
        if fmt in packager.FORMATS:
            return packager
    supported = sorted({f for packager in _REGISTERED for f in packager.FORMATS})
    raise SystemExit(f"No packager registered for format '{fmt}'. Supported: {', '.join(supported)}")
