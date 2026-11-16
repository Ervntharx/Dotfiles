#!/usr/bin/env python3
"""Batch-copy configured sources into data/."""

from __future__ import annotations

import fnmatch
import os
import shutil
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_ROOT / "dotfile_refer.yaml"
DATA_ROOT = PROJECT_ROOT / "data"


def load_config() -> tuple[list[Path], list[str]]:
    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    sources = [Path(source).expanduser() for source in config["sources"]]
    blacklist = config["blacklist"]
    return sources, blacklist


def archive_target(source: Path) -> Path:
    return DATA_ROOT / source.relative_to("/")


def is_blacklisted(relative: Path, patterns: list[str]) -> bool:
    path_text = relative.as_posix()
    return any(
        fnmatch.fnmatchcase(path_text, pattern)
        or fnmatch.fnmatchcase(relative.name, pattern)
        or any(fnmatch.fnmatchcase(part, pattern) for part in relative.parts)
        for pattern in patterns
    )


def copy_source(source: Path, blacklist: list[str]) -> Path:
    target = archive_target(source)
    target.parent.mkdir(parents=True, exist_ok=True)

    if source.is_symlink():
        if target.is_file() or target.is_symlink():
            target.unlink()
        os.symlink(os.readlink(source), target)
    elif source.is_dir():
        def ignore(directory: str, names: list[str]) -> set[str]:
            parent = Path(directory).relative_to(source)
            return {
                name
                for name in names
                if is_blacklisted(parent / name, blacklist)
            }

        shutil.copytree(
            source,
            target,
            dirs_exist_ok=True,
            symlinks=True,
            copy_function=shutil.copy2,
            ignore=ignore,
        )
    else:
        shutil.copy2(source, target)

    return target


def run() -> int:
    try:
        sources, blacklist = load_config()
    except Exception as exc:
        print(f"ERROR: cannot load dotfile_refer.yaml: {exc}", file=sys.stderr)
        return 1

    failed_sources: list[Path] = []
    succeeded = 0

    for source in sources:
        if not os.path.lexists(source):
            print(f"ERROR: source not found: {source}", file=sys.stderr)
            failed_sources.append(source)
            continue

        try:
            target = copy_source(source, blacklist)
        except Exception as exc:
            print(
                f"ERROR: backup task failed: {source}: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            failed_sources.append(source)
            continue

        succeeded += 1
        print(f"OK: {source} -> {target}")

    print(
        "SUMMARY: "
        f"total_copy_tasks={len(sources)}, "
        f"succeeded={succeeded}, "
        f"failed={len(failed_sources)}"
    )
    print("FAILED SOURCES:")
    if failed_sources:
        for source in failed_sources:
            print(f"  {source}")
    else:
        print("  none")

    return 1 if failed_sources else 0


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("ERROR: sync.py does not accept arguments", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run())
