"""
RAG pipeline for document intelligence — semantic search over financial document corpus.

Uses:
  - text-embedding-3-large for embeddings (3072 dimensions)
  - ChromaDB for vector storage and retrieval
  - Recursive character text splitter for chunking
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class ChunkResult:
    """A retrieved document chunk with metadata."""
    text: str
    source: str
    page: int | None
    score: float
    metadata: dict[str, Any]


class DocumentRAG:
    """RAG pipeline for financial document retrieval."""

    def __init__(
        self,
        collection_name: str = "wm_documents",
        embedding_model: str = "text-embedding-3-large",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._collection = None

    def _get_collection(self):
        """Lazy-init ChromaDB collection."""
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

            client = chromadb.Client()
            embedding_fn = OpenAIEmbeddingFunction(model_name=self.embedding_model)
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            return self._collection
        except Exception as e:
            logger.error("chromadb_init_failed", error=str(e))
            return None

    def _chunk_text(self, text: str, source: str = "") -> list[dict]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        chunk_id = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append({
                "id": f"{source}_{chunk_id}",
                "text": chunk_text,
                "metadata": {"source": source, "chunk_index": chunk_id, "char_start": start},
            })
            start += self.chunk_size - self.chunk_overlap
            chunk_id += 1
        return chunks

    def ingest_document(self, text: str, source: str, metadata: dict | None = None) -> int:
        """Ingest a document into the vector store."""
        collection = self._get_collection()
        if collection is None:
            return 0

        chunks = self._chunk_text(text, source)
        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{**(metadata or {}), **c["metadata"]} for c in chunks]

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("document_ingested", source=source, chunks=len(chunks))
        return len(chunks)

    def query(self, question: str, n_results: int = 5) -> list[ChunkResult]:
        """Retrieve relevant chunks for a question."""
        collection = self._get_collection()
        if collection is None:
            return []

        results = collection.query(query_texts=[question], n_results=n_results)

        chunks = []
        for i in range(len(results["documents"][0])):
            chunks.append(ChunkResult(
                text=results["documents"][0][i],
                source=results["metadatas"][0][i].get("source", ""),
                page=results["metadatas"][0][i].get("page"),
                score=1 - results["distances"][0][i],  # cosine distance → similarity
                metadata=results["metadatas"][0][i],
            ))
        return chunks

    def get_context_for_extraction(self, question: str, n_results: int = 10) -> str:
        """Get concatenated context for document extraction."""
        chunks = self.query(question, n_results=n_results)
        return "\n\n---\n\n".join(
            f"[Source: {c.source}, Score: {c.score:.3f}]\n{c.text}" for c in chunks
        )
