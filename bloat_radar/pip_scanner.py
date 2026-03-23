"""Scan Python site-packages: measure installed package sizes, detect unused packages."""

from __future__ import annotations

import ast
import importlib.metadata
import os
import re
import site
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PipPackageInfo:
    """Information about an installed pip package."""

    name: str
    version: str
    size_bytes: int
    path: str
    summary: str = ""
    top_level_modules: list[str] = field(default_factory=list)
    file_count: int = 0
    is_used: Optional[bool] = None  # None = not checked


def _dir_size(path: Path) -> tuple[int, int]:
    """Calculate total size and file count for a directory."""
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
    except (PermissionError, OSError):
        pass
    return total, count


def _get_package_dirs(dist: importlib.metadata.Distribution) -> list[Path]:
    """Get the actual directories/files belonging to a distribution."""
    dirs = []
    try:
        files = dist.files
        if files:
            # Find the dist-info or egg-info directory
            dist_path = dist._path if hasattr(dist, '_path') else None
            if dist_path:
                parent = Path(dist_path).parent
            else:
                parent = None

            # Collect unique top-level directories from RECORD
            top_levels = set()
            for f in files:
                parts = f.parts
                if parts:
                    top_levels.add(parts[0])

            if parent:
                for tl in top_levels:
                    p = parent / tl
                    if p.exists():
                        dirs.append(p)
    except Exception:
        pass
    return dirs


def _get_top_level_imports(dist: importlib.metadata.Distribution) -> list[str]:
    """Get the top-level importable module names for a distribution."""
    # Try top_level.txt first
    try:
        tl = dist.read_text("top_level.txt")
        if tl:
            return [line.strip() for line in tl.strip().splitlines() if line.strip()]
    except Exception:
        pass

    # Fall back to package name normalized
    name = dist.metadata["Name"]
    if name:
        return [name.replace("-", "_").lower()]
    return []


def scan_pip_packages(site_packages_dir: Optional[str] = None) -> list[PipPackageInfo]:
    """
    Scan installed pip packages and measure their sizes.

    Args:
        site_packages_dir: Optional explicit path. If None, uses current environment's site-packages.

    Returns:
        List of PipPackageInfo for each installed distribution.
    """
    packages = []
    seen = set()

    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        if not name or name in seen:
            continue
        seen.add(name)

        version = dist.metadata["Version"] or "unknown"
        summary = dist.metadata["Summary"] or ""
        top_level = _get_top_level_imports(dist)

        # Calculate size from distribution files
        total_size = 0
        total_files = 0
        pkg_path = ""

        pkg_dirs = _get_package_dirs(dist)
        if pkg_dirs:
            pkg_path = str(pkg_dirs[0].parent)
            for d in pkg_dirs:
                if d.is_dir():
                    s, c = _dir_size(d)
                    total_size += s
                    total_files += c
                elif d.is_file():
                    try:
                        total_size += d.stat().st_size
                        total_files += 1
                    except OSError:
                        pass

        packages.append(PipPackageInfo(
            name=name,
            version=version,
            size_bytes=total_size,
            path=pkg_path,
            summary=summary,
            top_level_modules=top_level,
            file_count=total_files,
        ))

    return sorted(packages, key=lambda p: p.size_bytes, reverse=True)


def _extract_imports_from_file(filepath: Path) -> set[str]:
    """Extract top-level import names from a Python file using AST."""
    imports = set()
    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(filepath))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    except (SyntaxError, ValueError, OSError):
        pass
    return imports


def _extract_imports_from_requirements(filepath: Path) -> set[str]:
    """Extract package names from requirements.txt style files."""
    names = set()
    try:
        for line in filepath.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Strip version specifiers
            name = re.split(r"[>=<!~;\[]", line)[0].strip()
            if name:
                names.add(name.lower())
    except OSError:
        pass
    return names


def find_unused_packages(
    packages: list[PipPackageInfo],
    project_dir: str,
    check_requirements: bool = True,
) -> list[PipPackageInfo]:
    """
    Find packages that are installed but not imported in the project.

    Args:
        packages: List of installed packages.
        project_dir: Path to the project source code.
        check_requirements: Also check requirements.txt for declared deps.

    Returns:
        Packages that appear to be unused.
    """
    root = Path(project_dir)

    # Collect all imports from Python files
    all_imports: set[str] = set()
    for py_file in root.rglob("*.py"):
        # Skip venv, .venv, node_modules
        parts = py_file.parts
        if any(p in (".venv", "venv", "node_modules", ".git", "__pycache__") for p in parts):
            continue
        all_imports.update(_extract_imports_from_file(py_file))

    # Also collect from requirements files
    declared_deps: set[str] = set()
    if check_requirements:
        for req_file in ("requirements.txt", "requirements-dev.txt", "requirements.in"):
            rf = root / req_file
            if rf.exists():
                declared_deps.update(_extract_imports_from_requirements(rf))

    # Standard library modules to ignore
    stdlib = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()

    unused = []
    for pkg in packages:
        # Skip standard tools and pip itself
        if pkg.name.lower() in ("pip", "setuptools", "wheel", "pkg-resources", "distribute"):
            continue

        # Check if any of the package's top-level modules are imported
        is_imported = any(mod in all_imports for mod in pkg.top_level_modules)

        # Check if the package name appears in requirements
        is_declared = pkg.name.lower() in declared_deps

        if not is_imported:
            pkg.is_used = False
            unused.append(pkg)
        else:
            pkg.is_used = True

    return unused


def get_pip_summary(packages: list[PipPackageInfo]) -> dict:
    """Generate a summary of pip package scan results."""
    total_size = sum(p.size_bytes for p in packages)
    return {
        "total_packages": len(packages),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "top_10_largest": [
            {"name": p.name, "version": p.version, "size_mb": round(p.size_bytes / (1024 * 1024), 2)}
            for p in packages[:10]
        ],
    }
