# Enterprise Knowledge Graph Engine

## Purpose

The `akwb.graph` package provides a canonical, in-memory graph abstraction over the `KnowledgeObject` and `KnowledgeRelationship` instances produced by earlier sprints. It is **not** a graph database, and it does not integrate Neo4j, TigerGraph, JanusGraph, or any external graph DB.

The engine is the single graph representation used by all future engines.

## Graph Model

- `KnowledgeGraph` — container for `GraphNode`s and `GraphEdge`s with adjacency indexes.
- `GraphNode` — a view over a `KnowledgeObject` with labels, properties, and edge references.
- `GraphEdge` — a view over a `KnowledgeRelationship` with source, target, type, and direction.

## Graph Abstractions

| Component | Responsibility |
|---|---|
| `KnowledgeGraph` | Stores nodes, edges, incoming/outgoing adjacency, and an optional index. |
| `GraphIndex` / `InMemoryGraphIndex` | Fast inverted indexes for type, tag, domain, source, confidence, lifecycle, project, metadata, and relationship type. |
| `GraphQuery` | Declarative query object (type, tag, domain, source, confidence, lifecycle, project, metadata, relationship, edge type, limit). |
| `DefaultGraphQueryEngine` | Executes `GraphQuery` against an indexed `KnowledgeGraph`. |
| `GraphTraversal` / `DefaultTraversalAlgorithm` | BFS, DFS, shortest path, dependency walk, reverse dependency walk. |
| `GraphValidation` / `GraphValidator` | Broken references, cycles, duplicate edges, orphan nodes, invalid relationship types. |
| `GraphStatistics` | Node/edge counts, type distributions, density, connected components, orphans, cycles. |
| `GraphBuilder` | Builds a `KnowledgeGraph` from a `KnowledgeCatalog`. |
| `GraphEngine` | Orchestrator that wires indexing, querying, traversal, validation, statistics, and plugin loading. |

## Supported Operations

### Object lookup
`engine.query(graph, GraphQuery(node_type="decision"))`

### Relationship lookup
`engine.query(graph, GraphQuery(edge_type="depends_on"))`

### Incoming / outgoing edges
`graph.get_incoming_edges(node_id)`
`graph.get_outgoing_edges(node_id)`

### Ancestors / Descendants
`graph.ancestors(node_id)`
`graph.descendants(node_id)`

### Dependency graph
`graph.dependency_walk(...)` via `GraphEngine.traverse(..., strategy="dependency")`

### Reverse dependency
`GraphEngine.traverse(..., strategy="reverse_dependency")`

### Cycles
`GraphValidator` detects directed cycles and `GraphStatistics` counts strongly connected components.

### Neighborhood
`graph.neighborhood(node_id, radius=2)`

### Connected components
`graph.connected_components()`

### Impact analysis
`graph.descendants(node_id)` or `graph.impact(node_id)` — all nodes reachable from a starting node.

## Plugin Ports

The following ports are all replaceable through the plugin system:

- `GraphStorage` (`port_name = "graph_storage"`) — persist and load graphs.
- `GraphQueryEngine` (`port_name = "graph_query_engine"`) — execute `GraphQuery`.
- `TraversalAlgorithm` (`port_name = "graph_traversal"`) — execute `TraversalRequest`.
- `GraphIndexer` (`port_name = "graph_index"`) — build and search graph indexes.

## Usage Example

```python
from akwb.graph.engine import GraphEngine
from akwb.graph.models import GraphQuery, TraversalRequest
from akwb.knowledge.framework import KnowledgeFramework

framework = KnowledgeFramework()
catalog = framework.new_catalog()
# ... add objects and relationships ...

engine = GraphEngine(framework=framework)
graph = engine.build(catalog)

# Query
result = engine.query(graph, GraphQuery(node_type="decision"))
print(result.node_ids)

# Traversal
result = engine.traverse(
    graph,
    TraversalRequest(start="ku://decision-1", strategy="dependency"),
)
print(result.node_ids)

# Validation
validation = engine.validate(graph)
print(validation.ok)

# Statistics
stats = engine.statistics(graph)
print(stats.node_count, stats.edge_count, stats.cycle_count)
```

## Plugin Example

```python
from akwb.graph.models import GraphQuery, KnowledgeGraph, QueryResult
from akwb.graph.plugins import GraphQueryEngine

class CustomQueryEngine(GraphQueryEngine):
    port_name = "graph_query_engine"

    def execute(self, query: GraphQuery, graph: KnowledgeGraph) -> QueryResult:
        # Custom ranking or external search.
        return QueryResult(node_ids=list(graph.nodes.keys())[: query.limit])

# In plugin register function:
#   api.register_port("graph_query_engine", CustomQueryEngine())
```

## Exclusions Respected

- No Neo4j, TigerGraph, JanusGraph, or GraphDB integration.
- No external database required.
- Storage remains abstract via the `GraphStorage` port.

## Module Structure

```
src/akwb/graph/
  __init__.py        # Public API
  models.py          # GraphNode, GraphEdge, KnowledgeGraph, queries, results
  plugins.py         # GraphStorage, GraphQueryEngine, TraversalAlgorithm, GraphIndexer ports
  index.py           # InMemoryGraphIndex, DefaultGraphQueryEngine
  traversal.py       # DefaultTraversalAlgorithm
  validation.py      # GraphValidator
  statistics.py      # GraphStatistics
  builder.py         # GraphBuilder
  engine.py          # GraphEngine orchestrator
```
