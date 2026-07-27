"""Usage example for the AKWB Enterprise Extraction Pipeline."""

from __future__ import annotations

from akwb.domain.models import Artifact
from akwb.extraction.pipeline import ExtractionPipeline


def main() -> None:
    pipeline = ExtractionPipeline()

    artifact = Artifact(
        name="adr.md",
        relative_path="docs/adr/001-postgresql.md",
        mime_type="text/markdown",
    )

    text = """# Decision to use PostgreSQL

We will adopt PostgreSQL as the primary data store for reliability.

```python
def connect():
    return psycopg2.connect(DSN)
```

| Criterion | PostgreSQL | SQLite |
|-----------|------------|--------|
| Scale     | High       | Low    |
"""

    result = pipeline.extract(artifact, text, project_id="akwb")

    print(f"Extraction OK: {result.ok}")
    print(f"Candidates: {result.candidate_count}")
    print(f"Knowledge objects: {len(result.objects)}")
    for obj in result.objects:
        print(f"  - {obj.type}: {obj.title}")

    if result.diagnostics:
        print("\nDiagnostics:")
        for diag in result.diagnostics:
            print(f"  - [{diag.level}] {diag.code}: {diag.message}")


if __name__ == "__main__":
    main()
