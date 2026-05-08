# Features Backlog

## Publish
- [ ] Publish to PyPI — `python -m build` + `twine upload dist/*`

## Core Capabilities
- [ ] **Streaming support** — providers return full responses; add token streaming
- [ ] **Tool / function calling** — agents cannot call external tools yet
- [ ] **Memory / context persistence** — agents lose state between stages; add cross-stage memory
- [ ] **Observability** — add tracing, structured logging, and per-stage cost tracking

## Providers
- [ ] OpenAI native provider (without LiteLLM wrapper)
- [ ] Gemini provider
- [ ] AWS Bedrock provider

## Developer Experience
- [ ] Web UI / playground — run pipelines without writing code
- [ ] Type stubs / py.typed marker for IDE completion
- [ ] Async streaming CLI output (live token display in `swarm run`)
