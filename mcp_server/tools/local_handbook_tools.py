"""Local handbook search tool using ChromaDB vector store and all-MiniLM-L6-v2 embeddings.

Drops matches below SIMILARITY_THRESHOLD and strictly returns coverage: 'none' when
no relevant documentation exists, preventing ungrounded hallucination.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, List, Optional
from config import config
from mcp_server.privacy import audit_tool_call
from mcp_server.schemas import DocMatch, SearchDocsResult, SourceRef, ToolError

import os
import threading

CHROMA_STORE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "chroma_store"

# Global lazy-loaded references
_embedder = None
_embedder_lock = threading.Lock()
_chroma_collection = None


def _get_embedder():
    global _embedder
    with _embedder_lock:
        if _embedder is None:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from sentence_transformers import SentenceTransformer
            try:
                _embedder = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            except Exception:
                _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        return _embedder


def _warmup_embedder():
    try:
        _get_embedder()
    except Exception:
        pass


# Start background embedder warmup thread on module import
threading.Thread(target=_warmup_embedder, name="EmbedderWarmupThread", daemon=True).start()


def _get_chroma_collection():
    global _chroma_collection
    if _chroma_collection is None:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_STORE_DIR))
        _chroma_collection = client.get_or_create_collection(
            name="handbook_docs",
            metadata={"hnsw:space": "cosine"},
        )
    return _chroma_collection


def search_onboarding_docs(query: str, top_k: int = 4) -> SearchDocsResult:
    """Search the local onboarding handbook for setup instructions, architecture, rules, and workflows."""
    clean_query = query.strip()
    if not clean_query:
        res = SearchDocsResult(query=query, matches=[], coverage="none", source_refs=[])
        audit_tool_call("search_onboarding_docs", {"query": query}, "empty_query", res, 0)
        return res

    try:
        embedder = _get_embedder()
        collection = _get_chroma_collection()

        query_embedding = embedder.encode(clean_query, normalize_embeddings=True).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(max(top_k, 1), 10),
            include=["documents", "metadatas", "distances"],
        )

        matches: List[DocMatch] = []
        source_refs: List[SourceRef] = []

        raw_docs = results.get("documents", [[]])[0]
        raw_metas = results.get("metadatas", [[]])[0]
        raw_distances = results.get("distances", [[]])[0]

        threshold = config.similarity_threshold

        for idx, (doc_text, meta, distance) in enumerate(zip(raw_docs, raw_metas, raw_distances)):
            # In cosine space, similarity = 1.0 - distance
            similarity = round(max(0.0, 1.0 - float(distance)), 4)
            if similarity < threshold:
                # Drop weak matches strictly
                continue

            heading_path = meta.get("heading_path", "")
            file_name = meta.get("file", "")
            origin = meta.get("origin", "repo_docs")
            url = meta.get("url")

            label = f"{heading_path} (authored)" if origin == "authored" else heading_path
            source_id = f"S{len(source_refs) + 1}"

            source_refs.append(
                SourceRef(
                    id=source_id,
                    kind="local",
                    label=label,
                    url=url,
                )
            )

            matches.append(
                DocMatch(
                    text=doc_text,
                    file=file_name,
                    heading_path=heading_path,
                    origin=origin,
                    url=url,
                    similarity=similarity,
                )
            )

        if not matches:
            res = SearchDocsResult(
                query=clean_query,
                matches=[],
                coverage="none",
                source_refs=[],
            )
            audit_tool_call("search_onboarding_docs", {"query": query, "top_k": top_k}, "no_match", res, 0)
            return res

        best_sim = matches[0].similarity
        coverage_level = "high" if best_sim >= 0.60 else "low"

        res = SearchDocsResult(
            query=clean_query,
            matches=matches,
            coverage=coverage_level,
            source_refs=source_refs,
        )
        audit_tool_call("search_onboarding_docs", {"query": query, "top_k": top_k}, "success", res, 0)
        return res

    except Exception as exc:
        res = SearchDocsResult(
            query=clean_query,
            matches=[],
            coverage="none",
            error=ToolError(
                code="search_error",
                message=f"Failed to query handbook vector store: {type(exc).__name__}: {exc}",
                retryable=True,
            ),
            source_refs=[],
        )
        audit_tool_call("search_onboarding_docs", {"query": query, "top_k": top_k}, "error", res, 0)
        return res

