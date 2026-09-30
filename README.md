# release-one-gate

A minimal example of one semantic decision driving one branch:

```
START -> classify_with_jev -> billing | technical -> END
```

Jev (TypeSafe's decision model) answers a single typed `Choice` question about a
synthetic support message. The typed answer is stored in LangGraph state, a plain
Python function picks the branch, and the branch returns a fixed acknowledgement.
LangSmith traces the run. There is no generative LLM in the flow.

## Article

This project accompanies the Medium article
[What evidence should an AI release approver inspect?](https://medium.com/@pkhafizov/what-evidence-should-an-ai-release-approver-inspect-24e2a9bbb371)
by Pavel Khafizov. This repository is the small runnable example behind it.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # skip if you already have a .env
```

Fill in `.env`:

| Variable | Needed |
|---|---|
| `TYPESAFE_API_KEY` | Always |
| `LANGSMITH_TRACING` | Set to `true` to trace |
| `LANGSMITH_API_KEY` | When tracing is on |
| `LANGSMITH_PROJECT` | When tracing is on (`gate-article`) |


## Run

```bash
uv run python main.py
```

Two synthetic messages are classified, one request each. For each one the script
prints the category, confidence, probabilities, and acknowledgement. If a Jev request
fails, the error is printed and the exit code is 1. No decision is substituted.

To send traces to a different project for one run:

```bash
LANGSMITH_PROJECT=another-project uv run python main.py
```

## Test

```bash
uv run pytest
```

One parameterized test covers both branches with an injected classifier response. It
needs no credentials, makes no network calls, and turns tracing off.

## What to inspect in LangSmith

Open the project named in `LANGSMITH_PROJECT`. Each input produces one trace:

```
support_router
├── classify_with_jev
│   ├── TypeSafeClassifier   <- the Jev request
│   └── route                <- the Python branch selection
└── billing | technical      <- the branch that ran
```

- `TypeSafeClassifier`: the input shows the message and the question. The output shows
  `choice`, `probabilities`, `confidence`, the model id, and token usage.
- `route`: the category returned by the routing function.
- `billing` or `technical`: only the selected branch appears.

## Limits

- A typed answer and a visible trace show what was decided and which path ran. They do
  not show that the decision was correct, that the system is secure, or that it is
  ready for production.
- Confidence describes how concentrated the probabilities are. It is not a measure of
  correctness. This example routes on the choice alone and has no low-confidence path.
- Two easy inputs are not an evaluation. This repository makes no speed, cost, or
  accuracy claims.
- Messages are sent to TypeSafe and, when tracing is on, to LangSmith. Check each
  provider's current data retention terms before sending anything that is not
  synthetic.
- `langchain-typesafe` is an alpha release and `TypeSafeClassifier` is marked beta, so
  the version is pinned. The model id is pinned to `jev-1.13.0`.

Sources are listed in [SOURCES.md](SOURCES.md).
