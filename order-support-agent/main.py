"""Chat with the agent in the terminal.   python main.py --backend mock"""
import argparse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent.agent import SupportAgent
from agent.llm import get_backend


def main():
    parser = argparse.ArgumentParser(description="D2C order-support agent")
    parser.add_argument("--backend", choices=["mock", "anthropic"], default="mock")
    args = parser.parse_args()
    agent = SupportAgent(get_backend(args.backend))
    history = []
    print("D2C support agent. Type 'exit' to quit.")
    print("Try: Where is my order ORD-1001? phone ends 4321")
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in {"exit", "quit"}:
            break
        result = agent.reply(text, history)
        print(f"Agent: {result.text}")
        if result.tools_used:
            print(f"  [tools: {', '.join(result.tools_used)}]")


if __name__ == "__main__":
    main()
