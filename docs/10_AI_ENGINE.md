# AI Engine

## Purpose
Define how AKWB produces optimized, token-aware, retrieval-friendly AI context from the project knowledge graph.

## Responsibilities
- Summarize `KnowledgeUnit`s.
- Chunk and structure content for LLM context windows.
- Generate embeddings and vector indexes.
- Assemble `ContextBundle`s for different AI tasks.
- Support retrieval-augmented generation (RAG) use cases.
- Manage context budget and token limits.

## Inputs
- `KnowledgeGraph` from the Knowledge Engine.
- `SourceCatalog`.
- Configuration: model token budget, embedding model, chunk size, chunk overlap, enable embeddings.
- `ContextBuilder` plugins.
- Prior context artifacts.

## Process
1. **Summarization:** For each `KnowledgeUnit`, generate or update a concise natural-language summary. Use lightweight local heuristics or models; external model calls are explicit opt-in.
2. **Chunking:** Split source text and summaries into chunks bounded by token count and semantic boundaries.
3. **Embedding:** Compute embeddings for chunks and summaries. This step is optional; a local model is preferred by default.
4. **Index Build:** Construct a vector index (HNSW or flat) and an inverted keyword index.
5. **Context Assembly:** Build `ContextBundle`s for tasks (code Q&A, onboarding, impact analysis). Each bundle contains selected chunks, metadata, and a relevance map.
6. **RAG Interface:** Provide a retrieval API used by future commands (`akwb ask`) or external tools.

## Outputs
- `ContextBundle` artifacts.
- Chunk and embedding files in `.akwb/context/`.
- Vector and keyword indexes.
- Updated `KnowledgeUnit` summaries.

## Dependencies
- `04_DOMAIN_MODEL.md`
- `08_KNOWLEDGE_ENGINE.md`
- `09_WORKSPACE_ENGINE.md`
- `11_DATA_MODEL.md`

## Future Extensions
- Integration with OpenAI, Ollama, and other local or remote LLMs.
- Agentic workflows for auto-refactoring suggestions.
- Multi-modal context (diagrams, images).
- Real-time context updates in watch mode.

## Risks
- LLM/embedding dependencies are large or require network access.
- Token budgets are hard to enforce consistently across different models.
- Privacy concerns if data leaves the local machine.

## Design Decisions

- AI context generation is local-first; external model calls require explicit permission.
- Context bundles are versioned artifacts like any other workspace output.
- A `ContextRetrievalAPI` supports retrieval-augmented generation (RAG) by task type (code Q&A, onboarding, impact analysis).
- Task selection maps a user intent to a `ContextBuilder` using task tags and a relevance score threshold.
- Summarization falls back to extractive heuristics when no local generative model is configured.
- Token budgets are enforced per chunk and per bundle using a pluggable tokenizer; over-budget content is ranked and truncated.
- Embeddings are optional; if disabled, keyword and graph indexes still function.
- Context builders are plugins, so different model strategies can coexist.
- Token counting uses a pluggable tokenizer; the default is an approximate tokenizer to avoid heavy dependencies.
