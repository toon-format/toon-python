# Framework Integrations

This package does not ship integrations for LLM or data frameworks – no LangChain serializers or output parsers, no agent-framework adapters, no pandas API, and no MCP server.

## Why this is out of scope

Each integration is a thin layer over one encode or decode call, but it ties the package to another project's dependencies, API, and release cycle. Johann closed the LangChain pull request on that line: "a LangChain integration is out of scope for the core library, which should stay focused on encoding and decoding. This would be a great fit as a separate package (e.g. `toon-langchain`)" ([#45](https://github.com/toon-format/toon-python/pull/45#issuecomment-4073109814)). The MCP server got the same answer ([#31](https://github.com/toon-format/toon-python/pull/31#issuecomment-4073055880)).

Integrations are welcome as separate packages or on the framework's side. The optional `pydantic` extra ([#46](https://github.com/toon-format/toon-python/pull/46)) is not affected.

## Prior requests

- [#31](https://github.com/toon-format/toon-python/pull/31) – "Add Model Context Protocol (MCP) Server for TOON Format"
- [#44](https://github.com/toon-format/toon-python/discussions/44) – "Agent framework integration" (LangChain, Pydantic AI)
- [#45](https://github.com/toon-format/toon-python/pull/45) – "feat(langchain): add ToonSerializer and ToonOutputParser"
- [#56](https://github.com/toon-format/toon-python/issues/56) – "An interface with Pandas"
