"""Two ways to cut a product into searchable chunks, so we can measure which retrieves better."""
from dataclasses import dataclass

STRATEGIES = ("whole", "fields")


@dataclass
class Chunk:
    sku: str
    text: str


def chunk_product(product: dict, strategy: str) -> list:
    sku = product["sku"]
    tags = ", ".join(product["tags"])
    if strategy == "whole":
        return [Chunk(sku, f"{product['name']}. {product['category']}. {product['description']} Tags: {tags}")]
    if strategy == "fields":
        return [
            Chunk(sku, f"{product['name']}. {product['category']}"),
            Chunk(sku, product["description"]),
            Chunk(sku, f"Tags: {tags}"),
        ]
    raise ValueError(f"Unknown chunking strategy '{strategy}'. Use one of {STRATEGIES}.")
