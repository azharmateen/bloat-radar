"""Click CLI: bloat-radar scan, analyze, suggest, report, treemap."""

from __future__ import annotations

import os
import sys

import click

from . import __version__
from .alternatives import find_alternatives, get_total_potential_savings
from .npm_scanner import find_duplicates, find_largest_packages, get_scan_summary, scan_node_modules
from .pip_scanner import find_unused_packages, get_pip_summary, scan_pip_packages
from .reporter import report_duplicates, report_html_treemap, report_json, report_markdown, report_terminal


@click.group()
@click.version_option(version=__version__, prog_name="bloat-radar")
def cli():
    """Analyze JavaScript/Python package sizes, find duplicates, suggest lighter alternatives."""
    pass


@cli.command()
@click.option("--path", "-p", default=".", help="Project directory to scan")
@click.option("--type", "-t", "scan_type", type=click.Choice(["npm", "pip", "all"]), default="all", help="What to scan")
@click.option("--top", "-n", default=30, help="Number of top packages to show")
@click.option("--format", "-f", "fmt", type=click.Choice(["terminal", "json", "markdown"]), default="terminal", help="Output format")
@click.option("--include-nested/--no-nested", default=True, help="Include nested node_modules")
def scan(path: str, scan_type: str, top: int, fmt: str, include_nested: bool):
    """Scan installed packages and show size report."""
    path = os.path.abspath(path)
    all_packages = []

    if scan_type in ("npm", "all"):
        nm_path = os.path.join(path, "node_modules")
        if os.path.isdir(nm_path):
            click.echo(f"Scanning node_modules in {path}...", err=True)
            npm_pkgs = scan_node_modules(path, include_nested=include_nested)
            all_packages.extend(npm_pkgs)
            summary = get_scan_summary(npm_pkgs)
            click.echo(f"Found {summary['total_packages']} npm packages ({summary['total_size_mb']} MB)", err=True)
        elif scan_type == "npm":
            click.echo(f"No node_modules found in {path}", err=True)

    if scan_type in ("pip", "all"):
        click.echo("Scanning pip packages...", err=True)
        pip_pkgs = scan_pip_packages()
        all_packages.extend(pip_pkgs)
        summary = get_pip_summary(pip_pkgs)
        click.echo(f"Found {summary['total_packages']} pip packages ({summary['total_size_mb']} MB)", err=True)

    if not all_packages:
        click.echo("No packages found to analyze.")
        return

    # Output report
    if fmt == "terminal":
        click.echo(report_terminal(all_packages, top_n=top))
    elif fmt == "json":
        click.echo(report_json(all_packages))
    elif fmt == "markdown":
        click.echo(report_markdown(all_packages, top_n=top))

    # Show duplicates for npm
    if scan_type in ("npm", "all"):
        npm_only = [p for p in all_packages if hasattr(p, "is_duplicate")]
        dups = find_duplicates(npm_only)
        if dups:
            click.echo(report_duplicates(npm_only))


@cli.command()
@click.argument("package_name")
@click.option("--ecosystem", "-e", type=click.Choice(["npm", "pip"]), default=None, help="Package ecosystem")
def analyze(package_name: str, ecosystem: str | None):
    """Analyze a specific package and find alternatives."""
    alts = find_alternatives(package_name, ecosystem)

    if not alts:
        click.echo(f"No alternatives found for '{package_name}'.")
        click.echo("The package may already be optimal, or it's not in our database.")
        return

    click.echo(f"\nAlternatives for '{package_name}':")
    click.echo("=" * 60)

    for alt in alts:
        savings_color = "green" if alt.savings_percent > 0 else "red"
        click.echo(f"\n  Replace with: {click.style(alt.replacement, bold=True)}")
        click.echo(f"  Category:     {alt.category}")
        click.echo(f"  Ecosystem:    {alt.ecosystem}")
        click.echo(f"  Original:     ~{alt.original_size_kb} KB")
        click.echo(f"  Replacement:  ~{alt.replacement_size_kb} KB")

        if alt.savings_percent > 0:
            click.echo(f"  Savings:      {click.style(f'{alt.savings_percent}%', fg=savings_color)}")
        else:
            click.echo(f"  Note:         Replacement is larger (more features)")

        click.echo(f"  Reason:       {alt.note}")


@cli.command()
@click.option("--path", "-p", default=".", help="Project directory")
@click.option("--type", "-t", "scan_type", type=click.Choice(["npm", "pip", "all"]), default="all", help="Ecosystem")
def suggest(path: str, scan_type: str):
    """Scan packages and suggest lighter alternatives."""
    path = os.path.abspath(path)
    package_names = []

    if scan_type in ("npm", "all"):
        nm_path = os.path.join(path, "node_modules")
        if os.path.isdir(nm_path):
            npm_pkgs = scan_node_modules(path)
            package_names.extend(p.name for p in npm_pkgs)

    if scan_type in ("pip", "all"):
        pip_pkgs = scan_pip_packages()
        package_names.extend(p.name for p in pip_pkgs)

    if not package_names:
        click.echo("No packages found.")
        return

    ecosystem_filter = scan_type if scan_type != "all" else None
    savings = get_total_potential_savings(package_names, ecosystem_filter)

    if not savings["suggestions"]:
        click.echo("No alternative suggestions found. Your dependencies look lean!")
        return

    click.echo(f"\nFound {savings['packages_with_alternatives']} packages with lighter alternatives:")
    click.echo(f"Potential savings: ~{savings['total_savings_kb']} KB")
    click.echo("=" * 70)

    for s in savings["suggestions"]:
        if s["savings_percent"] > 0:
            click.echo(
                f"\n  {click.style(s['package'], fg='yellow')} -> "
                f"{click.style(s['replacement'], fg='green')} "
                f"({s['savings_percent']}% smaller)"
            )
            click.echo(f"    {s['note']}")


@cli.command()
@click.option("--path", "-p", default=".", help="Project directory")
@click.option("--type", "-t", "scan_type", type=click.Choice(["npm", "pip", "all"]), default="all")
@click.option("--format", "-f", "fmt", type=click.Choice(["terminal", "json", "markdown", "html"]), default="terminal")
@click.option("--output", "-o", default=None, help="Output file path")
@click.option("--top", "-n", default=30, help="Number of top packages")
def report(path: str, scan_type: str, fmt: str, output: str | None, top: int):
    """Generate a detailed size report in various formats."""
    path = os.path.abspath(path)
    all_packages = []

    if scan_type in ("npm", "all"):
        nm_path = os.path.join(path, "node_modules")
        if os.path.isdir(nm_path):
            all_packages.extend(scan_node_modules(path))

    if scan_type in ("pip", "all"):
        all_packages.extend(scan_pip_packages())

    if not all_packages:
        click.echo("No packages found.")
        return

    if fmt == "terminal":
        result = report_terminal(all_packages, top_n=top)
    elif fmt == "json":
        result = report_json(all_packages)
    elif fmt == "markdown":
        result = report_markdown(all_packages, top_n=top)
    elif fmt == "html":
        out_path = output or "bloat-radar-report.html"
        result = report_html_treemap(all_packages, output_path=out_path)
        click.echo(f"HTML treemap written to {out_path}", err=True)
        return

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        click.echo(f"Report written to {output}", err=True)
    else:
        click.echo(result)


@cli.command()
@click.option("--path", "-p", default=".", help="Project directory")
@click.option("--type", "-t", "scan_type", type=click.Choice(["npm", "pip", "all"]), default="all")
@click.option("--output", "-o", default="bloat-radar-treemap.html", help="Output HTML file path")
def treemap(path: str, scan_type: str, output: str):
    """Generate an interactive HTML treemap visualization."""
    path = os.path.abspath(path)
    all_packages = []

    if scan_type in ("npm", "all"):
        nm_path = os.path.join(path, "node_modules")
        if os.path.isdir(nm_path):
            click.echo("Scanning node_modules...", err=True)
            all_packages.extend(scan_node_modules(path))

    if scan_type in ("pip", "all"):
        click.echo("Scanning pip packages...", err=True)
        all_packages.extend(scan_pip_packages())

    if not all_packages:
        click.echo("No packages found.")
        return

    report_html_treemap(all_packages, title="bloat-radar Treemap", output_path=output)
    click.echo(f"Treemap written to {output}")
    click.echo(f"Open in browser: file://{os.path.abspath(output)}")


def main():
    cli()


if __name__ == "__main__":
    main()
