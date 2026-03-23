"""Generate HTML treemap visualization: package sizes as rectangles, color by category."""

from __future__ import annotations

import html
import json
from typing import Any, Optional

# Category color mapping
CATEGORY_COLORS = {
    "utility": "#3498db",
    "framework": "#e74c3c",
    "datetime": "#f39c12",
    "http": "#2ecc71",
    "validation": "#9b59b6",
    "state": "#1abc9c",
    "build": "#e67e22",
    "css": "#fd79a8",
    "image": "#00cec9",
    "testing": "#6c5ce7",
    "templating": "#fdcb6e",
    "crypto": "#d63031",
    "formatting": "#74b9ff",
    "cli": "#55efc4",
    "fs": "#a29bfe",
    "async": "#fab1a0",
    "config": "#81ecec",
    "middleware": "#ffeaa7",
    "dev": "#dfe6e9",
    "data": "#0984e3",
    "scraping": "#636e72",
    "cloud": "#b2bec3",
    "orm": "#fd79a8",
    "task-queue": "#00b894",
    "other": "#95a5a6",
}


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def _assign_color(name: str, index: int) -> str:
    """Assign a color based on package name patterns or index."""
    name_lower = name.lower()

    # Try to guess category from name
    category_hints = {
        "utility": ["lodash", "underscore", "ramda", "utils", "helper"],
        "framework": ["express", "fastify", "react", "vue", "angular", "next", "nuxt", "django", "flask"],
        "datetime": ["moment", "dayjs", "date", "time", "luxon"],
        "http": ["axios", "request", "fetch", "http", "got", "ky"],
        "build": ["webpack", "babel", "esbuild", "rollup", "vite", "swc", "terser"],
        "testing": ["jest", "mocha", "chai", "vitest", "pytest", "test"],
        "css": ["sass", "less", "postcss", "tailwind", "styled", "css"],
        "cli": ["commander", "yargs", "inquirer", "chalk", "ora"],
        "data": ["pandas", "numpy", "polars", "scipy"],
    }

    for cat, hints in category_hints.items():
        if any(h in name_lower for h in hints):
            return CATEGORY_COLORS.get(cat, CATEGORY_COLORS["other"])

    # Deterministic color from palette
    colors = list(CATEGORY_COLORS.values())
    return colors[index % len(colors)]


def generate_treemap_data(packages: list[Any]) -> list[dict]:
    """Convert package list to treemap data format."""
    data = []
    for i, pkg in enumerate(packages):
        name = pkg.name if hasattr(pkg, "name") else pkg.get("name", "unknown")
        size = pkg.size_bytes if hasattr(pkg, "size_bytes") else pkg.get("size_bytes", 0)
        version = pkg.version if hasattr(pkg, "version") else pkg.get("version", "")

        if size <= 0:
            continue

        data.append({
            "name": name,
            "version": version,
            "size": size,
            "size_formatted": _format_size(size),
            "color": _assign_color(name, i),
        })

    return sorted(data, key=lambda d: d["size"], reverse=True)


def generate_treemap_html(
    packages: list[Any],
    title: str = "Package Size Treemap",
    output_path: Optional[str] = None,
) -> str:
    """
    Generate a self-contained HTML file with an interactive treemap visualization.

    Uses a pure CSS/JS treemap layout (no external dependencies).

    Args:
        packages: List of package info objects (NpmPackageInfo or PipPackageInfo).
        title: Title for the visualization.
        output_path: Optional path to write the HTML file.

    Returns:
        The HTML string.
    """
    data = generate_treemap_data(packages)
    total_size = sum(d["size"] for d in data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #fff; }}
.header {{
    padding: 24px 32px;
    background: #111;
    border-bottom: 1px solid #333;
}}
.header h1 {{ font-size: 24px; font-weight: 600; }}
.header .stats {{
    margin-top: 8px;
    font-size: 14px;
    color: #888;
}}
.header .stats span {{ color: #fff; font-weight: 600; }}
.treemap-container {{
    padding: 16px;
    display: flex;
    flex-wrap: wrap;
    align-content: flex-start;
    min-height: calc(100vh - 100px);
}}
.pkg-cell {{
    position: relative;
    overflow: hidden;
    cursor: pointer;
    border: 1px solid rgba(0,0,0,0.3);
    transition: transform 0.1s, box-shadow 0.1s;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 4px;
}}
.pkg-cell:hover {{
    transform: scale(1.02);
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    z-index: 10;
    border-color: #fff;
}}
.pkg-cell .name {{
    font-weight: 600;
    font-size: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
    text-shadow: 0 1px 3px rgba(0,0,0,0.7);
}}
.pkg-cell .size {{
    font-size: 10px;
    opacity: 0.85;
    margin-top: 2px;
    text-shadow: 0 1px 3px rgba(0,0,0,0.7);
}}
.tooltip {{
    display: none;
    position: fixed;
    background: #222;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    z-index: 1000;
    pointer-events: none;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    max-width: 300px;
}}
.tooltip .tt-name {{ font-weight: 700; font-size: 15px; margin-bottom: 4px; }}
.tooltip .tt-version {{ color: #888; font-size: 12px; }}
.tooltip .tt-size {{ color: #4fc3f7; margin-top: 6px; }}
.tooltip .tt-pct {{ color: #aaa; font-size: 12px; }}
.legend {{
    padding: 16px 32px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    background: #111;
    border-top: 1px solid #333;
}}
.legend-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #aaa;
}}
.legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
}}
</style>
</head>
<body>
<div class="header">
    <h1>{html.escape(title)}</h1>
    <div class="stats">
        <span>{len(data)}</span> packages &middot;
        <span>{_format_size(total_size)}</span> total
    </div>
</div>

<div class="treemap-container" id="treemap"></div>
<div class="tooltip" id="tooltip"></div>

<script>
const DATA = {json.dumps(data)};
const TOTAL = {total_size};

function buildTreemap() {{
    const container = document.getElementById('treemap');
    const containerWidth = container.clientWidth;
    const containerHeight = Math.max(window.innerHeight - 120, 400);
    container.style.height = containerHeight + 'px';

    // Simple squarified treemap using slice-and-dice
    const rects = squarify(DATA, 0, 0, containerWidth, containerHeight);

    container.innerHTML = '';
    rects.forEach((r, i) => {{
        const cell = document.createElement('div');
        cell.className = 'pkg-cell';
        cell.style.position = 'absolute';
        cell.style.left = r.x + 'px';
        cell.style.top = r.y + 'px';
        cell.style.width = r.w + 'px';
        cell.style.height = r.h + 'px';
        cell.style.backgroundColor = r.data.color;

        if (r.w > 50 && r.h > 30) {{
            cell.innerHTML = '<div class="name">' + escapeHtml(r.data.name) + '</div>';
            if (r.w > 70 && r.h > 45) {{
                cell.innerHTML += '<div class="size">' + r.data.size_formatted + '</div>';
            }}
        }}

        cell.addEventListener('mouseenter', (e) => showTooltip(e, r.data));
        cell.addEventListener('mousemove', moveTooltip);
        cell.addEventListener('mouseleave', hideTooltip);

        container.appendChild(cell);
    }});
}}

function squarify(data, x, y, w, h) {{
    if (data.length === 0 || w <= 0 || h <= 0) return [];

    const totalSize = data.reduce((s, d) => s + d.size, 0);
    if (totalSize === 0) return [];

    const rects = [];
    let remaining = [...data];
    let cx = x, cy = y, cw = w, ch = h;

    while (remaining.length > 0) {{
        const isWide = cw >= ch;
        const side = isWide ? ch : cw;
        const totalRemaining = remaining.reduce((s, d) => s + d.size, 0);

        // Find best row
        let row = [remaining[0]];
        let rowSize = remaining[0].size;
        let bestRatio = Infinity;

        for (let i = 1; i < remaining.length; i++) {{
            const testRow = [...row, remaining[i]];
            const testSize = rowSize + remaining[i].size;
            const ratio = worstRatio(testRow, testSize, side, totalRemaining, isWide ? cw : ch);
            const prevRatio = worstRatio(row, rowSize, side, totalRemaining, isWide ? cw : ch);

            if (ratio <= prevRatio) {{
                row = testRow;
                rowSize = testSize;
            }} else {{
                break;
            }}
        }}

        // Layout this row
        const rowFraction = rowSize / totalRemaining;
        const rowThickness = isWide ? cw * rowFraction : ch * rowFraction;

        let offset = 0;
        row.forEach(d => {{
            const frac = d.size / rowSize;
            const cellLength = side * frac;

            if (isWide) {{
                rects.push({{ x: cx, y: cy + offset, w: rowThickness, h: cellLength, data: d }});
            }} else {{
                rects.push({{ x: cx + offset, y: cy, w: cellLength, h: rowThickness, data: d }});
            }}
            offset += cellLength;
        }});

        // Advance
        if (isWide) {{
            cx += rowThickness;
            cw -= rowThickness;
        }} else {{
            cy += rowThickness;
            ch -= rowThickness;
        }}

        remaining = remaining.slice(row.length);
    }}

    return rects;
}}

function worstRatio(row, rowSize, side, totalSize, fullSide) {{
    const rowThickness = (rowSize / totalSize) * fullSide;
    if (rowThickness === 0) return Infinity;
    let worst = 0;
    row.forEach(d => {{
        const cellLength = (d.size / rowSize) * side;
        const ratio = Math.max(cellLength / rowThickness, rowThickness / cellLength);
        worst = Math.max(worst, ratio);
    }});
    return worst;
}}

function escapeHtml(str) {{
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}}

const tooltip = document.getElementById('tooltip');
function showTooltip(e, data) {{
    const pct = ((data.size / TOTAL) * 100).toFixed(1);
    tooltip.innerHTML = '<div class="tt-name">' + escapeHtml(data.name) + '</div>' +
        '<div class="tt-version">v' + escapeHtml(data.version) + '</div>' +
        '<div class="tt-size">' + data.size_formatted + '</div>' +
        '<div class="tt-pct">' + pct + '% of total</div>';
    tooltip.style.display = 'block';
    moveTooltip(e);
}}
function moveTooltip(e) {{
    tooltip.style.left = (e.clientX + 12) + 'px';
    tooltip.style.top = (e.clientY + 12) + 'px';
}}
function hideTooltip() {{ tooltip.style.display = 'none'; }}

window.addEventListener('resize', buildTreemap);
buildTreemap();
</script>
</body>
</html>"""

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    return html_content
