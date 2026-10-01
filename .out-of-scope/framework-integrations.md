# Framework Integrations

This package does not ship integrations for LLM or data frameworks – no LangChain serializers or output parsers, no agent-framework adapters, no pandas API, and no MCP server. The core library encodes Python values to TOON and decodes TOON back to Python values. Everything else builds on those two calls.

## Why this is out of scope

Every one of these integrations is a thin layer over `encode()` and `decode()`, but each one ties the package to someone else's release cycle. An integration for LangChain, pandas, or an MCP server means another optional dependency to pin, another API that breaks on its own schedule, and another test matrix – for code that is a single call on the user's side:

```python
# pandas
encode({"customers": df[["Customer", "Customer question"]].to_dict("records")})

# Pydantic models, dataclasses, agent-framework payloads
encode(model.model_dump())
encode(dataclasses.asdict(obj))
```

The DataFrame example already emits a tabular array (§9.3), `customers[3]{Customer,"Customer question"}:` with one row per record, so a dedicated pandas API wouldn't produce anything better.

Johann closed the LangChain integration with the same reasoning: "a LangChain integration is out of scope for the core library, which should stay focused on encoding and decoding. This would be a great fit as a separate package (e.g. `toon-langchain`)" ([#45](https://github.com/toon-format/toon-python/pull/45#issuecomment-4073109814)). The MCP server got the same answer: "toon-python should stay focused on encoding/decoding. If there's appetite for this, it would be better as a separate repository" ([#31](https://github.com/toon-format/toon-python/pull/31#issuecomment-4073055880)).

Integrations are welcome as separate packages, or on the framework's side.

The optional `pydantic` extra ([#46](https://github.com/toon-format/toon-python/pull/46)) exists and is not part of this decision. Host-type normalization through a `JSONEncoder.default`-style hook is allowed by the spec (§3) and is a regular feature request, not an integration.

## Prior requests

- [#31](https://github.com/toon-format/toon-python/pull/31): "Add Model Context Protocol (MCP) Server for TOON Format"
- [#44](https://github.com/toon-format/toon-python/discussions/44): "Agent framework integration" (LangChain, Pydantic AI)
- [#45](https://github.com/toon-format/toon-python/pull/45): "feat(langchain): add ToonSerializer and ToonOutputParser"
- [#56](https://github.com/toon-format/toon-python/issues/56): "An interface with Pandas"
