# bloat-radar

[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-blue?logo=anthropic&logoColor=white)](https://claude.ai/code)


**Your dependencies are bloated. Find out by how much.**

Analyze JavaScript/Python package sizes, find duplicates, and get suggestions for lighter alternatives -- all from the terminal.

```
$ bloat-radar scan --type npm

Scanning node_modules in /app...
Found 847 npm packages (312.4 MB)

Package             Version    Size        Files     %     Bar
--------------------------------------------------------------------------------
@next/swc-darwin    14.2.3     48.2 MB      12    15.4%   ████████████████████
typescript          5.4.5      38.1 MB     108    12.2%   ███████████████▊
esbuild             0.21.3     9.4 MB       24     3.0%   ████
webpack             5.91.0     6.2 MB      462     2.0%   ██▌
...

Duplicate Packages:
  debug (3 copies)
    v4.3.4    120 KB  node_modules/debug
    v3.2.7    98 KB   node_modules/express/node_modules/debug
    v2.6.9    72 KB   node_modules/body-parser/node_modules/debug
    Potential savings: 170 KB
```

## Why?

- **node_modules** averages 300MB+ for modern projects
- **50+ packages** have lighter drop-in replacements (moment -> dayjs saves 99%)
- **Duplicate packages** waste disk and bundle size silently
- You need a tool that **shows the problem** before you can fix it

## Install

```bash
pip install bloat-radar
```

## Usage

### Scan packages

```bash
# Scan everything (npm + pip)
bloat-radar scan

# Scan only npm packages
bloat-radar scan --type npm --path ./my-project

# Scan only pip packages
bloat-radar scan --type pip

# Output as JSON
bloat-radar scan --format json > report.json

# Output as Markdown
bloat-radar scan --format markdown > DEPENDENCIES.md
```

### Analyze a specific package

```bash
# Find alternatives for a package
bloat-radar analyze moment
bloat-radar analyze lodash
bloat-radar analyze requests --ecosystem pip
```

### Get suggestions

```bash
# Scan and suggest lighter alternatives
bloat-radar suggest --path ./my-project
bloat-radar suggest --type npm
```

### Generate reports

```bash
# Terminal table
bloat-radar report

# HTML treemap
bloat-radar report --format html --output sizes.html

# JSON for CI/CD
bloat-radar report --format json --output report.json
```

### Interactive treemap

```bash
# Generate clickable HTML treemap
bloat-radar treemap --output treemap.html
```

## Alternatives Database

50+ known package swaps with size savings:

| Heavy Package | Lighter Alternative | Savings |
|--------------|-------------------|---------|
| moment (4.2 MB) | dayjs (7 KB) | 99% |
| lodash (1.4 MB) | native ES6+ | 100% |
| webpack (28 MB) | esbuild (800 KB) | 97% |
| jest (22 MB) | vitest (1.2 MB) | 95% |
| axios (440 KB) | native fetch | 98% |
| chalk (120 KB) | picocolors (4 KB) | 97% |
| pandas (82 MB) | polars (28 MB) | 66% |
| celery (16 MB) | arq (80 KB) | 99% |

## Unused Package Detection (Python)

```bash
# Find pip packages not imported in your code
bloat-radar scan --type pip --path ./src
```

## License

MIT
