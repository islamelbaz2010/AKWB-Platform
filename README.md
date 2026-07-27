# AKWB Platform — Knowledge Workspace

**AKWB** is a local-first, project-owned knowledge workspace for software
teams. It analyses a project directory, discovers documents and source files,
and builds a structured, versioned knowledge graph that lives next to your code
in `.akwb/`.

- **Local-first** — all data stays in the project directory.
- **Plugin-based** — extend discovery, extraction, and graph storage through
  a clean port interface.
- **CLI-first** — one command to analyse a project and produce reports and
  exports.

## Installation

Requires **Python 3.12 or newer**.

```bash
pip install -e .
```

This installs the `akwb` console script.

## Quick Start

Create a sample project and analyse it:

```bash
mkdir sample_project && cd sample_project
cat > README.md << 'EOF'
# Sample Project

A minimal example used by the AKWB quick-start guide.
EOF

mkdir -p src
cat > src/app.py << 'EOF'
"""Sample application module."""
import config

def main() -> None:
    settings = config.load_settings()
    print(f"Starting with {settings}")

if __name__ == "__main__":
    main()
EOF

akwb analyze .
```

After analysis, the `.akwb/` workspace contains:

```
.akwb/
├── artifacts.json
├── workspace.json
├── index/
│   └── source_catalog.jsonl
├── knowledge/
│   ├── catalog.jsonl
│   ├── graph_edges.jsonl
│   └── graph_nodes.jsonl
├── graph/
│   ├── graph.cypher
│   ├── graph.dot
│   └── graph.jsonl
├── reports/
│   ├── summary.md
│   └── summary.json
└── logs/
    └── analysis.log
```

View the summary report:

```bash
akwb report summary
```

Or export the graph to Cypher:

```bash
akwb export cypher
```

## CLI

```
akwb --help
```

Primary commands in AKWB 1.0.0 MVP:

- `akwb init [path]` — initialize a `.akwb/` workspace.
- `akwb analyze [path]` — discover artifacts, extract knowledge, build the
  graph, and persist workspace artifacts.
- `akwb discover [path]` — run only the discovery phase and produce the
  artifact registry.
- `akwb doctor [path]` — validate the environment and workspace.
- `akwb report {summary,structure,graph}` — display a generated report.
- `akwb export {jsonl,dot,cypher}` — export the knowledge graph.
- `akwb version` — print the AKWB version.

For the full CLI specification, supported flags, exit codes, and planned
post-MVP commands, see [`docs/13_CLI_SPECIFICATION.md`](docs/13_CLI_SPECIFICATION.md).

## Architecture

AKWB uses a layered, port-driven architecture:

1. **Discovery** — recursively scans the project tree, classifies files, and
   fingerprints them for incremental updates.
2. **Extraction** — parses documents and source code into knowledge objects
   and relationships. Markdown and Python source are supported out of the box.
3. **Knowledge Framework** — defines typed knowledge objects, relationships,
   evidence, and validators.
4. **Graph Engine** — builds an in-memory knowledge graph, validates it, and
   exports it to JSONL, DOT, and Cypher.
5. **Workspace** — materialises all artifacts under `.akwb/`.
6. **Plugin Framework** — loads third-party plugins that extend extraction,
   graph storage, or reporting through domain ports.

See the full architecture and design documents in [`docs/`](docs/).

## Example

Analyse the bundled fixtures:

```bash
akwb analyze fixtures/small_project
akwb report summary --project-root fixtures/small_project
```

JSON output is available for scripting:

```bash
akwb analyze . --json
```

## Documentation

- [Product Scope](docs/PRODUCT_SCOPE.md)
- [MVP Acceptance Test](docs/MVP_ACCEPTANCE_TEST.md)
- [CLI Specification](docs/13_CLI_SPECIFICATION.md)
- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)
- [Security Model](docs/16_SECURITY_MODEL.md)
- [Performance Strategy](docs/17_PERFORMANCE_STRATEGY.md)
- [Known Limitations](docs/KNOWN_LIMITATIONS.md)

## License

MIT — see [`pyproject.toml`](pyproject.toml) for the full license text.
