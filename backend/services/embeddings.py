"""Text embeddings for semantic POI search (pgvector, 384 dims).

Backends (EMBEDDING_BACKEND):
- "hash"      — dependency-free hashing-trick bag-of-words. Deterministic and instant;
                token overlap -> cosine similarity. Default for dev/tests.
- "fastembed" — real sentence embeddings via ONNX (BAAI/bge-small-en-v1.5, 384 dims).
                Downloads the model on first use; set FASTEMBED_CACHE_PATH to persist it.

All functions are synchronous — call from Celery tasks directly, from async
endpoints via run_in_threadpool.
"""

import hashlib
import math
import re

from django.conf import settings

_fastembed_model = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    if settings.EMBEDDING_BACKEND == "fastembed":
        return _fastembed(texts)
    return [_hash_embed(t) for t in texts]


def poi_document(poi) -> str:
    """The text a POI is embedded from."""
    return " ".join(
        filter(
            None,
            [
                poi.title,
                poi.short_description,
                poi.description,
                " ".join(poi.categories),
                poi.city,
                poi.country,
            ],
        )
    )


def _hash_embed(text: str, dims: int = 384) -> list[float]:
    vec = [0.0] * dims
    for token in re.findall(r"\w+", text.lower()):
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        sign = 1.0 if (h >> 160) % 2 == 0 else -1.0
        vec[h % dims] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _fastembed(texts: list[str]) -> list[list[float]]:
    global _fastembed_model
    from fastembed import TextEmbedding

    if _fastembed_model is None:
        _fastembed_model = TextEmbedding(settings.EMBEDDING_MODEL)
    return [[float(x) for x in v] for v in _fastembed_model.embed(texts)]
