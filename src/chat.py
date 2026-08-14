"""
chat.py — Command-line chat interface for the RAG chatbot.

Loads API keys from a .env file (never hardcode keys in source code).
Each conversation gets a "thread_id" so LangGraph's memory checkpointer can
track history separately per conversation, and even resume a previous
conversation if you restart with the same thread_id.
"""

import os
import sys
import uuid

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from tavily import TavilyClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vector_store import load_vector_store, build_vector_store
from graph import build_graph

load_dotenv()  # reads .env file in the project root


def check_env():
    missing = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.environ.get("TAVILY_API_KEY"):
        missing.append("TAVILY_API_KEY")
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        print("Create a .env file in the project root with:")
        print("  ANTHROPIC_API_KEY=sk-ant-...")
        print("  TAVILY_API_KEY=tvly-...")
        sys.exit(1)


def main():
    check_env()

    print("Setting up... (loading vector store, connecting to LLM)")

    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "chroma_db")
    if not os.path.exists(db_path):
        print("No vector store found — building it now...")
        collection = build_vector_store()
    else:
        collection = load_vector_store()

    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0.3)
    tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    app = build_graph(collection, llm, tavily_client)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\nRAG Chatbot ready (thread: {thread_id[:8]})")
    print("Ask me about your projects, or anything else — I'll search my knowledge")
    print("base first, and fall back to the web if I don't have a good answer.")
    print("Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        if not question:
            continue

        result = app.invoke({"question": question}, config=config)

        route_used = "web search" if result.get("web_results") else "knowledge base"
        print(f"\n[used: {route_used}]")
        print(f"Bot: {result['answer']}\n")


if __name__ == "__main__":
    main()
