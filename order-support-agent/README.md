# WhatsApp Order-Support Agent for a D2C Store

An AI assistant that answers customers about their orders, the return policy and products, in English or Hinglish.

**Tools & skills:** Python, LLM API (Anthropic Claude), tool/function calling, guardrails, evals, Shopify Admin API, WhatsApp Cloud API, FastAPI.

## What it does
- **Order status** from the order id plus the last 4 phone digits (wrong details never reveal anything).
- **Return policy** read from `data/policy.md`.
- **Product search** over `data/products.json`; it only recommends real products.
- **Guardrails:** refunds, cancellations and discounts go to a human; prompt-injection attempts are refused; replies that promise a refund are blocked.

## Folder map
```
agent/        tools.py, guardrails.py, llm.py, agent.py, shopify.py
data/         orders.json, products.json, policy.md  (sample data)
evals/        cases.jsonl, run_evals.py
whatsapp/     webhook.py, parser.py
tests/        pytest tests
main.py       terminal chat
```

## Run it
```bash
pip install -r requirements.txt
python -m pytest -q                      # 17 tests, offline
python main.py --backend mock            # chat, no API key
cp .env.example .env                     # add ANTHROPIC_API_KEY
python main.py --backend anthropic       # chat with a real model
python -m evals.run_evals --backend anthropic
```

## Evals
17 cases in `evals/cases.jsonl` (orders, policy, products, Hinglish, wrong phone, refund, discount, prompt injection, out of scope). The runner reports pass rate, latency, tokens and (if you set `INPUT_PRICE_INR_PER_M` / `OUTPUT_PRICE_INR_PER_M`) cost per chat.

| Backend | Pass rate | Avg latency | Cost / chat |
|---|---|---|---|
| anthropic | _run the eval and fill in_ | | |

## WhatsApp
```bash
pip install -r requirements-whatsapp.txt
uvicorn whatsapp.webhook:app --port 8000
```
Expose port 8000 with a tunnel and set the webhook URL (`/webhook`) in Meta's developer dashboard using the values in `.env.example`.

## Shopify
Set `SHOPIFY_STORE` and `SHOPIFY_TOKEN` in `.env`. Order names like `ORD-1001` map to Shopify `#1001`. Without them the agent uses `data/orders.json`.
