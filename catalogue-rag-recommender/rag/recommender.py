"""Retrieve products for a query, then write a reply that can only mention catalogue items."""
import json
import os
import re
from pathlib import Path

from rag.chunking import chunk_product
from rag.embedder import HashingEmbedder
from rag.store import InMemoryStore

CATALOGUE_PATH = Path(__file__).resolve().parent.parent / "data" / "catalogue.json"
SKU_PATTERN = re.compile(r"SKU-\d+", re.IGNORECASE)
PRICE_PATTERN = re.compile(r"(?:under|below|less than|upto|up to|within)\s*(?:rs\.?|inr|₹)?\s*(\d+)", re.IGNORECASE)


def load_catalogue(path=None) -> list:
    return json.loads(Path(path or CATALOGUE_PATH).read_text(encoding="utf-8"))


def parse_max_price(query: str):
    match = PRICE_PATTERN.search(query)
    return int(match.group(1)) if match else None


def find_unknown_skus(text: str, valid_skus) -> list:
    """Hallucination check: every SKU mentioned in a reply must exist in the catalogue."""
    valid = {s.upper() for s in valid_skus}
    return [s for s in SKU_PATTERN.findall(text) if s.upper() not in valid]


class Recommender:
    def __init__(self, strategy="whole", store=None, embedder=None, catalogue=None):
        self.catalogue = catalogue if catalogue is not None else load_catalogue()
        self.by_sku = {p["sku"]: p for p in self.catalogue}
        self.embedder = embedder or HashingEmbedder()
        self.store = store or InMemoryStore()
        chunks = [c for p in self.catalogue for c in chunk_product(p, strategy)]
        self.store.add(chunks, [self.embedder.embed(c.text) for c in chunks])

    def recommend(self, query: str, k: int = 3, in_stock_only: bool = True) -> list:
        max_price = parse_max_price(query)
        hits = self.store.search(self.embedder.embed(query), len(self.catalogue))
        results = []
        for sku, score in hits:
            product = self.by_sku[sku]
            if in_stock_only and not product["in_stock"]:
                continue
            if max_price is not None and product["price_inr"] > max_price:
                continue
            if score <= 0:
                continue
            results.append({**product, "score": round(score, 3)})
            if len(results) == k:
                break
        return results

    def reply(self, query: str, k: int = 3) -> str:
        """Template reply built only from retrieved products (cannot invent items)."""
        results = self.recommend(query, k)
        if not results:
            return "I couldn't find a matching product. Try describing the type, taste or budget."
        lines = [f"- {p['name']} ({p['sku']}) at Rs {p['price_inr']}: {p['description']}" for p in results]
        return "Here are my picks:\n" + "\n".join(lines)

    def llm_reply(self, query: str, k: int = 3, client=None, model=None) -> str:
        """Optional: let an LLM phrase the answer, then verify it. Falls back to the template."""
        results = self.recommend(query, k)
        if not results:
            return self.reply(query, k)
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
        context = json.dumps([{"sku": p["sku"], "name": p["name"], "price_inr": p["price_inr"], "description": p["description"]} for p in results], ensure_ascii=False)
        response = client.messages.create(
            model=model,
            max_tokens=500,
            system="You recommend products. Use ONLY the products in the JSON provided. Mention each product's SKU and price exactly as given. Never mention any other product. Keep it short.",
            messages=[{"role": "user", "content": f"Customer asked: {query}\n\nProducts:\n{context}"}],
        )
        text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()
        if not text or find_unknown_skus(text, self.by_sku):
            return self.reply(query, k)  # reject a reply that mentions anything outside the catalogue
        return text
