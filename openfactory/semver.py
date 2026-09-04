"""Tiny semver helper for the prod version picker — show the current version and
suggest the next patch/minor/major bump (the panel lets the approver pick or edit)."""

from __future__ import annotations

import re
from functools import total_ordering
from typing import Any

# Regex to match valid SemVer components (ignores v prefix, captures major, minor, patch, prerelease, build)
_V = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

def _cmp_prerelease(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return 1
    if not b:
        return -1

    parts_a = a.split('.')
    parts_b = b.split('.')

    for pa, pb in zip(parts_a, parts_b):
        if pa == pb:
            continue

        pa_is_num = pa.isdigit()
        pb_is_num = pb.isdigit()

        if pa_is_num and pb_is_num:
            return 1 if int(pa) > int(pb) else -1
        elif pa_is_num:
            return -1
        elif pb_is_num:
            return 1
        else:
            return 1 if pa > pb else -1

    return 1 if len(parts_a) > len(parts_b) else -1


@total_ordering
class Version:
    def __init__(self, major: int, minor: int, patch: int, prerelease: str = "", build: str = ""):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease
        self.build = build

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        return _cmp_prerelease(self.prerelease, other.prerelease) < 0

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        if self.build:
            base += f"+{self.build}"
        return base

    def __repr__(self) -> str:
        return f"Version({self.major}, {self.minor}, {self.patch}, {self.prerelease!r}, {self.build!r})"

    def __iter__(self):
        # Support tuple unpacking for backward compatibility with existing code: `maj, mi, pa = parse(version)`
        yield self.major
        yield self.minor
        yield self.patch


def parse(tag: str | None) -> Version:
    m = _V.search(tag or "")
    if m:
        return Version(
            int(m.group("major")),
            int(m.group("minor")),
            int(m.group("patch")),
            m.group("prerelease") or "",
            m.group("build") or ""
        )
    return Version(0, 0, 0)


def _fmt(maj: int, mi: int, pa: int) -> str:
    return f"{maj}.{mi}.{pa}"


def bump(version: str | None, part: str) -> str:
    v = parse(version)
    if part == "major":
        return _fmt(v.major + 1, 0, 0)
    if part == "minor":
        return _fmt(v.major, v.minor + 1, 0)
    return _fmt(v.major, v.minor, v.patch + 1)


def suggest(latest: str | None) -> dict[str, str]:
    return {
        "current": _fmt(*parse(latest)),
        "patch": bump(latest, "patch"),
        "minor": bump(latest, "minor"),
        "major": bump(latest, "major"),
    }
