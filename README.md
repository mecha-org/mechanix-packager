# mechanix-packager

Shared packaging tooling for Mechanix apps. Currently builds RPM and DEB
(via [nfpm](https://nfpm.goreleaser.com)).

Each app repo (`mechanix-clock`, `mechanix-files`, ...) stays fully
independent - this tool is installed separately and invoked *from* an
app repo's root.

## Structure

```text
package.py           CLI entrypoint: resolves version/arch, stages the
                      build bundle, dispatches each requested format to
                      its packager
resolve_version.py    Standalone package release resolver (rpm/deb version)
common.py             helpers: repo root, upstream version
                      (pubspec.yaml or Cargo.toml), finding/staging the
                      flutter-elinux bundle
packagers/
  __init__.py         The packager contract + registry
  nfpm.py             rpm, deb, apk, archlinux - all via nfpm
```

## Install

Download and extract a tagged release:

```sh
curl -fsSL -o mechanix-packager.tar.gz \
  https://github.com/mecha-org/mechanix-packager/archive/refs/tags/v0.0.1.tar.gz
mkdir -p mechanix-packager && tar -xzf mechanix-packager.tar.gz -C mechanix-packager --strip-components=1
```

## Use

Run it *from the app repo's root*, it resolves everything (pubspec.yaml or
Cargo.toml, packaging/nfpm/nfpm.yaml, the build output) relative to app's
current working directory.

```sh

# version from pubspec.yaml/Cargo.toml, release defaults to "1"
python3 /path/to/mechanix-packager/package.py

# CI / fetch the next release number:
python3 /path/to/mechanix-packager/resolve_version.py --format rpm
python3 /path/to/mechanix-packager/package.py --formats rpm --release "$RELEASE"
```

## Contract an app repo must follow

- `pubspec.yaml` (flutter-elinux apps) or `Cargo.toml` (Rust apps) at the
  repo root, with a `version:`/`version = "..."` field.
- `packaging/nfpm/nfpm.yaml` - the nfpm config. Its `name:` field is what
  the nfpm packager and `resolve_version.py` use as the package name.
- `packaging/nfpm/scripts/` - launcher/postinstall/postremove scripts
  referenced from `nfpm.yaml`, if any.
- flutter-elinux apps: a `build/elinux/*/release/bundle` directory to
  package, before running `package.py` - it gets staged to a fixed
  `./stage/bundle` path since nfpm.yaml can't reference a variable one.
- Cargo apps: build output lands at a fixed `target/.../release/<bin>`
  path already, so `nfpm.yaml` references it directly.
`nfpm.yaml`'s actual content (binary name, maintainer,
description, dependencies, whether a desktop entry/icon exist yet) - is
actual per-app data and will be maintained in each app repo.
