"""Alternative suggestions database: known lightweight replacements with size savings estimates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Alternative:
    """A lighter alternative to a heavy package."""

    original: str
    replacement: str
    category: str
    original_size_kb: int  # Approximate typical size in KB
    replacement_size_kb: int
    savings_percent: int
    note: str
    ecosystem: str  # "npm" or "pip"


# ─── NPM ALTERNATIVES ──────────────────────────────────────────────
_NPM_ALTERNATIVES: list[Alternative] = [
    # Utility libraries
    Alternative("lodash", "lodash-es (tree-shakeable) or native ES6+", "utility", 1400, 0, 100, "Most lodash functions have native equivalents", "npm"),
    Alternative("underscore", "native ES6+", "utility", 260, 0, 100, "Array/Object methods are native now", "npm"),
    Alternative("ramda", "rambda", "utility", 540, 52, 90, "Faster, smaller functional library", "npm"),
    Alternative("jquery", "native DOM API", "utility", 280, 0, 100, "querySelector, fetch, classList are native", "npm"),

    # Date/Time
    Alternative("moment", "dayjs", "datetime", 4200, 7, 99, "Same API, 2KB vs 67KB gzipped", "npm"),
    Alternative("moment", "date-fns (tree-shakeable)", "datetime", 4200, 50, 99, "Import only what you need", "npm"),
    Alternative("moment-timezone", "dayjs + timezone plugin", "datetime", 1800, 10, 99, "dayjs/plugin/timezone", "npm"),
    Alternative("luxon", "dayjs", "datetime", 680, 7, 99, "dayjs covers most Luxon use cases", "npm"),

    # HTTP
    Alternative("axios", "ky or native fetch", "http", 440, 10, 98, "fetch() is native in Node 18+ and browsers", "npm"),
    Alternative("request", "node-fetch or native fetch", "http", 1800, 10, 99, "Deprecated. Use native fetch", "npm"),
    Alternative("superagent", "ky", "http", 340, 10, 97, "ky is a tiny fetch wrapper", "npm"),
    Alternative("got", "ky or undici", "http", 480, 10, 98, "ky for browsers, undici for Node", "npm"),

    # Web frameworks
    Alternative("express", "fastify", "framework", 540, 320, 41, "Fastify is faster and more efficient", "npm"),
    Alternative("express", "hono", "framework", 540, 40, 93, "Hono is ultra-lightweight, works everywhere", "npm"),
    Alternative("koa", "hono", "framework", 220, 40, 82, "Hono has similar middleware pattern", "npm"),

    # Validation
    Alternative("joi", "zod", "validation", 480, 52, 89, "Zod is TypeScript-first, smaller", "npm"),
    Alternative("yup", "zod", "validation", 280, 52, 81, "Zod has better TS inference", "npm"),
    Alternative("ajv", "zod", "validation", 380, 52, 86, "Zod for TS projects, ajv for JSON Schema", "npm"),
    Alternative("class-validator", "zod", "validation", 220, 52, 76, "Zod is decorator-free", "npm"),

    # State management
    Alternative("redux", "zustand", "state", 120, 8, 93, "Zustand is simpler, less boilerplate", "npm"),
    Alternative("mobx", "valtio", "state", 380, 12, 97, "Valtio is proxy-based like MobX but tiny", "npm"),
    Alternative("vuex", "pinia", "state", 120, 20, 83, "Pinia is the official Vue store now", "npm"),

    # Bundling/Build
    Alternative("webpack", "esbuild", "build", 28000, 800, 97, "esbuild is 100x faster", "npm"),
    Alternative("webpack", "vite", "build", 28000, 2000, 93, "Vite uses esbuild + Rollup", "npm"),
    Alternative("babel", "swc", "build", 18000, 400, 98, "SWC is Rust-based, much faster", "npm"),
    Alternative("terser", "esbuild", "build", 2400, 800, 67, "esbuild minifies too", "npm"),

    # CSS
    Alternative("node-sass", "sass (dart-sass)", "css", 12000, 5200, 57, "node-sass is deprecated", "npm"),
    Alternative("less", "postcss", "css", 3600, 80, 98, "PostCSS with plugins is more flexible", "npm"),

    # Image
    Alternative("sharp", "squoosh", "image", 42000, 1200, 97, "squoosh is WASM-based, no native deps", "npm"),
    Alternative("jimp", "sharp", "image", 8400, 42000, -400, "sharp is faster but larger (native)", "npm"),

    # Testing
    Alternative("mocha + chai + sinon", "vitest", "testing", 4800, 1200, 75, "Vitest is all-in-one, Vite-powered", "npm"),
    Alternative("jest", "vitest", "testing", 22000, 1200, 95, "Vitest is faster, compatible API", "npm"),
    Alternative("karma", "vitest or playwright", "testing", 8800, 1200, 86, "Karma is deprecated", "npm"),

    # Templating
    Alternative("handlebars", "eta", "templating", 440, 20, 95, "Eta is faster and smaller", "npm"),
    Alternative("ejs", "eta", "templating", 200, 20, 90, "Eta is a modern replacement", "npm"),
    Alternative("pug", "eta", "templating", 2800, 20, 99, "Unless you need Pug syntax", "npm"),

    # Crypto / UUID
    Alternative("uuid", "crypto.randomUUID()", "crypto", 60, 0, 100, "Native in Node 19+ and browsers", "npm"),
    Alternative("nanoid", "crypto.randomUUID()", "crypto", 8, 0, 100, "If UUID format is acceptable", "npm"),
    Alternative("bcrypt", "bcryptjs", "crypto", 1800, 40, 98, "Pure JS, no native compilation", "npm"),

    # Misc
    Alternative("chalk", "picocolors", "formatting", 120, 4, 97, "picocolors is 14x smaller", "npm"),
    Alternative("colors", "picocolors", "formatting", 80, 4, 95, "colors had supply chain attack", "npm"),
    Alternative("commander", "citty", "cli", 100, 12, 88, "citty is modern and tiny", "npm"),
    Alternative("yargs", "citty", "cli", 420, 12, 97, "citty for simple CLIs", "npm"),
    Alternative("glob", "tinyglobby", "fs", 200, 8, 96, "tinyglobby is faster and smaller", "npm"),
    Alternative("minimatch", "picomatch", "fs", 80, 12, 85, "picomatch is faster", "npm"),
    Alternative("bluebird", "native Promise", "async", 440, 0, 100, "Native Promises are fast enough now", "npm"),
    Alternative("async", "native async/await", "async", 320, 0, 100, "async/await replaces most patterns", "npm"),
    Alternative("cross-env", "native env setting", "dev", 40, 0, 100, "Node 20+ handles env cross-platform", "npm"),
    Alternative("dotenv", "node --env-file", "config", 60, 0, 100, "Node 20.6+ has built-in .env support", "npm"),
    Alternative("body-parser", "express.json()", "middleware", 120, 0, 100, "Built into Express 4.16+", "npm"),
    Alternative("cors", "fastify-cors or manual headers", "middleware", 40, 4, 90, "Simple CORS headers are 5 lines", "npm"),
    Alternative("classnames", "clsx", "utility", 20, 4, 80, "clsx is smaller and faster", "npm"),
]

# ─── PIP ALTERNATIVES ──────────────────────────────────────────────
_PIP_ALTERNATIVES: list[Alternative] = [
    Alternative("requests", "httpx", "http", 800, 1200, -50, "httpx supports async + HTTP/2, slightly larger but more capable", "pip"),
    Alternative("requests", "urllib3 (direct)", "http", 800, 400, 50, "urllib3 is already a requests dependency", "pip"),
    Alternative("beautifulsoup4", "selectolax", "scraping", 1200, 200, 83, "selectolax is 30x faster HTML parser", "pip"),
    Alternative("beautifulsoup4", "lxml.html", "scraping", 1200, 0, 100, "lxml is often already installed", "pip"),
    Alternative("pillow", "pillow-simd", "image", 28000, 28000, 0, "Same API, SIMD-optimized, 4-6x faster", "pip"),
    Alternative("pandas", "polars", "data", 82000, 28000, 66, "Polars is faster and uses less memory", "pip"),
    Alternative("numpy + pandas", "polars", "data", 120000, 28000, 77, "Polars has no numpy dependency", "pip"),
    Alternative("flask", "litestar", "framework", 2400, 4000, -67, "Litestar is larger but much more capable", "pip"),
    Alternative("flask", "fastapi", "framework", 2400, 800, 67, "FastAPI is async-first, auto-docs", "pip"),
    Alternative("django-rest-framework", "django-ninja", "framework", 8000, 400, 95, "Ninja is faster, less boilerplate", "pip"),
    Alternative("celery", "huey", "task-queue", 16000, 200, 99, "Huey for simpler task queues", "pip"),
    Alternative("celery", "arq", "task-queue", 16000, 80, 100, "arq is async Redis-based, minimal", "pip"),
    Alternative("pyyaml", "ruyaml or strictyaml", "config", 1800, 400, 78, "ruyaml is a maintained ruamel.yaml fork", "pip"),
    Alternative("python-dateutil", "pendulum", "datetime", 800, 2400, -200, "Pendulum is larger but much better API", "pip"),
    Alternative("python-dateutil", "arrow", "datetime", 800, 400, 50, "Arrow is simpler date handling", "pip"),
    Alternative("sqlalchemy", "peewee", "orm", 12000, 800, 93, "Peewee for simple projects", "pip"),
    Alternative("boto3", "aioboto3", "cloud", 120000, 120000, 0, "Same size but async-capable", "pip"),
    Alternative("click", "typer", "cli", 600, 200, 67, "Typer wraps Click with type hints", "pip"),
    Alternative("argparse", "typer", "cli", 0, 200, 0, "Typer is better DX than argparse", "pip"),
    Alternative("pytest-cov", "coverage", "testing", 400, 200, 50, "Direct coverage is simpler", "pip"),
    Alternative("faker", "mimesis", "testing", 6000, 3000, 50, "Mimesis is faster for data generation", "pip"),
]


def get_all_alternatives() -> list[Alternative]:
    """Return all known alternatives."""
    return _NPM_ALTERNATIVES + _PIP_ALTERNATIVES


def get_npm_alternatives() -> list[Alternative]:
    """Return npm alternatives only."""
    return list(_NPM_ALTERNATIVES)


def get_pip_alternatives() -> list[Alternative]:
    """Return pip alternatives only."""
    return list(_PIP_ALTERNATIVES)


def find_alternatives(package_name: str, ecosystem: Optional[str] = None) -> list[Alternative]:
    """
    Find lighter alternatives for a given package.

    Args:
        package_name: Name of the package to find alternatives for.
        ecosystem: Filter by 'npm' or 'pip'. None returns both.

    Returns:
        List of Alternative suggestions.
    """
    name_lower = package_name.lower()
    results = []
    for alt in get_all_alternatives():
        if ecosystem and alt.ecosystem != ecosystem:
            continue
        if alt.original.lower() == name_lower:
            results.append(alt)
    return results


def find_alternatives_for_list(
    package_names: list[str], ecosystem: Optional[str] = None
) -> dict[str, list[Alternative]]:
    """
    Find alternatives for a list of packages.

    Args:
        package_names: List of package names.
        ecosystem: Filter by ecosystem.

    Returns:
        Dict mapping package names to their alternatives.
    """
    results: dict[str, list[Alternative]] = {}
    for name in package_names:
        alts = find_alternatives(name, ecosystem)
        if alts:
            results[name] = alts
    return results


def get_total_potential_savings(
    package_names: list[str], ecosystem: Optional[str] = None
) -> dict:
    """Calculate total potential size savings from switching to alternatives."""
    all_alts = find_alternatives_for_list(package_names, ecosystem)
    total_original_kb = 0
    total_replacement_kb = 0
    suggestions = []

    for name, alts in all_alts.items():
        # Pick the best alternative (highest savings)
        best = max(alts, key=lambda a: a.savings_percent)
        total_original_kb += best.original_size_kb
        total_replacement_kb += best.replacement_size_kb
        suggestions.append({
            "package": best.original,
            "replacement": best.replacement,
            "savings_percent": best.savings_percent,
            "note": best.note,
        })

    return {
        "packages_with_alternatives": len(all_alts),
        "total_original_kb": total_original_kb,
        "total_replacement_kb": max(0, total_replacement_kb),
        "total_savings_kb": max(0, total_original_kb - total_replacement_kb),
        "suggestions": suggestions,
    }
