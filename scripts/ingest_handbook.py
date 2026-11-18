"""Handbook ingestion script for Onboarding assistant.

Reads all markdown files in data/handbook/, parses front matter, chunks markdown
hierarchically by heading, embeds using sentence-transformers/all-MiniLM-L6-v2,
and persists embeddings into ChromaDB with cosine similarity space.
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config

HANDBOOK_DIR = Path(__file__).resolve().parent.parent / "data" / "handbook"
CHROMA_STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "chroma_store"
SUMMARY_FILE = HANDBOOK_DIR / "ingest_summary.json"

CHUNK_TARGET_CHARS = 1200
CHUNK_OVERLAP_CHARS = 150
CHUNK_MIN_CHARS = 200


def parse_front_matter(content: str, file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse YAML front matter from markdown file. Fails loudly if missing."""
    if not content.startswith("---"):
        raise ValueError(f"CRITICAL INGEST ERROR: Missing front matter in {file_path}")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"CRITICAL INGEST ERROR: Malformed front matter in {file_path}")

    fm_raw = parts[1].strip()
    body = parts[2].strip()

    metadata: Dict[str, Any] = {}
    for line in fm_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            metadata[k.strip()] = v.strip()

    required_keys = ["source_url", "origin"]
    missing = [k for k in required_keys if k not in metadata]
    if missing:
        raise ValueError(f"CRITICAL INGEST ERROR: Front matter missing required keys {missing} in {file_path}")

    return metadata, body


def split_section_text(text: str, target: int = CHUNK_TARGET_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> List[str]:
    """Split a section's text into overlapping chunks if it exceeds target length."""
    if len(text) <= target:
        return [text]

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + target, text_len)
        if end < text_len:
            # Try to break at paragraph or sentence boundary
            newline_break = text.rfind("\n\n", start, end)
            if newline_break != -1 and newline_break > start + 300:
                end = newline_break + 2
            else:
                period_break = text.rfind(". ", start, end)
                if period_break != -1 and period_break > start + 300:
                    end = period_break + 2

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break
        start = max(start + 1, end - overlap)

    return chunks


def chunk_markdown_file(file_path: Path, rel_path: str) -> List[Dict[str, Any]]:
    """Chunk a markdown document hierarchically by headings (# .. ###)."""
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()

    front_matter, body = parse_front_matter(full_content, file_path)
    lines = body.splitlines()

    heading_stack: List[Tuple[int, str]] = []
    current_section_lines: List[str] = []
    raw_sections: List[Tuple[str, str]] = []  # (heading_path, text)

    def get_current_heading_path() -> str:
        if not heading_stack:
            return rel_path
        headings = [h[1] for h in heading_stack]
        return f"{rel_path} > " + " > ".join(headings)

    for line in lines:
        match = re.match(r"^(#{1,3})\s+(.*)$", line)
        if match:
            # New heading found; flush previous section
            if current_section_lines:
                sec_text = "\n".join(current_section_lines).strip()
                if sec_text:
                    raw_sections.append((get_current_heading_path(), sec_text))
                current_section_lines = []

            level = len(match.group(1))
            heading_title = match.group(2).strip()

            # Pop higher or equal levels
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, heading_title))
        else:
            current_section_lines.append(line)

    if current_section_lines:
        sec_text = "\n".join(current_section_lines).strip()
        if sec_text:
            raw_sections.append((get_current_heading_path(), sec_text))

    # Process and size chunks
    chunks: List[Dict[str, Any]] = []
    pending_text = ""
    pending_heading = ""

    for heading_path, text in raw_sections:
        sub_chunks = split_section_text(text)
        for sub in sub_chunks:
            if len(sub) < CHUNK_MIN_CHARS and pending_text:
                # Merge small chunk into previous and retain heading context
                pending_text += "\n\n" + sub
                sub_heading_last = heading_path.split(" > ")[-1]
                if sub_heading_last not in pending_heading:
                    pending_heading += f" / {sub_heading_last}"
            else:
                if pending_text:
                    chunks.append({
                        "heading_path": pending_heading,
                        "text": pending_text,
                        "file": rel_path,
                        "url": front_matter.get("source_url", ""),
                        "origin": front_matter.get("origin", "repo_docs"),
                    })
                pending_text = sub
                pending_heading = heading_path

    if pending_text:
        chunks.append({
            "heading_path": pending_heading,
            "text": pending_text,
            "file": rel_path,
            "url": front_matter.get("source_url", ""),
            "origin": front_matter.get("origin", "repo_docs"),
        })

    return chunks


def ingest_handbook() -> int:
    print("--- [Onboarding assistant] Handbook Ingest ---")
    if not HANDBOOK_DIR.exists():
        print(f"FAILED: Handbook directory {HANDBOOK_DIR} does not exist. Run scripts/fetch_handbook.py first.")
        return 1

    md_files = list(HANDBOOK_DIR.glob("**/*.md"))
    # Exclude SOURCES.md from embedding
    md_files = [f for f in md_files if f.name != "SOURCES.md"]

    if not md_files:
        print(f"FAILED: No markdown files found in {HANDBOOK_DIR}!")
        return 1

    print(f"Found {len(md_files)} markdown files in handbook.")
    all_chunks: List[Dict[str, Any]] = []

    for file_path in md_files:
        rel_path = file_path.relative_to(HANDBOOK_DIR).as_posix()
        try:
            chunks = chunk_markdown_file(file_path, rel_path)
            all_chunks.extend(chunks)
            print(f"  Processed {rel_path} -> {len(chunks)} chunks")
        except Exception as e:
            print(f"FAILED to process {rel_path}: {e}")
            return 1

    print(f"Total chunks generated: {len(all_chunks)}")

    # Lazy-load sentence-transformers model
    print("Loading embedding model 'all-MiniLM-L6-v2' (CPU)...")
    try:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as exc:
        print(f"FAILED: Could not load SentenceTransformer model. Check network or PyTorch installation: {exc}")
        return 1

    # Embed chunk texts
    chunk_texts_for_embedding = [
        f"[{c['heading_path']}]\n{c['text']}" for c in all_chunks
    ]
    print(f"Generating embeddings for {len(chunk_texts_for_embedding)} chunks...")
    embeddings = embedder.encode(chunk_texts_for_embedding, show_progress_bar=True, normalize_embeddings=True)

    # Initialize ChromaDB
    print(f"Persisting to ChromaDB at {CHROMA_STORE_DIR}...")
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_STORE_DIR))
        # Clear or reset collection for a clean deterministic ingest
        try:
            client.delete_collection("handbook_docs")
        except Exception:
            pass

        collection = client.create_collection(
            name="handbook_docs",
            metadata={"hnsw:space": "cosine"},
        )

        ids = [f"chunk_{idx}" for idx in range(len(all_chunks))]
        metadatas = [
            {
                "file": c["file"],
                "heading_path": c["heading_path"],
                "url": c["url"],
                "origin": c["origin"],
            }
            for c in all_chunks
        ]
        documents = [c["text"] for c in all_chunks]

        # Add to ChromaDB in batches
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            end_idx = min(i + batch_size, len(ids))
            collection.add(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx].tolist(),
                metadatas=metadatas[i:end_idx],
                documents=documents[i:end_idx],
            )
        print("ChromaDB ingestion complete.")
    except Exception as exc:
        print(f"FAILED: Error interacting with ChromaDB: {exc}")
        return 1

    # Write ingest summary
    today_formatted = datetime.datetime.now().strftime("%d %b %Y").lstrip("0")
    summary = {
        "documents": len(md_files),
        "chunks": len(all_chunks),
        "ingest_date": today_formatted,
        "target_repo": config.target_repo,
    }
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n--- Ingest Summary ---")
    print(f"Documents:   {summary['documents']}")
    print(f"Sections:    {summary['chunks']}")
    print(f"Ingest Date: {summary['ingest_date']}")
    print(f"Summary saved to {SUMMARY_FILE}")
    print("SUCCESS: Handbook ingestion successfully completed.")
    return 0


if __name__ == "__main__":
    sys.exit(ingest_handbook())

