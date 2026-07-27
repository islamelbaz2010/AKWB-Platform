"""Sample graph engine plugin fixture."""

from akwb.graph.models import GraphQuery, KnowledgeGraph, QueryResult
from akwb.graph.plugins import GraphQueryEngine


class ReverseOrderQueryEngine(GraphQueryEngine):
    """Custom query engine that returns node ids in reverse alphabetical order."""

    def execute(self, query: GraphQuery, graph: KnowledgeGraph) -> QueryResult:
        node_ids = sorted(graph.nodes.keys(), reverse=True)
        if query.limit:
            node_ids = node_ids[: query.limit]
        return QueryResult(node_ids=node_ids)


def register(api) -> None:
    """Register the custom query engine with the plugin system."""
    api.register_port("graph_query_engine", ReverseOrderQueryEngine())
