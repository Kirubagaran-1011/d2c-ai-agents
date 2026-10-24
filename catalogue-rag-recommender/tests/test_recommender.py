from rag.chunking import chunk_product
from rag.embedder import HashingEmbedder
from rag.recommender import Recommender, find_unknown_skus, load_catalogue, parse_max_price
from rag.store import dot


def test_embedder_is_unit_length_and_stable():
    e = HashingEmbedder()
    v = e.embed("strong morning tea")
    assert abs(dot(v, v) - 1.0) < 1e-9 and v == e.embed("strong morning tea")


def test_chunking_strategies():
    product = load_catalogue()[0]
    assert len(chunk_product(product, "whole")) == 1
    assert len(chunk_product(product, "fields")) == 3


def test_obvious_query_ranks_right_product_first():
    assert Recommender().recommend("south indian filter coffee")[0]["sku"] == "SKU-006"


def test_out_of_stock_excluded_by_default():
    skus = [p["sku"] for p in Recommender().recommend("honey ginger lemon sore throat tea", k=5)]
    assert "SKU-012" not in skus


def test_price_filter():
    assert parse_max_price("tea under Rs 300") == 300
    assert all(p["price_inr"] <= 300 for p in Recommender().recommend("tea under 300", k=5))


def test_reply_only_mentions_catalogue_skus():
    r = Recommender()
    assert find_unknown_skus(r.reply("strong tea"), r.by_sku) == []
    assert find_unknown_skus("Try SKU-999 today", r.by_sku) == ["SKU-999"]


def test_no_match_message():
    assert "couldn't find" in Recommender().reply("zzzz qqqq")
