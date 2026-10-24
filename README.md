# D2C AI Agents

Two small, tested projects for D2C (direct-to-consumer) brands in India:

| Folder | What it is |
|---|---|
| [`order-support-agent/`](order-support-agent) | AI assistant that answers customers about orders, returns and products (English / Hinglish), with tool calling, guardrails and evals. Optional WhatsApp and Shopify connections. |
| [`catalogue-rag-recommender/`](catalogue-rag-recommender) | Product recommendation bot using embeddings and retrieval (RAG), with a hallucination check and a retrieval eval. Optional pgvector storage. |

Both run fully offline for testing (no API key needed). Add an Anthropic API key to use a real model.

## Quick start

```bash
cd order-support-agent
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
python main.py --backend mock
```

Do the same inside `catalogue-rag-recommender/`.

## Architecture (project 1)

```
Customer message
   -> input guardrail (empty / too long / prompt injection / refund or discount -> human)
   -> LLM with tools (get_order_status, search_products, get_return_policy)
   -> output guardrail (blocks claims like "I have processed your refund")
   -> reply
```

## Honest notes

- The `mock` backend is a tiny rule-based stand-in so tests run offline. It is **not** an LLM. Real quality numbers come from `python -m evals.run_evals --backend anthropic`.
- Order and product data are sample files. Shopify and WhatsApp code is included but was not tested against a live store or WhatsApp number; test it with your own credentials.
- The recommender eval uses a 15-product catalogue and queries written by the author, so it is a pipeline check, not a benchmark.
