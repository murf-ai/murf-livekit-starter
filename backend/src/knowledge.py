import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "knowledge"
TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u0900-\u097f]+", re.IGNORECASE)


@dataclass(frozen=True)
class KnowledgeDocument:
    title: str
    source: str
    content: str


class KnowledgeBase:
    """Small local document retriever with source-labelled results."""

    def __init__(self, directory: str | Path = DEFAULT_KNOWLEDGE_PATH) -> None:
        self.directory = Path(directory)
        self.documents = tuple(self._load_documents())

    def _load_documents(self) -> list[KnowledgeDocument]:
        documents = []
        for path in sorted(self.directory.glob("*.md")):
            lines = path.read_text(encoding="utf-8").splitlines()
            metadata = {}
            content_start = 0
            for index, line in enumerate(lines):
                if not line.strip():
                    content_start = index + 1
                    break
                key, separator, value = line.partition(":")
                if not separator:
                    break
                metadata[key.casefold().strip()] = value.strip()
            content = "\n".join(lines[content_start:]).strip()
            if content:
                documents.append(
                    KnowledgeDocument(
                        title=metadata.get("title", path.stem),
                        source=metadata.get("source", "Unknown source"),
                        content=content,
                    )
                )
        return documents

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {token.casefold() for token in TOKEN_PATTERN.findall(text)}

    def search(self, query: str, limit: int = 2) -> list[KnowledgeDocument]:
        query_tokens = self._tokens(query)
        if not query_tokens:
            return []
        ranked = []
        for document in self.documents:
            searchable = f"{document.title} {document.content}"
            score = len(query_tokens & self._tokens(searchable))
            if score:
                ranked.append((score, document))
        ranked.sort(key=lambda item: (-item[0], item[1].title))
        return [document for _, document in ranked[:limit]]

    def grounded_context(self, query: str) -> str:
        matches = self.search(query)
        if not matches:
            return "No relevant passage was found in the knowledge base."
        return "\n\n".join(
            f"SOURCE: {document.title} ({document.source})\n{document.content}"
            for document in matches
        )
