from toon_format.langchain import ToonSerializer, ToonOutputParser
from langchain_core.documents import Document


def test_serializer():
    docs = [Document(page_content={"name": "Ak", "skill": "Noob"})]
    result = ToonSerializer().transform_documents(docs)
    assert "name:Ak" in result[0].page_content


def test_parser():
    toon = "name:Ak\nage:22"
    result = ToonOutputParser().parse(toon)
    assert result["name"] == "Ak"