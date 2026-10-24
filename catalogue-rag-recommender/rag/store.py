"""Vector stores. InMemoryStore runs anywhere; PgVectorStore lives in pgvector_store.py."""


def dot(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))


class InMemoryStore:
    def __init__(self):
        self.items = []  # (sku, text, vector)

    def add(self, chunks, vectors):
        for chunk, vector in zip(chunks, vectors):
            self.items.append((chunk.sku, chunk.text, vector))

    def search(self, vector, k: int):
        """Return [(sku, score)] best chunk per product, highest score first."""
        best = {}
        for sku, _text, stored in self.items:
            score = dot(vector, stored)
            if score > best.get(sku, -1.0):
                best[sku] = score
        return sorted(best.items(), key=lambda pair: -pair[1])[:k]
