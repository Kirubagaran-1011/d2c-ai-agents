from types import SimpleNamespace

from agent.agent import SupportAgent
from agent.llm import AnthropicBackend, MockBackend
from evals.run_evals import load_cases, run, summarise
from whatsapp.parser import extract_message


def test_mock_agent_order_flow():
    result = SupportAgent(MockBackend()).reply("Where is ORD-1001? phone 4321", [])
    assert result.tools_used == ["get_order_status"] and "shipped" in result.text.lower()


def test_history_is_kept():
    history = []
    SupportAgent(MockBackend()).reply("Hi", history)
    assert [m["role"] for m in history] == ["user", "assistant"]


def test_all_evals_pass_on_mock_backend():
    summary = summarise(run("mock"))
    assert summary["passed"] == summary["cases"] == len(load_cases())


class FakeClient:
    """Pretends to be the Anthropic SDK: first asks for a tool, then answers."""

    def __init__(self):
        self.calls = 0
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.calls += 1
        usage = SimpleNamespace(input_tokens=10, output_tokens=5)
        if self.calls == 1:
            block = SimpleNamespace(type="tool_use", id="t1", name="get_return_policy", input={})
        else:
            assert kwargs["messages"][-1]["content"][0]["type"] == "tool_result"
            block = SimpleNamespace(type="text", text="You can return unopened items within 7 days.")
        return SimpleNamespace(content=[block], usage=usage)


def test_anthropic_backend_tool_loop_with_fake_client():
    agent = SupportAgent(AnthropicBackend(client=FakeClient()))
    result = agent.reply("What is the return policy?", [])
    assert result.tools_used == ["get_return_policy"]
    assert "7 days" in result.text and result.input_tokens == 20 and result.output_tokens == 10


def test_whatsapp_parser():
    payload = {"entry": [{"changes": [{"value": {"messages": [{"from": "919999999999", "type": "text", "text": {"body": "hi"}}]}}]}]}
    assert extract_message(payload) == ("919999999999", "hi")
    assert extract_message({}) is None
