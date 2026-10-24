"""Optional Shopify Admin REST lookup.

Used only when SHOPIFY_STORE (e.g. my-store.myshopify.com) and SHOPIFY_TOKEN are set.
Otherwise the agent reads data/orders.json so everything runs offline.
"""
import json
import os
import re
import urllib.parse
import urllib.request

API_VERSION = "2024-10"


def is_configured() -> bool:
    return bool(os.getenv("SHOPIFY_STORE") and os.getenv("SHOPIFY_TOKEN"))


def _digits(value) -> str:
    return re.sub(r"\D", "", value or "")


def fetch_order(order_number: str):
    """Return a normalised order dict (same shape as orders.json entries) or None."""
    store = os.environ["SHOPIFY_STORE"]
    token = os.environ["SHOPIFY_TOKEN"]
    number = order_number.upper().replace("ORD-", "")
    query = urllib.parse.urlencode({"name": f"#{number}", "status": "any"})
    url = f"https://{store}/admin/api/{API_VERSION}/orders.json?{query}"
    request = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
    with urllib.request.urlopen(request, timeout=10) as response:
        orders = json.loads(response.read().decode("utf-8")).get("orders", [])
    if not orders:
        return None
    order = orders[0]
    fulfillment = (order.get("fulfillments") or [{}])[0]
    phone = (
        order.get("phone")
        or (order.get("customer") or {}).get("phone")
        or (order.get("shipping_address") or {}).get("phone")
    )
    status = order.get("fulfillment_status") or "processing"
    return {
        "status": "delivered" if status == "fulfilled" and fulfillment.get("shipment_status") == "delivered" else ("shipped" if status in ("fulfilled", "partial") else "processing"),
        "items": [line.get("name", "") for line in order.get("line_items", [])],
        "courier": fulfillment.get("tracking_company"),
        "tracking_number": fulfillment.get("tracking_number"),
        "phone_last4": _digits(phone)[-4:],
    }
