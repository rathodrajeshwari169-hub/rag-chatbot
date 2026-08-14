"""
graph.py — The LangGraph state machine that ties everything together.

Flow:
  1. retrieve       — search the vector DB for relevant chunks
  2. decide_route    — if the retrieved chunks look weak/irrelevant, fall back to web search
  3. web_search      — (conditional) search the live web via Tavily
  4. generate         — call the LLM with the question + whatever context we found

State is a TypedDict that flows through each node, accumulating information as
it goes — this is the core LangGraph pattern.
"""

import os
import sys
from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vector_store import load_vector_store, search as vector_search

# Distance threshold: if the BEST retrieved chunk's distance is above this,
# we treat the vector DB as "not having a good answer" and fall back to web search.
# (Distance is from the embedding model — lower = more semantically similar.
# This threshold should be tuned per embedding model; this default works
# reasonably for the sentence-transformers model in normal use.)
RETRIEVAL_DISTANCE_THRESHOLD = 1.0


class ChatState(TypedDict):
    question: str
    retrieved_chunks: List[dict]
    route: str                  # "rag" or "web_search"
    web_results: Optional[str]
    answer: str
    chat_history: List[dict]    # accumulated across turns via the checkpointer


def make_retrieve_node(collection):
    def retrieve(state: ChatState) -> ChatState:
        hits = vector_search(collection, state["question"], top_k=3)
        state["retrieved_chunks"] = hits
        return state
    return retrieve


def decide_route(state: ChatState) -> str:
    """Router: does the vector DB have a good enough answer, or should we
    fall back to a live web search?"""
    hits = state.get("retrieved_chunks", [])
    if not hits or hits[0]["distance"] > RETRIEVAL_DISTANCE_THRESHOLD:
        return "web_search"
    return "generate"


def make_web_search_node(tavily_client):
    def web_search_node(state: ChatState) -> ChatState:
        try:
            results = tavily_client.search(state["question"], max_results=3)
            summary = "\n\n".join(
                f"[{r['title']}] {r['content'][:300]}" for r in results.get("results", [])
            )
            state["web_results"] = summary
        except Exception as e:
            state["web_results"] = f"(Web search failed: {e})"
        return state
    return web_search_node


def make_generate_node(llm):
    def generate(state: ChatState) -> ChatState:
        # Build context from whichever source we used
        if state.get("web_results"):
            context = f"Web search results:\n{state['web_results']}"
        else:
            context = "\n\n---\n\n".join(
                f"[Source: {c['source']}]\n{c['text']}" for c in state.get("retrieved_chunks", [])
            )

        system_prompt = (
            "You are a helpful assistant answering questions about the user's "
            "personal data science and ML projects. Use the provided context to "
            "answer accurately. If the context doesn't contain the answer, say so "
            "honestly rather than making something up."
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {state['question']}"

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        state["answer"] = response.content
        return state
    return generate


def build_graph(collection, llm, tavily_client):
    """Wire together the state graph: retrieve -> route -> (web_search) -> generate."""
    graph = StateGraph(ChatState)

    graph.add_node("retrieve", make_retrieve_node(collection))
    graph.add_node("web_search", make_web_search_node(tavily_client))
    graph.add_node("generate", make_generate_node(llm))

    graph.set_entry_point("retrieve")
    graph.add_conditional_edges(
        "retrieve",
        decide_route,
        {"web_search": "web_search", "generate": "generate"},
    )
    graph.add_edge("web_search", "generate")
    graph.add_edge("generate", END)

    # MemorySaver gives us persistent, thread-aware conversation memory —
    # each conversation gets a thread_id, and LangGraph automatically tracks
    # state across turns for that thread.
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)
