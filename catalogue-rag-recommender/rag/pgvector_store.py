"""Optional Postgres + pgvector store.

Start Postgres:   docker compose up -d
Install driver:   pip install "psycopg[binary]"
Use:              python cli.py --store pgvector "strong tea"
Set DATABASE_URL (default matches docker-compose.yml). Embedding size must match HashingEmbedder.dim.
"""
import os

DEFAULT_URL = "postgresql://postgres:postgres@localhost:5432/catalogue"


class PgVectorStore:
    def __init__(self, dim: int = 512, url: str = None):
        import psycopg  # imported here so the in-memory path needs no Postgres driver

        self.dim = dim
        self.conn = psycopg.connect(url or os.getenv("DATABASE_URL", DEFAULT_URL), autocommit=True)
        self.conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        self.conn.execute("DROP TABLE IF EXISTS chunks")
        self.conn.execute(f"CREATE TABLE chunks (id serial PRIMARY KEY, sku text, text text, embedding vector({dim}))")

    @staticmethod
    def _literal(vector) -> str:
        return "[" + ",".join(f"{v:.6f}" for v in vector) + "]"

    def add(self, chunks, vectors):
        with self.conn.cursor() as cur:
            for chunk, vector in zip(chunks, vectors):
                cur.execute(
                    "INSERT INTO chunks (sku, text, embedding) VALUES (%s, %s, %s::vector)",
                    (chunk.sku, chunk.text, self._literal(vector)),
                )

    def search(self, vector, k: int):
        sql = (
            "SELECT sku, MAX(1 - (embedding <=> %s::vector)) AS score FROM chunks "
            "GROUP BY sku ORDER BY score DESC LIMIT %s"
        )
        with self.conn.cursor() as cur:
            cur.execute(sql, (self._literal(vector), k))
            return [(sku, float(score)) for sku, score in cur.fetchall()]
