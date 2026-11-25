import argparse
import json
import os
from pathlib import Path

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langsmith import tracing_context

ORDERS = {
    "demo-1001": {"item": "Damaged mug", "eligible": True},
    "demo-1002": {"item": "Used shoes", "eligible": False},
    "demo-1003": {"item": "Unopened book", "eligible": True},
    "demo-1004": {"item": "Used coat", "eligible": False},
    "demo-1005": {"item": "Damaged toy", "eligible": True},
    "demo-1006": {"item": "Used paint", "eligible": False},
}
PROMPT = Path(__file__).resolve().parents[2] / "prompts" / "refund.txt"


@tool
def check_refund_eligibility(order_id: str) -> dict[str, str | bool]:
    """Look up refund eligibility for a synthetic order by its ID."""
    if order_id not in ORDERS:
        return {"found": False}
    return {"found": True, **ORDERS[order_id]}


class ScriptedRefundModel(FakeMessagesListChatModel):
    """Exercise the LangChain tool loop without calling a hosted model."""

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        return self


def demo_model(order_id: str, prompt: str) -> ScriptedRefundModel:
    order = ORDERS.get(order_id)
    if "always call check_refund_eligibility" not in prompt.lower():
        if order is None:
            answer = "I could not find that demo order."
        else:
            answer = "Your refund is eligible." if order["eligible"] else "Your refund is not eligible."
        return ScriptedRefundModel(responses=[AIMessage(content=answer)])

    answer = ""  # Default to empty answer if calling tool
    return ScriptedRefundModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "check_refund_eligibility",
                    "args": {"order_id": order_id},
                    "id": "demo-eligibility-check",
                }],
            ),
            AIMessage(content=answer),
        ]
    )


def run_refund_agent(model, prompt: str, question: str, *, middleware=()):
    """Run the same agent from the CLI or a local optimization runner."""
    with tracing_context(enabled=False):
        return create_agent(
            model, tools=[check_refund_eligibility], system_prompt=prompt, middleware=middleware
        ).invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"recursion_limit": 8},
        )["messages"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic refund agent.")
    parser.add_argument("--order-id", choices=[*ORDERS, "demo-missing"], default="demo-1002")
    parser.add_argument("--prompt", type=Path, default=PROMPT)
    parser.add_argument("--model", help="Opt in to a hosted model instead of the scripted model.")
    args = parser.parse_args()
    prompt = args.prompt.read_text(encoding="utf-8").strip()
    if not prompt:
        parser.error("The prompt file must not be empty.")

    if args.model:
        if not (os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_BASE_URL")):
            parser.error("--model requires OPENAI_API_KEY and an explicit OPENAI_BASE_URL.")
        model = ChatOpenAI(model=args.model, timeout=30, max_retries=0)
    else:
        model = demo_model(args.order_id, prompt)

    messages = run_refund_agent(model, prompt, f"Is order {args.order_id} eligible for a refund?")
    print(json.dumps({
        "mode": "model" if args.model else "scripted",
        "order_id": args.order_id,
        "tool_calls": [message.name for message in messages if isinstance(message, ToolMessage)],
        "answer": messages[-1].content,
    }, indent=2))


if __name__ == "__main__":
    main()
