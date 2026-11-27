"""Provider-neutral evidence selection, validation and answer contract."""

import json
import re
from dataclasses import dataclass
from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.search import SearchHit, technical_terms

PROMPT_VERSION = "extractive-v2"
SYNTHESIS_PROMPT_VERSION = "synthesis-v3"

_NUMBER = r"(?<![\w.,])(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?"
_BYTE_QUANTITY = re.compile(rf"({_NUMBER})[\s-]+bytes?\b", re.IGNORECASE)
_NUMBER_LITERAL = re.compile(rf"{_NUMBER}(?!\w|[.,][0-9])")


class Citation(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    chunk_id: str
    quote: str = Field(min_length=1, max_length=600)


class SourcedCitation(Citation):
    document_id: str
    document_title: str
    page_number: int | None = None
    claim: str | None = None


class Selection(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    citations: list[Citation] = Field(max_length=3)


class Claim(Citation):
    claim: str = Field(min_length=1, max_length=400)


class Synthesis(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    claims: list[Claim] = Field(max_length=3)
    unanswered: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(max_length=3)


@dataclass(frozen=True)
class Generated:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ProviderFailure(Exception):
    """Internal failure category without provider response text."""


class AnswerProvider(Protocol):
    def generate(self, query: str, evidence: dict[str, list[str]], *, deadline: float,
                 mode: str = "extractive") -> Generated: ...


class AnswerResponse(BaseModel):
    request_id: str
    status: Literal["ok", "insufficient_evidence", "degraded"]
    answer: str | None = None
    citations: list[SourcedCitation] = Field(default_factory=list)
    sources: list[SearchHit] = Field(default_factory=list)
    latency_ms: float = 0
    reason: Literal[
        "no_matching_evidence", "no_eligible_documents", "question_consent_required",
        "provider_abstained", "provider_not_configured", "provider_timeout",
        "provider_rate_limited", "provider_failure", "input_budget",
        "validation_rejected", "partial_answer", "no_quotable_evidence",
    ] | None = None
    unanswered: list[str] = Field(default_factory=list)


class InvalidSelection(ValueError):
    """Safe validation reason, without generated text."""


def eligible_hits(hits, public_docs):
    return [hit for hit in hits if (
        (hit.title, hit.source_url, hit.text) in public_docs if hit.document_type == "seed"
        else hit.external_ok
    )]


def public_evidence(hits: list[SearchHit], public_docs: frozenset[tuple[str, str, str]],
                    query: str = "") -> dict[str, list[str]]:
    """Pick a bounded set of exact excerpts, favoring new query terms and pages."""
    pool = []
    seen = set()
    terms = {term.replace(",", "") for term in technical_terms(query, limit=24)}
    for hit in eligible_hits(hits, public_docs):
        for sentence in re.split(r"(?<=[.!?])\s+", hit.text):
            key = " ".join(sentence.casefold().split())
            if key and len(sentence) <= 600 and key not in seen:
                seen.add(key)
                sentence_terms = {term.replace(",", "") for term in
                                  re.findall(r"[a-z0-9_]+(?:[.,-][a-z0-9_]+)*", key)}
                pool.append((hit, sentence, terms & sentence_terms))
    evidence: dict[str, list[str]] = {}
    covered, locations = set(), set()
    remaining = 2600
    for _ in range(12):
        pool = [row for row in pool if len(row[1]) <= remaining and
                (row[0].chunk_id in evidence or len(evidence) < 6)]
        if not pool:
            break
        chosen = max(range(len(pool)), key=lambda i: (
            len(pool[i][2] - covered), bool(pool[i][2]) and
            (pool[i][0].document_id, pool[i][0].page_number) not in locations, len(pool[i][2]),
        ))
        hit, sentence, matches = pool.pop(chosen)
        evidence.setdefault(hit.chunk_id, []).append(sentence)
        remaining -= len(sentence)
        covered.update(matches)
        locations.add((hit.document_id, hit.page_number))
    return evidence


def validated_selection(output: Generated, evidence: dict[str, list[str]],
                        mode: str = "extractive") -> tuple[list[Citation], list[str]]:
    if len(output.text) > 8192:
        raise InvalidSelection("output_too_large")
    try:
        data = json.loads(output.text)
    except (json.JSONDecodeError, RecursionError):
        raise InvalidSelection("invalid_json") from None
    try:
        result = (Synthesis if mode == "synthesis" else Selection).model_validate(data)
    except ValidationError:
        raise InvalidSelection("schema_invalid") from None
    citations = result.claims if isinstance(result, Synthesis) else result.citations
    seen = set()
    for citation in citations:
        key = (citation.chunk_id, citation.quote)
        if citation.chunk_id not in evidence:
            raise InvalidSelection("unknown_context_id")
        if citation.quote not in evidence[citation.chunk_id]:
            raise InvalidSelection("quote_mismatch")
        if key in seen:
            raise InvalidSelection("duplicate_citation")
        if isinstance(citation, Claim):
            # Byte counts may have implicit units in the source (for example a page-size range).
            byte_values = {value.replace(",", "") for value in _BYTE_QUANTITY.findall(citation.claim)}
            if byte_values and not byte_values <= {
                value.replace(",", "") for value in _NUMBER_LITERAL.findall(citation.quote)
            }:
                raise InvalidSelection("byte_value_missing_from_quote")
        seen.add(key)
    return citations, result.unanswered if isinstance(result, Synthesis) else []
