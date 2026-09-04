"""M3.5 — OPTIONAL bounded visual check. $0 stack; OFF by default.

Status (Sep 2026): no free vision model is available on the current Groq key (its list is text-only),
and demo items ship without images — so this stays disabled and the pipeline runs text-only, exactly
as v3 §2.3-B allows ("if no reliable free VLM, skip; frame as roadmap").

This module is a REAL, bounded seam: if a free vision-capable model is later configured
(`config.GROQ_VISION_MODEL`) and an item has an image, it returns a CONSERVATIVE visual note that
feeds the synthesizer as a *signal only* — never a decisive quality claim (guardrail: a confidently
wrong "it's sheer" would inflate returns). It must say "unclear" when unsure.
"""
from __future__ import annotations

import config


def available() -> bool:
    """True only if vision is enabled AND a vision model is configured."""
    return bool(config.ENABLE_VISION and getattr(config, "GROQ_VISION_MODEL", ""))


_SYSTEM = (
    "You are a cautious visual inspector for a clothing product image. Note ONLY clearly-visible, "
    "high-confidence facts (obvious dominant colour, general silhouette/length). Do NOT guess fabric "
    "sheerness, exact shade, or fit — if not clearly visible, say 'unclear'. Never be decisive from a "
    "single compressed image. Output JSON: {\"visible\":\"one short factual line\",\"confidence\":\"low|medium\"}."
)


def assess_image(image_url: str, product: dict) -> dict | None:
    """Return a bounded visual note {'visible','confidence'} or None. Safe no-op if unavailable."""
    if not available() or not image_url:
        return None
    key = config.get_groq_key()
    if not key:
        return None
    try:
        import json
        from groq import Groq
        client = Groq(api_key=key)
        resp = client.chat.completions.create(
            model=config.GROQ_VISION_MODEL,
            messages=[{"role": "system", "content": _SYSTEM},
                      {"role": "user", "content": [
                          {"type": "text", "text": f"Product: {product.get('title','')}. "
                                                   f"Describe only what is clearly visible."},
                          {"type": "image_url", "image_url": {"url": image_url}}]}],
            temperature=0.1, timeout=config.INFERENCE_TIMEOUT_S,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return None   # never let vision break the text pipeline
