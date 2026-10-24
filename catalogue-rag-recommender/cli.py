"""Ask the recommender from the terminal.   python cli.py "strong tea for the morning" """
import argparse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from rag.chunking import STRATEGIES
from rag.recommender import Recommender


def main():
    parser = argparse.ArgumentParser(description="Product recommendation RAG")
    parser.add_argument("query")
    parser.add_argument("--strategy", choices=STRATEGIES, default="whole")
    parser.add_argument("--store", choices=["memory", "pgvector"], default="memory")
    parser.add_argument("--llm", action="store_true", help="phrase the answer with an LLM (needs ANTHROPIC_API_KEY)")
    args = parser.parse_args()
    store = None
    if args.store == "pgvector":
        from rag.pgvector_store import PgVectorStore

        store = PgVectorStore()
    recommender = Recommender(args.strategy, store=store)
    print(recommender.llm_reply(args.query) if args.llm else recommender.reply(args.query))


if __name__ == "__main__":
    main()
