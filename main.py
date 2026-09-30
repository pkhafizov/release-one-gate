"""One semantic decision from Jev, one LangGraph branch, one LangSmith trace.

START -> classify_with_jev -> billing | technical -> END
"""

import os
import sys
from pathlib import Path
from typing import Literal, get_args

from dotenv import load_dotenv
from langchain_core.runnables import Runnable
from langchain_core.tracers.langchain import wait_for_all_tracers
from langchain_typesafe import (
    Choice,
    ClassifierRequest,
    ClassifierResponse,
    TypeSafeClassifier,
)
from langchain_typesafe.client import TypeSafeError
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

PROJECT_ROOT = Path(__file__).resolve().parent

# Pinned on purpose: the `jev-latest` alias moves when TypeSafe ships a release.
MODEL = "jev-1.13.0"

Category = Literal["billing", "technical"]
CATEGORIES: tuple[str, ...] = get_args(Category)

QUESTION_ID = "category"
QUESTIONS = {
    QUESTION_ID: Choice(
        instructions="Which support team should handle this message?",
        criteria={
            "billing": "Charges, refunds, invoices, or payment problems.",
            "technical": "Crashes, errors, bugs, or the product not working.",
        },
    )
}

ACKNOWLEDGEMENTS: dict[str, str] = {
    "billing": "Thanks - your message has been passed to the billing team.",
    "technical": "Thanks - your message has been passed to technical support.",
}

# Synthetic inputs. Nothing here comes from a real customer.
EXAMPLES = (
    "I was charged twice for my subscription this month. Please refund one charge.",
    "The app crashes every time I open the settings page.",
)

Classifier = Runnable[ClassifierRequest, ClassifierResponse]


class State(TypedDict, total=False):
    message: str
    answers: ClassifierResponse
    acknowledgement: str


def route(state: State) -> Category:
    """Pick the branch from the typed answer. Plain Python, no model call."""
    choice = state["answers"].choices[QUESTION_ID].choice
    if choice not in CATEGORIES:
        raise ValueError(f"Classifier returned an unknown category: {choice!r}")
    return choice


def billing(state: State) -> dict:
    return {"acknowledgement": ACKNOWLEDGEMENTS["billing"]}


def technical(state: State) -> dict:
    return {"acknowledgement": ACKNOWLEDGEMENTS["technical"]}


def build_graph(classifier: Classifier):
    def classify_with_jev(state: State) -> dict:
        # One request per input.
        request: ClassifierRequest = {
            "state": state["message"],
            "questions": QUESTIONS,
        }
        return {"answers": classifier.invoke(request)}

    return (
        StateGraph(State)
        .add_node("classify_with_jev", classify_with_jev)
        .add_node("billing", billing)
        .add_node("technical", technical)
        .add_edge(START, "classify_with_jev")
        .add_conditional_edges("classify_with_jev", route, list(CATEGORIES))
        .add_edge("billing", END)
        .add_edge("technical", END)
        .compile()
    )


def missing_config() -> list[str]:
    """Names of the variables this run needs and does not have."""
    required = ["TYPESAFE_API_KEY"]
    # LangSmith only traces when the value is exactly "true".
    if os.environ.get("LANGSMITH_TRACING") == "true":
        required += ["LANGSMITH_API_KEY", "LANGSMITH_PROJECT"]
    return [name for name in required if not os.environ.get(name, "").strip()]


def main() -> int:
    # Values already set in the process environment win over .env.
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    missing = missing_config()
    if missing:
        print(f"Missing configuration: {', '.join(missing)}", file=sys.stderr)
        return 1

    graph = build_graph(TypeSafeClassifier(model=MODEL))
    exit_code = 0
    try:
        for message in EXAMPLES:
            try:
                result = graph.invoke(
                    {"message": message},
                    config={"run_name": "support_router", "tags": ["one-gate"]},
                )
            except TypeSafeError as error:
                # No fallback decision: a failed call is reported, not replaced.
                print(
                    f"Jev request failed ({type(error).__name__}): {error}",
                    file=sys.stderr,
                )
                exit_code = 1
                continue

            answer = result["answers"].choices[QUESTION_ID]
            probabilities = ", ".join(
                f"{label}={value:.3f}"
                for label, value in sorted(answer.probabilities.items())
            )
            print(f"message:         {message}")
            print(f"category:        {answer.choice}")
            print(f"confidence:      {answer.confidence:.3f}")
            print(f"probabilities:   {probabilities}")
            print(f"acknowledgement: {result['acknowledgement']}")
            print()
    finally:
        # Traces upload in the background; send them before the process exits.
        wait_for_all_tracers()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
