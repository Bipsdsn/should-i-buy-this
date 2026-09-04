# Deploy — Streamlit Community Cloud (free, $0)

The app is **deploy-ready**. This is the exact path to a public URL (Deliverable #3).

## 1. Push `mvp/` to a public GitHub repo
```bash
cd mvp
git init && git add . && git commit -m "Should I Buy This? — wishlist confidence agent (MVP)"
git branch -M main
git remote add origin https://github.com/<you>/should-i-buy-this.git
git push -u origin main
```
`.streamlit/secrets.toml` (your Groq key) is git-ignored and will NOT be pushed. ✅
`verdict_cache/` IS committed on purpose → the demo is instant on first load. ✅

## 2. Create the app
1. Go to https://share.streamlit.io → **New app** → pick the repo.
2. **Main file path:** `app.py`  (repo root = `mvp/`; if you push the whole project instead, use `mvp/app.py`).
3. **Advanced → Secrets**, paste:
   ```toml
   GROQ_API_KEY = "your_free_key_from_console.groq.com"
   ```
4. Deploy. First build installs `requirements.txt` (incl. torch via sentence-transformers) — a few minutes.

## 3. Acceptance (do before submitting the link)
- Open the public URL in a **fresh incognito window** (desktop + mobile) — no sign-in wall.
- Run a demo check on the default item (should be **instant** — served from `verdict_cache/`).
- Run one with a custom fit concern (first custom call loads MiniLM once, then fast).
- Confirm the sparse-review item (HRX tee) returns an honest **"too few reviews / uncertain"**.

## Notes
- **$0:** Groq free tier + local MiniLM + Streamlit Community Cloud. No paid services.
- **Key hygiene:** the key you shared during the build lives only in local `secrets.toml`; rotate it at
  console.groq.com after submission and use a fresh one in Streamlit Cloud secrets.
- **Vision (M3.5)** is off (no free VLM on the current key); set `config.GROQ_VISION_MODEL` to enable later.
- If Groq is rate-limited at load, the app degrades to the honest review-derived verdict — never errors.
