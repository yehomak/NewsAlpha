from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

log = structlog.get_logger()

_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    from sentence_transformers import SentenceTransformer as ST

    log.info("embedder.loading_model", model=_MODEL_NAME)
    return ST(_MODEL_NAME)


def _encode(text: str) -> list[float]:
    import numpy as np

    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    arr: np.ndarray[tuple[int], np.dtype[np.float32]] = np.asarray(vec)
    return arr.tolist()


async def embed_text(text: str) -> list[float]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _encode, text)
