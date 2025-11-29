from __future__ import annotations

from typing import Any, Sequence

from langchain_core.documents import Document
from langchain_core.output_parsers import BaseOutputParser

from .. import encode, decode


class ToonSerializer:
    """Convert LangChain Documents to TOON format (30–60% fewer tokens)."""
    
    def transform_documents(
        self, documents: Sequence[Document], **kwargs: Any
    ) -> list[Document]:
        return [
            Document(
                page_content=encode(doc.page_content),
                metadata={**doc.metadata, "format": "toon"}
            )
            for doc in documents
        ]

    async def atransform_documents(
        self, documents: Sequence[Document], **kwargs: Any
    ) -> list[Document]:
        return self.transform_documents(documents, **kwargs)


class ToonOutputParser(BaseOutputParser):
    """Parse TOON responses from LLMs back to Python objects."""
    
    def parse(self, text: str) -> Any:
        return decode(text.strip())

    @property
    def _type(self) -> str:
        return "toon"