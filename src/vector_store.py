"""
vector_store.py — Build and query a Chroma vector database over the knowledge
base chunks, using a local (free, no API key) embedding model.

Uses sentence-transformers' all-MiniLM-L6-v2: a small, fast, well-regarded
open-source embedding model that runs entirely on your machine.
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from chromadb import Documents, EmbeddingFunction, Embeddings
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from document_loader import build_chunks

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(BASE_DIR, "data", "knowledge_base")
DB_PATH = os.path.join(BASE_DIR, "outputs", "chroma_db")

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "project_knowledge_base"

# Set to True only in network-restricted sandboxes that can't reach
# huggingface.co to download the real embedding model. On a normal machine
# with internet access, leave this False — sentence-transformers is far
# better quality (true semantic meaning, not just word overlap).
USE_OFFLINE_FALLBACK = os.environ.get("RAG_OFFLINE_EMBEDDINGS", "false").lower() == "true"


class TfidfEmbeddingFunction(EmbeddingFunction):
    """A simple offline fallback that mimics the embedding interface using
    TF-IDF (keyword-overlap based, not true semantic meaning). Only used when
    the real embedding model can't be downloaded (no internet access to
    huggingface.co). Fit once on the corpus, then reused for queries."""

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(max_features=384)
        self._fitted = False

    def fit(self, corpus):
        self.vectorizer.fit(corpus)
        self._fitted = True

    def __call__(self, input: Documents) -> Embeddings:
        if not self._fitted:
            self.fit(input)  # first call (during collection.add) fits on the corpus
        vecs = self.vectorizer.transform(input).toarray()
        return vecs.tolist()


_shared_tfidf_fn = None  # keep one fitted instance alive across add() and query()


def get_embedding_function():
    """Real semantic embedding model (requires internet access), or an
    offline TF-IDF fallback for network-restricted environments."""
    global _shared_tfidf_fn
    if USE_OFFLINE_FALLBACK:
        if _shared_tfidf_fn is None:
            _shared_tfidf_fn = TfidfEmbeddingFunction()
        return _shared_tfidf_fn
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )


def build_vector_store(kb_path=KB_PATH, db_path=DB_PATH, reset=True):
    """Chunk all documents, embed them, and store them in a persistent Chroma DB."""
    print("Building vector store...")
    chunks = build_chunks(kb_path)
    print(f"  Loaded {len(chunks)} chunks from {kb_path}")

    client = chromadb.PersistentClient(path=db_path)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # collection didn't exist yet — nothing to delete

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )

    collection.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[{"source": c.source} for c in chunks],
    )
    print(f"  Embedded and stored {len(chunks)} chunks in Chroma at {db_path}")
    return collection


def load_vector_store(db_path=DB_PATH):
    """Reconnect to an already-built vector store."""
    client = chromadb.PersistentClient(path=db_path)
    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )


def search(collection, query, top_k=3):
    """Search the vector store for the chunks most relevant to a query.

    Returns a list of dicts with text, source, and distance (lower = more similar).
    """
    results = collection.query(query_texts=[query], n_results=top_k)
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        hits.append({"text": doc, "source": meta["source"], "distance": dist})
    return hits


if __name__ == "__main__":
    collection = build_vector_store()

    print("\n" + "=" * 50)
    print("TEST SEARCHES")
    print("=" * 50)

    test_queries = [
        "What loss did the character-level model achieve?",
        "How were the two loyalty scores validated?",
        "What data quality issue was found in the customer dataset?",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        hits = search(collection, q, top_k=2)
        for h in hits:
            print(f"  [{h['source']}, distance={h['distance']:.3f}] {h['text'][:150].strip()}...")
