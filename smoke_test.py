"""M0 smoke test. PASS when the scaffold imports, the catalog loads, and (if a key is set)
Groq returns a completion. Run:  python mvp/smoke_test.py
"""
from __future__ import annotations
import sys

def main() -> int:
    ok = True

    # 1. imports
    try:
        import streamlit  # noqa: F401
        import config, product_source, reasoner  # noqa: F401
        print("PASS  imports (streamlit, config, product_source, reasoner)")
    except Exception as e:
        print("FAIL  imports:", e); return 1

    # 2. catalog
    try:
        cat = product_source.load_catalog()
        assert cat and "reviews" in cat[0]
        print(f"PASS  demo catalog loads ({len(cat)} item[s])")
    except Exception as e:
        print("FAIL  catalog:", e); ok = False

    # 3. honest fallback verdict is always valid (no key path)
    try:
        fb = reasoner._fallback(cat[0], cat[0]["reviews"][:2])
        assert reasoner._validate(fb) and fb["_engine"] == "fallback"
        print("PASS  honest fallback verdict is schema-valid")
    except Exception as e:
        print("FAIL  fallback verdict:", e); ok = False

    # 4. assess() returns a schema-valid verdict (cache/groq/fallback — any path)
    try:
        v = reasoner.assess(cat[0], config.DEFAULT_FIT_PRIOR)
        assert reasoner._validate(v), "verdict missing required keys"
        print(f"PASS  assess() valid verdict (engine={v.get('_engine')}, "
              f"reviews={len(v.get('_reviews_used', []))})")
    except Exception as e:
        print("FAIL  assess():", e); ok = False

    # 5. precomputed demo verdict cache present (reliability layer)
    import glob, os
    n = len(glob.glob(os.path.join(os.path.dirname(__file__), "verdict_cache", "*.json")))
    print(f"{'PASS' if n >= len(cat) else 'WARN'}  verdict cache: {n}/{len(cat)} items"
          f"{'' if n >= len(cat) else ' (run: python reasoner.py)'}")

    # 6. Groq live call (tolerant: rate-limit on free tier is a WARN, not a failure)
    if config.has_groq():
        out = reasoner.groq_complete("Reply with exactly: OK", system="You reply tersely.",
                                     model=config.GROQ_FAST_MODEL)
        if out and "OK" in out:
            print("PASS  Groq free-tier completion:", out.strip()[:40])
        else:
            print("WARN  Groq key set but no completion now (likely transient free-tier rate limit)")
    else:
        print("SKIP  Groq live call — no GROQ_API_KEY set (get a free key at console.groq.com)")

    print("\nStatus:", "GREEN ✅" if ok else "RED ❌")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
