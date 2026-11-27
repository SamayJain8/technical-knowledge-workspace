"""Exact cosine search over compatible, attributed Oracle chunks."""

import math
import re

import oracledb
from pydantic import BaseModel

from app.embeddings import MiniLM


def technical_terms(query: str, limit: int = 8) -> list[str]:
    """Keep numeric values and technical identifiers alongside ordinary words."""
    tokens = re.findall(r"[a-z0-9_]+(?:[.,-][a-z0-9_]+)*", query.casefold())
    stop = {"what", "which", "when", "where", "does", "that", "with", "using",
            "could", "should", "about", "have", "information", "stored", "many"}
    special = [token for token in tokens if len(token) <= 40 and
               (any(char.isdigit() for char in token) or "_" in token or "-" in token)]
    words = [token for token in tokens if 4 <= len(token) <= 40 and token not in stop]
    return list(dict.fromkeys(special + words))[:limit]


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    source_url: str | None
    provenance: str
    text: str
    similarity_score: float
    document_type: str = "seed"
    page_number: int | None = None
    external_ok: bool = False
    fusion_score: float | None = None


def search(connection: oracledb.Connection, model: MiniLM, query: str,
           top_k: int, threshold: float, *, document_ids=(), document_type=None,
           strategy="semantic", candidate_limit: int | None = None) -> list[SearchHit]:
    if type(top_k) is not int or not 1 <= top_k <= 10:
        raise ValueError("top_k must be between 1 and 10")
    limit = top_k if candidate_limit is None else candidate_limit
    if not top_k <= limit <= 16:
        raise ValueError("Invalid candidate limit")
    vector = model.encode([query])[0]
    scope = ["c.embedding_version = :version", "(d.source_url IS NOT NULL OR d.content_hash IS NOT NULL)"]
    binds = {"vector": vector, "version": model.fingerprint, "top_k": 24 if strategy == "hybrid" else limit}
    if document_ids:
        names = [f"doc{i}" for i in range(len(document_ids))]
        binds.update(zip(names, document_ids, strict=True))
        scope.append(f"d.document_id IN ({', '.join(':' + name for name in names)})")
    if document_type:
        scope.append("d.document_type = :kind")
        binds["kind"] = document_type
    projection = """
            SELECT c.chunk_id, c.document_id, d.title, d.source_url, d.provenance,
                   c.chunk_text, VECTOR_DISTANCE(c.embedding, :vector, COSINE) AS distance,
                   d.document_type, c.page_number, d.external_ok
            FROM document_chunks c JOIN documents d ON d.document_id = c.document_id
            WHERE """

    def hits(rows):
        return [
            SearchHit(chunk_id=row[0], document_id=row[1], title=row[2], source_url=row[3],
                      provenance=row[4], text=row[5], similarity_score=1.0 - row[6],
                      document_type=row[7], page_number=row[8], external_ok=bool(row[9]))
            for row in rows if row[6] is not None and math.isfinite(row[6])
        ]

    with connection.cursor() as cursor:
        cursor.execute(projection + " AND ".join(scope) +
                       " ORDER BY distance, c.chunk_id FETCH EXACT FIRST :top_k ROWS ONLY",
                       binds, fetch_lobs=False)
        dense = [hit for hit in hits(cursor) if hit.similarity_score >= threshold]
        if strategy != "hybrid":
            return dense

        terms = technical_terms(query)
        if not terms:
            return dense[:limit]
        names = [f"term{i}" for i in range(len(terms))]
        binds.update(zip(names, terms, strict=True))
        matches = []
        weights = []
        for name, term in zip(names, terms, strict=True):
            if any(char.isdigit() for char in term) or "_" in term or "-" in term:
                # Oracle regex boundaries keep offset 24 from matching 240.
                pattern = term.replace(".", "[.]")
                if re.fullmatch(r"\d{1,3}(?:,\d{3})+", term):
                    pattern = f"({pattern}|{term.replace(',', '')})"
                elif re.fullmatch(r"\d{4,9}", term):
                    pattern = f"({pattern}|{int(term):,})"
                binds[name] = f"(^|[^[:alnum:]_]){pattern}([^[:alnum:]_]|$)"
                matches.append(f"REGEXP_LIKE(c.chunk_text, :{name}, 'i')")
                weights.append(2)
            else:
                matches.append(f"DBMS_LOB.INSTR(LOWER(c.chunk_text), :{name}) > 0")
                weights.append(1)
        score = " + ".join(f"CASE WHEN {match} THEN {weight} ELSE 0 END"
                           for match, weight in zip(matches, weights, strict=True))
        binds["term_min"] = min(2, sum(weights))
        cursor.execute(projection + " AND ".join(scope) + f" AND ({score}) >= :term_min"
                       f" ORDER BY ({score}) DESC, distance, c.chunk_id FETCH FIRST :top_k ROWS ONLY",
                       binds, fetch_lobs=False)
        lexical = [hit for hit in hits(cursor) if hit.similarity_score >= threshold]
    combined = {}
    rank_scores: dict[str, float] = {}
    for branch in (dense, lexical):
        for rank, hit in enumerate(branch, 1):
            combined[hit.chunk_id] = hit
            rank_scores[hit.chunk_id] = rank_scores.get(hit.chunk_id, 0.0) + 1 / (60 + rank)
    ordered = sorted(combined, key=lambda key: (-rank_scores[key], key))[:limit]
    return [combined[key].model_copy(update={"fusion_score": rank_scores[key]}) for key in ordered]
