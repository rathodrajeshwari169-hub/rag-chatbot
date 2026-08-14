"""
document_loader.py — Load knowledge base documents and split them into chunks
suitable for embedding and retrieval.

Chunking strategy: split by paragraph/section first (respects natural document
structure), then further split any chunk that's still too long. This keeps
each chunk semantically coherent instead of cutting mid-sentence.
"""

import os
import glob
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str      # which file this chunk came from
    chunk_id: str     # unique id, e.g. "character_lm_project.md::3"


def load_markdown_files(folder_path):
    """Read every .md file in a folder into (filename, text) pairs."""
    docs = []
    for path in sorted(glob.glob(os.path.join(folder_path, "*.md"))):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        docs.append((os.path.basename(path), text))
    return docs


def split_into_chunks(text, max_chunk_chars=800, overlap_chars=100):
    """Split text on blank lines (paragraphs/sections) first, then merge small
    paragraphs together and split any that are still too long.

    overlap_chars: a small amount of text repeated between consecutive chunks
    so a fact split across a chunk boundary isn't lost entirely from either chunk.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chunk_chars:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= max_chunk_chars:
                current = para
            else:
                # Paragraph itself is too long — hard split with overlap
                for i in range(0, len(para), max_chunk_chars - overlap_chars):
                    chunks.append(para[i:i + max_chunk_chars])
                current = ""
    if current:
        chunks.append(current)

    return chunks


def build_chunks(folder_path, max_chunk_chars=800, overlap_chars=100):
    """Load all markdown files in a folder and return a flat list of Chunk objects."""
    docs = load_markdown_files(folder_path)
    all_chunks = []
    for filename, text in docs:
        pieces = split_into_chunks(text, max_chunk_chars, overlap_chars)
        for i, piece in enumerate(pieces):
            all_chunks.append(Chunk(text=piece, source=filename, chunk_id=f"{filename}::{i}"))
    return all_chunks


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    KB_PATH = os.path.join(BASE_DIR, "data", "knowledge_base")
    chunks = build_chunks(KB_PATH)
    print(f"Loaded {len(chunks)} chunks from knowledge base:")
    for c in chunks[:5]:
        print(f"  [{c.chunk_id}] {c.text[:80].strip()}...")
