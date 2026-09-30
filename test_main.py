"""Offline routing test: no credentials, no network, no trace uploads."""

import pytest
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse
from langsmith import tracing_context

import main


@pytest.fixture(autouse=True)
def no_tracing(monkeypatch):
    # Importing `main` does not load .env, and tracing is forced off here in case
    # the shell exports it.
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    with tracing_context(enabled=False):
        yield


def injected_classifier(choice: str, probabilities: dict[str, float]):
    response = ClassifierResponse.model_validate(
        {
            "model": "injected",
            "answers": {
                main.QUESTION_ID: {
                    "type": "choice",
                    "choice": choice,
                    "probabilities": probabilities,
                    "confidence": 0.9,
                }
            },
        }
    )
    return RunnableLambda(lambda _request: response)


@pytest.mark.parametrize(
    ("message", "choice", "probabilities", "acknowledgement"),
    [
        (
            "I was charged twice.",
            "billing",
            {"billing": 0.97, "technical": 0.03},
            "Thanks - your message has been passed to the billing team.",
        ),
        (
            "The app crashes on launch.",
            "technical",
            {"billing": 0.02, "technical": 0.98},
            "Thanks - your message has been passed to technical support.",
        ),
    ],
    ids=["billing", "technical"],
)
def test_graph_runs_the_selected_branch(message, choice, probabilities, acknowledgement):
    graph = main.build_graph(injected_classifier(choice, probabilities))

    steps = list(graph.stream({"message": message}, stream_mode="updates"))

    executed = [node for step in steps for node in step]
    assert executed == ["classify_with_jev", choice]
    assert steps[-1][choice] == {"acknowledgement": acknowledgement}
