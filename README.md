# LangGraph RAG Chatbot with Web Search Fallback and Persistent Memory

An AI chatbot that answers questions using a personal knowledge base (via
Retrieval-Augmented Generation) and automatically falls back to a live web
search when the knowledge base doesn't have a good answer — all orchestrated
as a LangGraph state graph, with persistent, thread-aware conversation memory.

## Objective

Build a chatbot that combines three capabilities that are each individually
common in AI applications, but require careful orchestration to work together
correctly: (1) grounding answers in a private document set via RAG, (2) an
automatic fallback to live web search when local documents don't cover the
question, and (3) remembering earlier turns in the same conversation.

## Architecture

```
User question
     │
     ▼
 [retrieve]  ── search Chroma vector DB (semantic search over document chunks)
     │
     ▼
 [decide_route]  ── is the best match close enough? (distance threshold)
     │                                    │
     │ yes (good match)                   │ no (weak/no match)
     ▼                                     ▼
 [generate]  ◄──────────────────────  [web_search]  ── live Tavily search
     │
     ▼
  Answer (LLM call, grounded in whichever context was found)
```

- **Retrieval (RAG):** documents are split into ~800-character chunks (respecting
  paragraph boundaries), embedded, and stored in a **Chroma** vector database.
  At query time, the question is embedded the same way and matched against the
  stored chunks using semantic similarity — not just keyword overlap.
- **Routing:** if the closest retrieved chunk's distance is above a threshold
  (meaning nothing in the knowledge base is a good match), the graph routes to
  a **Tavily** live web search instead of answering from weak/irrelevant context.
- **Generation:** the LLM (Claude, via `langchain-anthropic`) receives the
  original question plus whichever context was found (local chunks or web
  results) and generates the final answer.
- **Memory:** LangGraph's `MemorySaver` checkpointer tracks conversation state
  per `thread_id`, so the chatbot remembers earlier turns within a session and
  can even resume a previous conversation if restarted with the same thread ID.

## Knowledge base

The chatbot's knowledge base is built from this person's own project
documentation:
- Customer Segmentation Analysis (README + final report)
- Character-Level Language Model (README)

53 chunks total, built with paragraph-aware splitting and a small overlap
between adjacent chunks so facts near a chunk boundary aren't lost.

## What was tested vs. what requires your own API keys

This project needs two external services — an LLM (Claude, via Anthropic's
API) and live web search (Tavily) — both requiring free-tier API keys.

**Tested and verified working (no API key required):**
- Document loading and chunking (53 chunks from 3 markdown files)
- Embedding + Chroma vector store construction
- Semantic retrieval — verified that queries return chunks from the
  semantically correct source document (e.g. a question about loss values
  correctly retrieves from the Character-LM doc, not the customer segmentation
  doc)

**Requires your own API keys to run (code complete, not live-tested here):**
- LLM answer generation (Anthropic API)
- Web search fallback (Tavily API)
- Full end-to-end conversation flow with memory

This split exists because the development environment this was built in has
restricted network access (it can't reach every external API), not because of
any issue with the code itself — the LLM and web search integrations use
standard, well-documented LangChain patterns.

## How to run it yourself

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your API keys
cp .env.example .env
# then edit .env and paste in your real ANTHROPIC_API_KEY and TAVILY_API_KEY

# 3. Build the vector store (one-time, or whenever you update the knowledge base)
python src/vector_store.py

# 4. Start chatting
python src/chat.py
```

## Example interaction (expected behavior)

```
You: What loss did the character-level model achieve?
[used: knowledge base]
Bot: The model's training loss dropped from 4.41 to 1.63 over 2,000
     iterations, with validation loss following a similar trend from 4.40
     to 1.79 — confirming it learned generalizable patterns rather than
     memorizing the training text.

You: What's the weather in Delhi right now?
[used: web search]
Bot: [live weather result, since this isn't in the knowledge base]

You: Can you remind me what the first thing I asked was?
[used: knowledge base]
Bot: You first asked about the loss achieved by the character-level model.
```

## Limitations

- **Retrieval threshold is a fixed heuristic**, not learned — it may
  occasionally route to web search when the knowledge base actually had a
  decent answer, or vice versa. A production system would tune this against
  a labeled test set.
- **No re-ranking step** — retrieval returns the top-k chunks by embedding
  distance only; a production RAG system often adds a re-ranking model for
  better precision.
- **Chunking is paragraph-based, not semantic** — a more advanced approach
  would use semantic chunking (grouping by topic, not just paragraph breaks).
- **Single-collection knowledge base** — currently mixes all documents into
  one Chroma collection; a larger system might separate by project or add
  metadata filtering.

## Files

```
rag_chatbot/
├── data/
│   └── knowledge_base/          # Source markdown documents
├── src/
│   ├── document_loader.py       # Chunking logic
│   ├── vector_store.py           # Embeddings + Chroma vector DB
│   ├── graph.py                   # LangGraph state machine (routing, RAG, web search, LLM)
│   └── chat.py                     # CLI chat interface with persistent memory
├── outputs/
│   └── chroma_db/                # Persisted vector database (generated)
├── .env.example                  # Template for API keys
├── .gitignore
└── requirements.txt
```
