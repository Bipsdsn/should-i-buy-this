# Should I Buy This? — Wishlist Confidence Agent (MVP)

Honest, calibrated fit / quality / look confidence for saved fashion items. **$0 stack**
(Groq free tier + local MiniLM retrieval + Streamlit). No monetary incentives; says "uncertain"
when the data can't support a call. See `../technical-implementation-plan-v3.md`.

## Run locally
```bash
pip install -r requirements.txt
export GROQ_API_KEY=...        # free at https://console.groq.com  (optional for M0)
python smoke_test.py           # M0 health check
streamlit run app.py
```

## Deploy (free)
Streamlit Community Cloud → point at `mvp/app.py` → add `GROQ_API_KEY` in Secrets.

## Status
- **M0–M4, M6 done; M5 deploy-ready (not yet pushed).**
- M0 scaffold · M1 demo catalog (8 items, edge cases) · M2 MiniLM body-twin retrieval (+keyword fallback) ·
  M3 Groq synthesizer + precomputed verdict cache · M3.5 bounded VLM seam (OFF — no free VLM) ·
  M4 full UI (confidence card, states, how-it-works) · M6 hardening (Groq retry, error guard) ·
  **M5 → see `DEPLOY.md`** (push to GitHub + Streamlit Cloud). Post-deploy hallway tests: pending.

## Files
`app.py` UI · `config.py` models/keys · `product_source.py` catalog+PDP · `reasoner.py` pipeline ·
`demo_catalog.json` demo items · `smoke_test.py` health check.
