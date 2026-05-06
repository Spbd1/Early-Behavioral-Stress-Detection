"""Lightweight local RAG primitives for keyword explanation and grounding.

The retriever is intentionally small and deterministic. It ranks local knowledge snippets by token
overlap and never decides alerts; downstream reviewers inspect retrieved evidence before promotion.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[\w'-]+", re.UNICODE)


@dataclass(frozen=True)
class KnowledgeDocument:
    """One local knowledge-base snippet."""

    doc_id: str
    title: str
    source_type: str
    text: str
    geography: str = "global"
    locale: str = "en"
    version: str = "v1"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


@dataclass(frozen=True)
class RetrievedContext:
    """Retrieved grounding context for a candidate keyword."""

    doc_id: str
    title: str
    source_type: str
    snippet: str
    score: float
    geography: str
    locale: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


class LocalKnowledgeBase:
    """Read/write a local JSONL knowledge base built from project-owned materials."""

    def __init__(self, documents: Iterable[KnowledgeDocument] | None = None) -> None:
        self.documents = list(documents or [])

    @classmethod
    def from_jsonl(cls, path: str | Path) -> LocalKnowledgeBase:
        """Load documents from JSONL; missing files produce an empty KB for tests and scaffolds."""
        kb_path = Path(path)
        if not kb_path.exists():
            return cls([])
        documents = []
        for line in kb_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                documents.append(KnowledgeDocument(**json.loads(line)))
        return cls(documents)

    def to_jsonl(self, path: str | Path) -> None:
        """Persist the knowledge base as JSONL."""
        kb_path = Path(path)
        kb_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(document.to_dict(), sort_keys=True) for document in self.documents]
        kb_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    @classmethod
    def from_text_files(cls, paths: Iterable[str | Path], source_type: str) -> LocalKnowledgeBase:
        """Create snippets from project paper, ontology docs, codebooks, reports, or notes files."""
        documents: list[KnowledgeDocument] = []
        for path in paths:
            text_path = Path(path)
            text = text_path.read_text(encoding="utf-8")
            for idx, chunk in enumerate(_chunk_text(text)):
                documents.append(
                    KnowledgeDocument(
                        doc_id=f"{text_path.stem}:{idx + 1}",
                        title=text_path.name,
                        source_type=source_type,
                        text=chunk,
                    )
                )
        return cls(documents)


class LightweightRAGRetriever:
    """Deterministic lexical retriever for local behavioral-stress knowledge."""

    def __init__(self, knowledge_base: LocalKnowledgeBase) -> None:
        self.knowledge_base = knowledge_base
        self._doc_tokens = [set(_tokens(document.text)) for document in knowledge_base.documents]
        self._idf = self._build_idf(self._doc_tokens)

    def retrieve(
        self,
        query: str,
        *,
        geography: str | None = None,
        locale: str | None = None,
        top_k: int = 3,
    ) -> list[RetrievedContext]:
        """Return the best local contexts for a query and optional geo/locale hints."""
        query_tokens = set(_tokens(query))
        if not query_tokens:
            return []
        scored: list[RetrievedContext] = []
        for document, doc_tokens in zip(
            self.knowledge_base.documents, self._doc_tokens, strict=False
        ):
            lexical_score = sum(self._idf.get(token, 1.0) for token in query_tokens & doc_tokens)
            geo_bonus = 0.25 if geography and document.geography in {geography, "global"} else 0.0
            locale_bonus = 0.15 if locale and document.locale == locale else 0.0
            score = lexical_score + geo_bonus + locale_bonus
            if score <= 0:
                continue
            scored.append(
                RetrievedContext(
                    doc_id=document.doc_id,
                    title=document.title,
                    source_type=document.source_type,
                    snippet=_snippet(document.text, query_tokens),
                    score=round(score, 4),
                    geography=document.geography,
                    locale=document.locale,
                )
            )
        return sorted(scored, key=lambda item: (-item.score, item.doc_id))[:top_k]

    @staticmethod
    def _build_idf(doc_tokens: list[set[str]]) -> dict[str, float]:
        total = max(len(doc_tokens), 1)
        frequencies: dict[str, int] = {}
        for tokens in doc_tokens:
            for token in tokens:
                frequencies[token] = frequencies.get(token, 0) + 1
        return {
            token: math.log((1 + total) / (1 + count)) + 1 for token, count in frequencies.items()
        }


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _chunk_text(text: str, *, max_chars: int = 900) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 > max_chars and current:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


def _snippet(text: str, query_tokens: set[str], *, max_chars: int = 260) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    best = max(
        sentences, key=lambda sentence: len(set(_tokens(sentence)) & query_tokens), default=text
    )
    return best[: max_chars - 1].rstrip() + ("…" if len(best) >= max_chars else "")
