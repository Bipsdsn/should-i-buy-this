"""M3 — the honest confidence synthesizer + verdict cache. $0 stack.

Pipeline (v3 §2.3): retrieve body-twin reviews (M2) -> build prompt (size chart + fit prior +
retrieved reviews) -> Groq Llama synthesizes a calibrated JSON Verdict -> parse -> cache.

Reliability (v3 §2.5): every demo verdict is precomputed & cached to disk so the live demo is
instant; on no-key / timeout / bad-JSON we degrade to a review-derived honest fallback. The AI is
the *opposite* of a deflecting bot — it either helps or plainly states the limit. No price levers.

CLI:  python reasoner.py            # precompute demo verdict cache + print samples
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from typing import TypedDict

import config
import retriever
import vision

_HERE = os.path.dirname(__file__)
_VCACHE_DIR = os.path.join(_HERE, "verdict_cache")
os.makedirs(_VCACHE_DIR, exist_ok=True)


class Verdict(TypedDict, total=False):
    fit: dict
    quality: dict
    look: dict
    what_would_settle_it: list[str]
    overall: dict
    _engine: str          # "groq" | "fallback"
    _reviews_used: list


SYSTEM = (
    "You are an honest fit-and-confidence assistant for Indian online fashion shoppers. "
    "Using the size chart vs the shopper's usual size and how their last buy fit, the fit/quality "
    "signals in the supplied reviews, and the product details, assess THREE things: fit, quality, "
    "and look/occasion. Give a CALIBRATED confidence (high/medium/low). When the data cannot support "
    "a call, say so plainly and name what would settle it — never guess, never invent facts not in "
    "the inputs. NEVER use price, discounts, or urgency to persuade. You are the opposite of a support "
    "bot that deflects: you either genuinely help or state the limit honestly.\n"
    "CALIBRATION RULES (follow strictly):\n"
    "1. Confidence must reflect how much consistent evidence you have. Few or conflicting reviews -> "
    "low/medium; many reviews agreeing -> high. Never 'high' from thin evidence.\n"
    "2. If FEWER THAN 4 reviews are available, quality.read MUST be 'insufficient_reviews', "
    "overall.confidence MUST be 'low', and buy_readiness MUST be 'check_first' or 'not_yet'. "
    "Do NOT call quality 'reassuring' or fit confidence 'high' from 3 or fewer reviews.\n"
    "3. If multiple reviews say the item runs small / to size up (or runs large / size down), set "
    "fit.call to 'size_up' (or 'size_down') accordingly, unless the shopper already accounts for it.\n"
    "4. If reviews conflict on fit, use 'uncertain' and say what would settle it.\n"
    "Respond with ONLY a single JSON object, no prose, matching exactly this shape:\n"
    '{"fit":{"call":"likely_fits|size_up|size_down|uncertain","confidence":"high|medium|low","why":"..."},'
    '"quality":{"read":"reassuring|mixed|concerning|insufficient_reviews","why":"..."},'
    '"look":{"suits_occasion":"yes|maybe|no|unclear","styling_tip":"...","evidence_clip":null},'
    '"what_would_settle_it":["at most 2 concrete resolvers"],'
    '"overall":{"confidence":"high|medium|low","one_line":"honest summary",'
    '"buy_readiness":"ready|check_first|not_yet"}}'
)


def groq_complete(prompt: str, system: str = "", model: str | None = None) -> str | None:
    """Single Groq chat call. Returns text, or None on any failure (caller falls back)."""
    key = config.get_groq_key()
    if not key:
        return None
    import time
    for attempt in range(2):   # one light retry to ride transient free-tier rate limits (M6)
        try:
            from groq import Groq
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model=model or config.GROQ_SYNTH_MODEL,
                messages=[
                    {"role": "system", "content": system or "You are a helpful, honest assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                timeout=config.INFERENCE_TIMEOUT_S,
                response_format={"type": "json_object"},
            )
            return resp.choices[0].message.content
        except Exception:
            if attempt == 0:
                time.sleep(1.5)
                continue
            return None


def _build_prompt(product: dict, fit_prior: dict, reviews: list[dict],
                  visual_note: dict | None = None) -> str:
    rv = "\n".join(f"- ({r['rating']}★) {r['text']}" for r in reviews) or "- (no reviews available)"
    n_total = len(product.get("reviews", []))
    vis = (f"VISUAL NOTE (bounded, treat as a weak signal): {visual_note}\n" if visual_note else "")
    return (
        f"PRODUCT: {product.get('brand','')} — {product.get('title','')} "
        f"[{product.get('category','')}]\n"
        f"DETAILS: {product.get('details','')}\n"
        f"SIZE CHART: {json.dumps(product.get('size_chart', {}))}\n"
        f"SHOPPER: usually wears size {fit_prior.get('usual_size','?')}; "
        f"their last purchase fit '{fit_prior.get('last_fit','?')}'; "
        f"stated concern: {fit_prior.get('concern') or 'none'}.\n"
        f"TOTAL REVIEWS AVAILABLE FOR THIS ITEM: {n_total} "
        f"(the {len(reviews)} below are the most relevant to this shopper).\n"
        f"MOST RELEVANT REVIEWS (from shoppers with similar fit concerns):\n{rv}\n"
        f"{vis}\n"
        f"Assess fit, quality, look for THIS shopper. Remember: honest, calibrated, no price talk, "
        f"JSON only."
    )


def _parse(raw: str | None) -> Verdict | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)   # tolerate stray prose around the JSON
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def _validate(v: Verdict | None) -> bool:
    if not isinstance(v, dict):
        return False
    return all(k in v for k in ("fit", "quality", "look", "what_would_settle_it", "overall"))


def _fallback(product: dict, reviews: list[dict]) -> Verdict:
    """Honest, review-derived verdict when Groq is unavailable. Conservative by design."""
    texts = " ".join(r["text"].lower() for r in reviews)
    n = len(product.get("reviews", []))
    runs_small = len(re.findall(r"runs small|size up|tight|snug|small", texts))
    thin = len(re.findall(r"thin|sheer|see-through|cheap|flimsy", texts))
    colour = len(re.findall(r"colour|color|lighter|duller|washed", texts))

    if n < 3:
        fit = {"call": "uncertain", "confidence": "low",
               "why": f"Only {n} review(s) — not enough to judge fit for you."}
        quality = {"read": "insufficient_reviews", "why": "Too few reviews to assess quality."}
    else:
        if runs_small >= 2:
            fit = {"call": "size_up", "confidence": "medium",
                   "why": "Multiple similar shoppers report it runs small / tight."}
        else:
            fit = {"call": "uncertain", "confidence": "low",
                   "why": "Reviews are mixed on fit; depends on your body."}
        quality = ({"read": "concerning", "why": "Several reviews flag thin/sheer/flimsy fabric."}
                   if thin >= 2 else {"read": "mixed", "why": "Reviews are mixed on quality."})
    look = {"suits_occasion": "unclear",
            "styling_tip": "Colour may differ from the photo." if colour >= 2 else "",
            "evidence_clip": None}
    settle = []
    if fit["call"] in ("uncertain", "size_up"):
        settle.append("Compare the size chart against a garment you own that fits well.")
    if quality["read"] in ("concerning", "mixed", "insufficient_reviews"):
        settle.append("Check photo reviews for fabric/colour before deciding.")
    ready = "not_yet" if fit["confidence"] == "low" else "check_first"
    return {"fit": fit, "quality": quality, "look": look,
            "what_would_settle_it": settle or ["Have a quick look at recent photo reviews."],
            "overall": {"confidence": "low" if n < 3 else "medium",
                        "one_line": "Honest read from reviews; some uncertainty remains.",
                        "buy_readiness": ready},
            "_engine": "fallback"}


def _cache_key(product: dict, fit_prior: dict) -> str:
    raw = f'{product["id"]}|{fit_prior.get("usual_size")}|{fit_prior.get("last_fit")}|{(fit_prior.get("concern") or "").strip().lower()}'
    return hashlib.sha1(raw.encode()).hexdigest()[:20]


def _cache_path(key: str) -> str:
    return os.path.join(_VCACHE_DIR, f"{key}.json")


def _load_cached(key: str) -> Verdict | None:
    p = _cache_path(key)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return None
    return None


def _save_cached(key: str, v: Verdict) -> None:
    try:
        json.dump(v, open(_cache_path(key), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception:
        pass


def assess(product: dict, fit_prior: dict, reviews: list | None = None,
           use_cache: bool = True) -> Verdict:
    """Full pipeline: (cache?) -> retrieve -> Groq -> parse -> fallback. Always returns a Verdict.

    Cache hits are a pure JSON read (retrieved reviews are stored in the verdict), so the default
    demo path never even loads the embedding model — instant and torch-free (v3 reliability).
    """
    key = _cache_key(product, fit_prior)
    if use_cache:
        cached = _load_cached(key)
        if cached and "_reviews_used" in cached:
            return cached

    top = retriever.top_reviews(product, fit_prior)
    visual_note = None
    if vision.available() and product.get("image_url"):
        visual_note = vision.assess_image(product["image_url"], product)
    raw = groq_complete(_build_prompt(product, fit_prior, top, visual_note), system=SYSTEM)
    v = _parse(raw)
    if _validate(v):
        v["_engine"] = "groq"          # type: ignore[index]
    else:
        v = _fallback(product, top)    # honest degrade
    v["_reviews_used"] = top           # type: ignore[index]
    if v["_engine"] == "groq":
        _save_cached(key, v)           # cache only successful Groq verdicts (with reviews)
    return v


def precompute_demo_verdicts(fit_prior: dict | None = None) -> dict:
    """Precompute + cache verdicts for every demo item (v3 reliability layer). Returns a summary."""
    import product_source
    prior = fit_prior or config.DEFAULT_FIT_PRIOR
    summary = {}
    for item in product_source.load_catalog():
        v = assess(item, prior, use_cache=False)   # force fresh, then it's saved if groq
        summary[item["id"]] = {"engine": v.get("_engine"),
                               "fit": v["fit"]["call"], "conf": v["overall"]["confidence"],
                               "quality": v["quality"]["read"]}
    return summary


if __name__ == "__main__":
    print("Groq key present:", config.has_groq())
    print("Precomputing demo verdicts (default profile)…\n")
    s = precompute_demo_verdicts()
    for pid, r in s.items():
        print(f"  {pid:32} engine={r['engine']:8} fit={r['fit']:11} "
              f"quality={r['quality']:20} conf={r['conf']}")
    # honesty spot-check: sparse item must be uncertain/insufficient
    tee = s.get("demo-tee-hrx-08", {})
    print(f"\nHonesty check (sparse tee): fit={tee.get('fit')} quality={tee.get('quality')} "
          f"-> {'OK' if tee.get('quality')=='insufficient_reviews' or tee.get('fit')=='uncertain' else 'REVIEW'}")
