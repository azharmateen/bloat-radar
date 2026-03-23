"""Reports: terminal table (sorted by size), JSON, markdown, HTML treemap."""

from __future__ import annotations

import json
from typing import Any, Optional

from .treemap import generate_treemap_html


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def _size_bar(size_bytes: int, max_bytes: int, width: int = 20) -> str:
    """Generate a simple ASCII bar chart segment."""
    if max_bytes == 0:
        return " " * width
    ratio = min(size_bytes / max_bytes, 1.0)
    filled = int(ratio * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def _pkg_to_dict(pkg: Any) -> dict:
    """Convert a package info object to a dict."""
    if isinstance(pkg, dict):
        return pkg
    return {
        "name": getattr(pkg, "name", "unknown"),
        "version": getattr(pkg, "version", ""),
        "size_bytes": getattr(pkg, "size_bytes", 0),
        "file_count": getattr(pkg, "file_count", 0),
        "path": getattr(pkg, "path", ""),
        "is_duplicate": getattr(pkg, "is_duplicate", False),
    }


def report_terminal(
    packages: list[Any],
    top_n: int = 30,
    show_bar: bool = True,
) -> str:
    """
    Generate a terminal-friendly table report sorted by size.

    Args:
        packages: List of package info objects.
        top_n: Number of packages to show.
        show_bar: Whether to include a size bar chart.

    Returns:
        Formatted string for terminal output.
    """
    pkgs = [_pkg_to_dict(p) for p in packages]
    pkgs.sort(key=lambda p: p["size_bytes"], reverse=True)
    pkgs = pkgs[:top_n]

    if not pkgs:
        return "No packages found."

    total_size = sum(p["size_bytes"] for p in pkgs)
    max_size = pkgs[0]["size_bytes"] if pkgs else 1

    # Calculate column widths
    max_name = max(len(p["name"]) for p in pkgs)
    max_name = max(max_name, 7)  # "Package" header
    max_ver = max((len(p["version"]) for p in pkgs), default=7)
    max_ver = max(max_ver, 7)

    lines = []
    lines.append(f"\n{'Package':<{max_name}}  {'Version':<{max_ver}}  {'Size':>10}  {'Files':>6}  {'%':>5}", )

    if show_bar:
        lines[0] += f"  {'Bar':^20}"

    lines.append("-" * len(lines[0]))

    for p in pkgs:
        pct = (p["size_bytes"] / total_size * 100) if total_size > 0 else 0
        dup = " [DUP]" if p.get("is_duplicate") else ""
        line = (
            f"{p['name']:<{max_name}}  "
            f"{p['version']:<{max_ver}}  "
            f"{_format_size(p['size_bytes']):>10}  "
            f"{p['file_count']:>6}  "
            f"{pct:>4.1f}%"
        )
        if show_bar:
            line += f"  {_size_bar(p['size_bytes'], max_size)}"
        line += dup
        lines.append(line)

    lines.append("-" * len(lines[1]))
    lines.append(f"{'Total':<{max_name}}  {'':<{max_ver}}  {_format_size(total_size):>10}  {sum(p['file_count'] for p in pkgs):>6}")
    lines.append(f"\nShowing top {len(pkgs)} of {len(packages)} packages")

    return "\n".join(lines)


def report_json(packages: list[Any], indent: int = 2) -> str:
    """
    Generate a JSON report.

    Args:
        packages: List of package info objects.
        indent: JSON indent level.

    Returns:
        JSON string.
    """
    pkgs = [_pkg_to_dict(p) for p in packages]
    pkgs.sort(key=lambda p: p["size_bytes"], reverse=True)

    total_size = sum(p["size_bytes"] for p in pkgs)
    report = {
        "summary": {
            "total_packages": len(pkgs),
            "total_size_bytes": total_size,
            "total_size_human": _format_size(total_size),
        },
        "packages": [
            {
                "name": p["name"],
                "version": p["version"],
                "size_bytes": p["size_bytes"],
                "size_human": _format_size(p["size_bytes"]),
                "file_count": p["file_count"],
                "is_duplicate": p.get("is_duplicate", False),
                "percentage": round(p["size_bytes"] / total_size * 100, 2) if total_size > 0 else 0,
            }
            for p in pkgs
        ],
    }
    return json.dumps(report, indent=indent)


def report_markdown(packages: list[Any], top_n: int = 30) -> str:
    """
    Generate a Markdown report.

    Args:
        packages: List of package info objects.
        top_n: Number of packages to show.

    Returns:
        Markdown string.
    """
    pkgs = [_pkg_to_dict(p) for p in packages]
    pkgs.sort(key=lambda p: p["size_bytes"], reverse=True)
    pkgs = pkgs[:top_n]

    total_size = sum(p["size_bytes"] for p in pkgs)

    lines = [
        "# Package Size Report",
        "",
        f"**Total:** {_format_size(total_size)} across {len(packages)} packages",
        "",
        "| # | Package | Version | Size | Files | % |",
        "|---|---------|---------|------|-------|---|",
    ]

    for i, p in enumerate(pkgs, 1):
        pct = (p["size_bytes"] / total_size * 100) if total_size > 0 else 0
        dup = " :warning:" if p.get("is_duplicate") else ""
        lines.append(
            f"| {i} | {p['name']}{dup} | {p['version']} | "
            f"{_format_size(p['size_bytes'])} | {p['file_count']} | {pct:.1f}% |"
        )

    lines.extend([
        "",
        f"*Showing top {len(pkgs)} of {len(packages)} packages*",
    ])

    return "\n".join(lines)


def report_html_treemap(
    packages: list[Any],
    title: str = "Package Size Treemap",
    output_path: Optional[str] = None,
) -> str:
    """
    Generate an HTML treemap visualization.

    Args:
        packages: List of package info objects.
        title: Title for the visualization.
        output_path: Optional path to write the HTML file.

    Returns:
        HTML string.
    """
    return generate_treemap_html(packages, title=title, output_path=output_path)


def report_duplicates(packages: list[Any]) -> str:
    """
    Generate a report of duplicate packages.

    Args:
        packages: List of package info objects (must have is_duplicate and duplicate_versions).

    Returns:
        Formatted duplicate report string.
    """
    pkgs = [_pkg_to_dict(p) for p in packages]
    duplicates: dict[str, list[dict]] = {}

    for p in pkgs:
        if p.get("is_duplicate"):
            name = p["name"]
            if name not in duplicates:
                duplicates[name] = []
            duplicates[name].append(p)

    if not duplicates:
        return "No duplicate packages found."

    lines = ["\nDuplicate Packages:", "=" * 50]

    total_waste = 0
    for name, copies in sorted(duplicates.items()):
        sizes = [c["size_bytes"] for c in copies]
        waste = sum(sizes[1:])  # All but the largest are "waste"
        total_waste += waste

        lines.append(f"\n  {name} ({len(copies)} copies)")
        for c in copies:
            lines.append(f"    v{c['version']}  {_format_size(c['size_bytes']):>10}  {c['path']}")
        lines.append(f"    Potential savings: {_format_size(waste)}")

    lines.extend([
        "",
        f"Total duplicate packages: {len(duplicates)}",
        f"Total potential savings: {_format_size(total_waste)}",
    ])

    return "\n".join(lines)
