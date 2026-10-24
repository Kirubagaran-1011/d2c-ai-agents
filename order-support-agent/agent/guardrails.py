"""Input and output guardrails. Plain rules, easy to read and test."""
import re
from dataclasses import dataclass

HANDOFF_REPLY = (
    "I can't do that myself, but I've passed your request to our support team. "
    "They will get back to you shortly."
)
REFUSAL_REPLY = "I can only help with orders, returns and our products. What would you like to know?"

INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above) (instructions|rules)",
    r"system prompt",
    r"reveal .*(prompt|instructions|rules)",
    r"you are now",
    r"developer mode",
    r"jailbreak",
]
# Things the agent must never do on its own: money actions and discounts.
ACTION_PATTERNS = [
    r"\brefund",
    r"money back",
    r"paisa wapas",
    r"paise wapas",
    r"\bdiscount",
    r"\bcoupon",
    r"promo code",
    r"\bcancel",
]
# Output claims the agent must never make.
FORBIDDEN_OUTPUT = [
    r"(i|we)('ve| have) (processed|issued|initiated|approved) (a |your )?(refund|cancellation)",
    r"refund (has been|is) (processed|issued|approved)",
    r"here is (a |your )?(discount|coupon|promo)",
    r"use (code|coupon) [A-Z0-9]{4,}",
]


@dataclass
class GuardResult:
    allowed: bool
    reply: str = ""
    reason: str = ""
    handoff: bool = False


def _matches(patterns, text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def check_input(text: str) -> GuardResult:
    if not text or not text.strip():
        return GuardResult(False, "Please type your question and I'll help.", "empty")
    if len(text) > 1000:
        return GuardResult(False, "That message is too long. Please send a shorter one.", "too_long")
    if _matches(INJECTION_PATTERNS, text):
        return GuardResult(False, REFUSAL_REPLY, "injection")
    asks_policy = re.search(r"\bpolic(y|ies)\b", text, flags=re.IGNORECASE)
    if _matches(ACTION_PATTERNS, text) and not asks_policy:
        return GuardResult(False, HANDOFF_REPLY, "needs_human", handoff=True)
    return GuardResult(True)


def check_output(text: str) -> GuardResult:
    if not text or not text.strip():
        return GuardResult(False, HANDOFF_REPLY, "empty_output", handoff=True)
    if _matches(FORBIDDEN_OUTPUT, text):
        return GuardResult(False, HANDOFF_REPLY, "forbidden_claim", handoff=True)
    return GuardResult(True)
