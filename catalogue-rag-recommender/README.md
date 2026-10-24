# Product Recommendation Bot (RAG)

A chatbot that suggests products from a store catalogue and never makes up items.

**Tools & skills:** Python, embeddings, retrieval (RAG), pgvector (optional), hallucination check, retrieval evals, chunking comparison.

## How it works
1. Each product is cut into chunks (`whole` or `fields` strategy) and turned into vectors by `rag/embedder.py`.
2. A query is embedded and matched against the stored vectors; the best products come back (price and stock filters applied, e.g. "tea under 300").
3. The reply is built only from retrieved products. With `--llm`, a model phrases the reply and any SKU outside the catalogue makes the reply get rejected.

## Folder map
```
rag/       embedder.py, chunking.py, store.py, pgvector_store.py, recommender.py
data/      catalogue.json (15 sample products)
evals/     queries.jsonl, run_eval.py
tests/     pytest tests
cli.py     ask from the terminal
```

## Run it
```bash
pip install -r requirements.txt
python -m pytest -q
python cli.py "strong tea for the morning"
python -m evals.run_eval                 # compares chunking strategies
python cli.py --llm "gift for diwali"    # needs ANTHROPIC_API_KEY
```

## pgvector (optional)
```bash
docker compose up -d
pip install "psycopg[binary]"
python cli.py --store pgvector "filter coffee"
```
The pgvector path was not run against a live database when this was written; test it before you rely on it.

## Eval results
Run `python -m evals.run_eval` and paste your numbers:

| Strategy | hit@1 | hit@3 | hit@5 |
|---|---|---|---|
| whole | | | |
| fields | | | |

Note: the sample catalogue is small and the queries are easy, so grow both before quoting numbers.
