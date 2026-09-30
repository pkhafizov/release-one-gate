# Sources

Official pages consulted while building this example, read on 2026-09-29 and
2026-09-30. Vendor pages describe announced capabilities and designs. Their
performance claims were not independently verified here.

## Integration and API

- [TypeSafe integrations - Docs by LangChain](https://docs.langchain.com/oss/python/integrations/providers/typesafe): `TypeSafeClassifier`, request shape, tracing.
- [langchain-typesafe on PyPI](https://pypi.org/project/langchain-typesafe/): version 0.0.1a3. The installed package source was read to confirm types, errors, and trace metadata.
- [TypeSafe introduction](https://docs.typesafe.ai/introduction): what Jev returns.
- [TypeSafe Choice primitive](https://docs.typesafe.ai/primitives/choice): question and answer fields, meaning of confidence.
- [TypeSafe models](https://docs.typesafe.ai/models): model ids and aliases, data handling.
- [TypeSafe documentation index](https://docs.typesafe.ai/llms.txt)

## Tracing

- [Trace with LangGraph](https://docs.langchain.com/langsmith/trace-with-langgraph)
- [Trace with LangChain](https://docs.langchain.com/langsmith/trace-with-langchain): environment variables, flushing traces before exit.

## Background

- [Building Production Agents with Jev and LangGraph](https://www.langchain.com/blog/building-prod-with-jev-and-langgraph): the pattern this example reduces to one decision.
- [LangSmith Engine v2](https://www.langchain.com/blog/langsmith-engine-v2-redteam): background only. Nothing from Engine is implemented here.
