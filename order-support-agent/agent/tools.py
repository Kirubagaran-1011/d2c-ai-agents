"""Tools the agent can call. Each tool returns a plain dict (JSON friendly)."""
import json
import re
from pathlib import Path

from agent import shopify

DATA = Path(__file__).resolve().parent.parent / "data"

TOOL_SCHEMAS = [
    {
        "name": "get_order_status",
        "description": "Look up the status and tracking of an order. Needs the order id (like ORD-1001) and the last 4 digits of the phone number on the order for verification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order id such as ORD-1001"},
                "phone_last4": {"type": "string", "description": "Last 4 digits of the phone number on the order"},
            },
            "required": ["order_id", "phone_last4"],
        },
    },
    {
        "name": "search_products",
        "description": "Search the product catalogue by what the customer wants (type, taste, use, price). Returns up to 3 matching products.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What the customer is looking for"}},
            "required": ["query"],
        },
    },
    {
        "name": "get_return_policy",
        "description": "Get the store's return, replacement and refund policy text.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _load_json(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _tokens(text: str):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def get_order_status(order_id: str, phone_last4: str) -> dict:
    order_id = (order_id or "").strip().upper()
    if shopify.is_configured():
        order = shopify.fetch_order(order_id)
    else:
        order = _load_json("orders.json").get(order_id)
    # Same message for "not found" and "wrong phone" so we never leak whether an id exists.
    if order is None or str(order.get("phone_last4")) != str(phone_last4).strip():
        return {"error": "No order found with those details. Please check the order id and phone digits."}
    safe = {k: v for k, v in order.items() if k != "phone_last4" and v is not None}
    safe["order_id"] = order_id
    return safe


def search_products(query: str, max_results: int = 3) -> dict:
    wanted = _tokens(query)
    scored = []
    for product in _load_json("products.json"):
        haystack = _tokens(" ".join([product["name"], product["category"], product["description"], " ".join(product["tags"])]))
        score = len(wanted & haystack)
        if score:
            scored.append((score, product))
    scored.sort(key=lambda item: (-item[0], item[1]["price_inr"]))
    results = [
        {"sku": p["sku"], "name": p["name"], "price_inr": p["price_inr"], "in_stock": p["in_stock"], "description": p["description"]}
        for _, p in scored[:max_results]
    ]
    return {"results": results}


def get_return_policy() -> dict:
    return {"policy": (DATA / "policy.md").read_text(encoding="utf-8").strip()}


TOOL_FUNCTIONS = {
    "get_order_status": get_order_status,
    "search_products": search_products,
    "get_return_policy": get_return_policy,
}


def run_tool(name: str, arguments: dict) -> dict:
    """Run a tool safely. Never raises: errors come back as data the model can read."""
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        return {"error": f"Unknown tool {name}"}
    try:
        return function(**(arguments or {}))
    except TypeError as exc:
        return {"error": f"Bad arguments for {name}: {exc}"}
    except Exception as exc:  # network or data errors must not crash the chat
        return {"error": f"Tool {name} failed: {exc}"}
