"""Central config for the Should-I-Buy-This MVP. $0 stack only (v3 plan)."""
from __future__ import annotations
import os

# --- Models (all free tier; verified available on Groq as of Sep 2026) ---
GROQ_SYNTH_MODEL = "openai/gpt-oss-120b"       # heavy reasoning / synthesis
GROQ_FAST_MODEL = "openai/gpt-oss-20b"         # light routing / cheap calls
EMBED_MODEL = "all-MiniLM-L6-v2"               # local, ~80MB, used from M2

# --- Behaviour knobs ---
INFERENCE_TIMEOUT_S = 10        # global cap; on breach -> graceful fallback (v3 §2.5)
TOP_K_REVIEWS = 6               # "body-twin" reviews passed to the synthesizer
ENABLE_VISION = False           # optional bounded VLM (M3.5); off until a free VLM is verified
GROQ_VISION_MODEL = ""          # set to a free vision-capable model id to activate vision.py

# Default fit profile used to precompute the instant demo verdict cache (matches app defaults).
DEFAULT_FIT_PRIOR = {"usual_size": "M", "last_fit": "Perfect", "concern": ""}


def get_groq_key() -> str | None:
    """Key from env or Streamlit secrets; None if unset (smoke/app degrade gracefully)."""
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    try:  # only import streamlit lazily so non-UI scripts don't need it
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY")  # type: ignore[attr-defined]
    except Exception:
        return None


def has_groq() -> bool:
    return bool(get_groq_key())
