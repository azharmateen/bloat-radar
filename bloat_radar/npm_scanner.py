"""Scan node_modules: walk directories, measure disk size, detect duplicates, find largest packages."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class NpmPackageInfo:
    """Information about an installed npm package."""

    name: str
    version: str
    size_bytes: int
    path: str
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    is_duplicate: bool = False
    duplicate_versions: list[str] = field(default_factory=list)
    file_count: int = 0


def _dir_size(path: Path) -> tuple[int, int]:
    """Calculate total size in bytes and file count for a directory."""
    total = 0
    count = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                    count += 1
                except OSError:
                    pass
    except PermissionError:
        pass
    return total, count


def _read_package_json(pkg_dir: Path) -> Optional[dict]:
    """Read and parse package.json from a directory."""
    pj = pkg_dir / "package.json"
    if pj.exists():
        try:
            with open(pj, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _find_packages_in_node_modules(nm_dir: Path) -> list[Path]:
    """Find all package directories in node_modules (handles scoped packages)."""
    packages = []
    if not nm_dir.exists():
        return packages

    for entry in sorted(nm_dir.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.name.startswith("@") and entry.is_dir():
            # Scoped package: @scope/name
            for sub in sorted(entry.iterdir()):
                if sub.is_dir() and not sub.name.startswith("."):
                    packages.append(sub)
        elif entry.is_dir():
            packages.append(entry)
    return packages


def scan_node_modules(project_dir: str, include_nested: bool = True) -> list[NpmPackageInfo]:
    """
    Scan node_modules directory and return package information.

    Args:
        project_dir: Path to the project root containing node_modules/
        include_nested: Whether to scan nested node_modules (dependency duplicates)

    Returns:
        List of NpmPackageInfo for each discovered package.
    """
    root = Path(project_dir)
    nm_dir = root / "node_modules"

    if not nm_dir.exists():
        return []

    # Collect all node_modules directories to scan
    nm_dirs = [nm_dir]
    if include_nested:
        for nested in nm_dir.rglob("node_modules"):
            if nested.is_dir():
                nm_dirs.append(nested)

    # Track all packages by name for duplicate detection
    name_versions: dict[str, list[str]] = {}
    packages: list[NpmPackageInfo] = []

    for current_nm in nm_dirs:
        for pkg_path in _find_packages_in_node_modules(current_nm):
            pj_data = _read_package_json(pkg_path)
            if pj_data is None:
                continue

            name = pj_data.get("name", pkg_path.name)
            version = pj_data.get("version", "unknown")
            description = pj_data.get("description", "")
            deps = list(pj_data.get("dependencies", {}).keys())

            size_bytes, file_count = _dir_size(pkg_path)

            pkg = NpmPackageInfo(
                name=name,
                version=version,
                size_bytes=size_bytes,
                path=str(pkg_path),
                description=description,
                dependencies=deps,
                file_count=file_count,
            )
            packages.append(pkg)

            if name not in name_versions:
                name_versions[name] = []
            name_versions[name].append(version)

    # Mark duplicates
    for pkg in packages:
        versions = name_versions.get(pkg.name, [])
        unique_versions = list(set(versions))
        if len(versions) > 1:
            pkg.is_duplicate = True
            pkg.duplicate_versions = unique_versions

    return packages


def find_largest_packages(packages: list[NpmPackageInfo], top_n: int = 20) -> list[NpmPackageInfo]:
    """Return the top N largest packages by disk size."""
    return sorted(packages, key=lambda p: p.size_bytes, reverse=True)[:top_n]


def find_duplicates(packages: list[NpmPackageInfo]) -> dict[str, list[NpmPackageInfo]]:
    """Group duplicate packages (same name, multiple installations)."""
    by_name: dict[str, list[NpmPackageInfo]] = {}
    for pkg in packages:
        if pkg.is_duplicate:
            if pkg.name not in by_name:
                by_name[pkg.name] = []
            by_name[pkg.name].append(pkg)
    return by_name


def get_scan_summary(packages: list[NpmPackageInfo]) -> dict:
    """Generate a summary of the scan results."""
    total_size = sum(p.size_bytes for p in packages)
    total_files = sum(p.file_count for p in packages)
    duplicates = find_duplicates(packages)
    duplicate_waste = sum(
        sum(p.size_bytes for p in copies[1:])
        for copies in duplicates.values()
    )

    return {
        "total_packages": len(packages),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_files": total_files,
        "duplicate_packages": len(duplicates),
        "duplicate_waste_bytes": duplicate_waste,
        "duplicate_waste_mb": round(duplicate_waste / (1024 * 1024), 2),
        "top_10_largest": [
            {"name": p.name, "version": p.version, "size_mb": round(p.size_bytes / (1024 * 1024), 2)}
            for p in find_largest_packages(packages, 10)
        ],
    }
