"""M2 — "body-twin" review retrieval (RAG-retrieval, no vector DB; v3 §2.3-A).

Embeds each item's reviews with local MiniLM and ranks them by cosine similarity to the shopper's
fit concern, so the synthesizer (M3) sees reviews from shoppers with a *similar body / fit worry*.
Embeddings are cached to disk (keyed by a content hash) so runtime is instant and offline.

Graceful degradation (v3 reliability): if sentence-transformers / the model is unavailable, falls
back to a pure-stdlib keyword-overlap scorer — retrieval never hard-fails.

CLI:  python retriever.py            # build cache + sanity query
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from functools import lru_cache

import numpy as np

import config

_HERE = os.path.dirname(__file__)
_CACHE_DIR = os.path.join(_HERE, "embeddings_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)


# ---------- embedding backend (MiniLM, with keyword fallback) ----------
@lru_cache(maxsize=1)
def _model():
    """Load MiniLM once. Returns None if unavailable -> caller uses keyword fallback."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(config.EMBED_MODEL)
    except Exception:
        return None


def _hash(texts: list[str]) -> str:
    h = hashlib.sha1("||".join(texts).encode("utf-8")).hexdigest()[:16]
    return h


def _embed(texts: list[str]) -> np.ndarray | None:
    m = _model()
    if m is None:
        return None
    v = m.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(v, dtype=np.float32)


# ---------- per-item review embeddings (disk-cached) ----------
def _item_review_texts(item: dict) -> list[str]:
    return [r["text"] for r in item.get("reviews", [])]


def get_item_embeddings(item: dict) -> np.ndarray | None:
    """Return (n_reviews, dim) normalized embeddings for an item's reviews, cached to disk."""
    texts = _item_review_texts(item)
    if not texts:
        return None
    path = os.path.join(_CACHE_DIR, f'{item["id"]}-{_hash(texts)}.npy')
    if os.path.exists(path):
        return np.load(path)
    emb = _embed(texts)
    if emb is not None:
        np.save(path, emb)
    return emb


# ---------- keyword fallback ----------
_WORD = re.compile(r"[a-z']+")

def _keyword_scores(query: str, texts: list[str]) -> np.ndarray:
    q = set(_WORD.findall(query.lower()))
    if not q:
        return np.zeros(len(texts), dtype=np.float32)
    out = []
    for t in texts:
        toks = set(_WORD.findall(t.lower()))
        inter = len(q & toks)
        out.append(inter / (len(q) ** 0.5 * (len(toks) ** 0.5 + 1e-9)))
    return np.asarray(out, dtype=np.float32)


# ---------- query builder + public API ----------
def build_query(fit_prior: dict) -> str:
    """Turn the fit profile into a retrieval query, weighted toward the stated concern."""
    concern = (fit_prior.get("concern") or "").strip()
    parts = []
    if concern:
        parts.append(concern)
    parts.append(f'usual size {fit_prior.get("usual_size", "")}')
    parts.append(f'{fit_prior.get("last_fit", "")} fit'.strip())
    return ". ".join(p for p in parts if p).strip() or "fit and size"


def top_reviews(item: dict, fit_prior: dict, k: int | None = None) -> list[dict]:
    """Return the top-k most relevant reviews as [{text, rating, score, method}] (desc score)."""
    k = k or config.TOP_K_REVIEWS
    reviews = item.get("reviews", [])
    if not reviews:
        return []
    query = build_query(fit_prior)
    texts = [r["text"] for r in reviews]

    emb = get_item_embeddings(item)
    qv = _embed([query]) if emb is not None else None
    if emb is not None and qv is not None:
        scores = (emb @ qv[0]).astype(float)  # cosine (both normalized)
        method = "minilm"
    else:
        scores = _keyword_scores(query, texts)
        method = "keyword"

    order = np.argsort(-scores)[:k]
    return [{"text": reviews[i]["text"], "rating": reviews[i]["rating"],
             "score": round(float(scores[i]), 3), "method": method} for i in order]


def build_all(catalog: list[dict]) -> None:
    for item in catalog:
        get_item_embeddings(item)


if __name__ == "__main__":
    import product_source
    cat = product_source.load_catalog()
    print("Building embedding cache for", len(cat), "items…")
    build_all(cat)

    # sanity: body-twin retrieval on the runs-small kurta for a shoulder concern
    kurta = product_source.get_product("demo-kurta-anouk-01")
    prior = {"usual_size": "M", "last_fit": "Perfect", "concern": "broad shoulders, tight on chest"}
    print(f"\nQuery: {build_query(prior)!r}")
    for r in top_reviews(kurta, prior, k=4):
        print(f"  [{r['method']} {r['score']:.3f}] ({r['rating']}★) {r['text']}")

    # sanity: sparse-review item should still return (few) reviews, not crash
    tee = product_source.get_product("demo-tee-hrx-08")
    print(f"\nSparse item '{tee['id']}' returns {len(top_reviews(tee, prior))} review(s) (expect <=2)")
