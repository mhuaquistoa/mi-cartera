"""Base de conocimiento: manual de criterios de inversión -> búsqueda BM25.

Cada criterio está redactado con palabras propias a partir de la bibliografía
y guarda el libro y la página del PDF de donde sale.

La búsqueda es léxica (BM25) y no usa embeddings: así corre en el servidor
gratuito sin descargar un modelo, y el índice es un JSON legible.
"""
import json
import math
import re
import unicodedata
from collections import Counter

from . import settings as S

STOP = set("de la el en y a los las del que un una por con para se es al lo su como mas o no si the of and to in is".split())


def _tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return [t for t in re.findall(r"[a-z0-9]+", text) if t not in STOP and len(t) > 1]


def load() -> list[dict]:
    return json.loads(S.KNOWLEDGE.read_text(encoding="utf-8")) if S.KNOWLEDGE.exists() else []


def search(query: str, chunks: list[dict], k: int = S.TOP_K) -> list[dict]:
    """BM25 (k1=1.5, b=0.75). Devuelve los k fragmentos con puntaje mayor que cero."""
    if not chunks:
        return []
    docs = [_tokens(c["texto"]) for c in chunks]
    avg = sum(map(len, docs)) / len(docs)
    df = Counter(t for d in docs for t in set(d))
    q = _tokens(query)
    scored = []
    for c, d in zip(chunks, docs):
        tf = Counter(d)
        score = sum(
            math.log(1 + (len(docs) - df[t] + 0.5) / (df[t] + 0.5))
            * tf[t] * 2.5 / (tf[t] + 1.5 * (0.25 + 0.75 * len(d) / avg))
            for t in q if t in tf
        )
        if score > 0:
            scored.append((score, c))
    return [dict(c, puntaje=round(s, 2)) for s, c in sorted(scored, key=lambda x: -x[0])[:k]]
