"""LLM backends. Both return the same StepResult so the agent loop is identical.

AnthropicBackend  - real model with tool calling (needs ANTHROPIC_API_KEY).
MockBackend       - tiny rule-based stand-in so tests and the demo run offline.
                    It is NOT a model; use it only to test the pipeline.
"""
import json
import os
import re
from dataclasses import dataclass


@dataclass
class StepResult:
    content: list  # assistant content blocks as plain dicts
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def text(self) -> str:
        return "".join(b["text"] for b in self.content if b["type"] == "text").strip()

    @property
    def tool_calls(self) -> list:
        return [b for b in self.content if b["type"] == "tool_use"]


class AnthropicBackend:
    def __init__(self, model=None, client=None):
        if client is None:
            import anthropic  # imported here so the mock path needs no install

            client = anthropic.Anthropic()
        self.client = client
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    def step(self, system, messages, tools) -> StepResult:
        response = self.client.messages.create(
            model=self.model, max_tokens=1024, system=system, tools=tools, messages=messages
        )
        blocks = []
        for block in response.content:
            if block.type == "text":
                blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                blocks.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
        if not blocks:
            blocks.append({"type": "text", "text": ""})
        usage = getattr(response, "usage", None)
        return StepResult(blocks, getattr(usage, "input_tokens", 0) or 0, getattr(usage, "output_tokens", 0) or 0)


class MockBackend:
    PRODUCT_WORDS = ["recommend", "suggest", "show me", "price", "buy", "chahiye", "best", "gift", "tea", "chai", "coffee", "mug", "do you have", "under"]
    POLICY_WORDS = ["return", "exchange", "policy", "wapas", "replace"]

    def step(self, system, messages, tools) -> StepResult:
        last = messages[-1]["content"]
        if isinstance(last, list):  # tool results are in, write the final answer
            return StepResult([{"type": "text", "text": self._compose(last, messages)}])
        return self._decide(last)

    def _decide(self, text: str) -> StepResult:
        low = text.lower()
        order = re.search(r"ord-\d+", low)
        if order:
            rest = text.replace(order.group(0), "").replace(order.group(0).upper(), "")
            digits = re.search(r"(?<![\d-])(\d{4})(?!\d)", rest)
            if not digits:
                return StepResult([{"type": "text", "text": "Please share the last 4 digits of the phone number on the order so I can verify it."}])
            return self._call("get_order_status", {"order_id": order.group(0).upper(), "phone_last4": digits.group(1)})
        if any(word in low for word in self.POLICY_WORDS):
            return self._call("get_return_policy", {})
        if any(word in low for word in self.PRODUCT_WORDS):
            return self._call("search_products", {"query": text})
        return StepResult([{"type": "text", "text": "I can help with orders, returns and our products. What do you need?"}])

    @staticmethod
    def _call(name, arguments) -> StepResult:
        return StepResult([{"type": "tool_use", "id": f"mock_{name}", "name": name, "input": arguments}])

    @staticmethod
    def _compose(results, messages) -> str:
        names = {b["id"]: b["name"] for b in messages[-2]["content"] if b.get("type") == "tool_use"}
        parts = []
        for result in results:
            data = json.loads(result["content"])
            name = names.get(result["tool_use_id"], "")
            if "error" in data:
                parts.append(data["error"])
            elif name == "get_order_status":
                line = f"Order {data['order_id']} is {data['status']}."
                if data.get("courier"):
                    line += f" Courier: {data['courier']}, tracking {data.get('tracking_number', 'n/a')}."
                if data.get("expected_delivery"):
                    line += f" Expected delivery: {data['expected_delivery']}."
                if data.get("delivered_on"):
                    line += f" Delivered on {data['delivered_on']}."
                parts.append(line)
            elif name == "get_return_policy":
                parts.append(data["policy"])
            elif name == "search_products":
                found = data["results"]
                if not found:
                    parts.append("I couldn't find a matching product. Could you tell me more about what you want?")
                else:
                    items = "; ".join(f"{p['name']} (Rs {p['price_inr']}{'' if p['in_stock'] else ', out of stock'})" for p in found)
                    parts.append(f"You might like: {items}.")
        return " ".join(parts) or "Sorry, I could not find that."


def get_backend(kind: str):
    if kind == "mock":
        return MockBackend()
    if kind == "anthropic":
        return AnthropicBackend()
    raise ValueError(f"Unknown backend '{kind}'. Use 'mock' or 'anthropic'.")
