"""Should I Buy This? — Wishlist Confidence Agent (Myntra-styled UI over the real engine). $0 stack.

Design adapted from the supplied Myntra mockup; every value shown is produced by the REAL engine
(Groq synthesizer + MiniLM body-twin retrieval + cached verdicts + honest fallback). No fabricated
vision / clips / body-metrics. Run:  python run.py   (or)   streamlit run app.py
"""
from __future__ import annotations
import html

import streamlit as st

import config
import product_source
import reasoner

st.set_page_config(page_title="Should I Buy This? | Myntra", page_icon="🛍️", layout="wide")

# ------------------------------------------------------------------ design system (from mockup)
CSS = """
<style>
:root{
  --m-pink:#ff3f6c; --m-pink-light:#fff0f3; --m-charcoal:#282c3f; --m-grey:#535766;
  --status-green:#03a685; --status-green-bg:#e6f7f3; --status-amber:#d97706; --status-amber-bg:#fffbeb;
  --status-muted:#64748b; --status-muted-bg:#f1f5f9;
  --radius-lg:20px; --radius-sm:12px; --shadow-soft:0 10px 30px rgba(40,44,63,.06);
}
.block-container{padding-top:1.2rem; max-width:1300px;}
/* NOTE: Streamlit's ⋮ menu + footer left visible on purpose — keeps built-in
   "Record screen" (screen + mic/voice) available for demo recording. */
.sib-header{display:flex; align-items:center; gap:12px; padding:14px 20px; background:#1F4E79; border-radius:12px; margin-bottom:18px;}
.sib-logo{width:34px;height:34px;background:var(--m-pink);border-radius:8px;color:#fff;font-weight:900;
  display:flex;align-items:center;justify-content:center;font-size:18px;}
.sib-logo-txt{font-weight:800;font-size:20px;color:#ffffff;}
.sib-sub{margin-left:auto;font-size:14px;font-weight:600;color:#dbe6f2;}
/* verdict hero */
.verdict-header{background:#fff;border-radius:var(--radius-lg);padding:34px;box-shadow:var(--shadow-soft);text-align:center;margin-bottom:24px;}
.verdict-badge{display:inline-block;padding:6px 16px;border-radius:50px;font-size:12px;font-weight:800;
  text-transform:uppercase;letter-spacing:1px;margin-bottom:16px;}
.badge-ready{background:var(--status-green-bg);color:var(--status-green);}
.badge-check{background:var(--status-amber-bg);color:var(--status-amber);}
.badge-muted{background:var(--status-muted-bg);color:var(--status-muted);}
.verdict-title{font-size:30px;font-weight:800;letter-spacing:-.5px;line-height:1.2;color:var(--m-charcoal);margin-bottom:10px;}
.verdict-sub{font-size:15px;color:var(--m-grey);}
/* pillars */
.pillars{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:24px;}
@media(max-width:1100px){.pillars{grid-template-columns:1fr;}}
.pillar{background:#fff;border-radius:var(--radius-lg);padding:24px;box-shadow:var(--shadow-soft);position:relative;}
.conf-tag{position:absolute;top:20px;right:20px;font-size:10px;font-weight:800;padding:4px 10px;border-radius:6px;text-transform:uppercase;}
.conf-high{background:var(--status-green-bg);color:var(--status-green);}
.conf-med{background:var(--status-amber-bg);color:var(--status-amber);}
.conf-low{background:var(--status-muted-bg);color:var(--status-muted);}
.pillar-icon{font-size:24px;margin-bottom:12px;}
.pillar-title{font-size:16px;font-weight:800;margin-bottom:8px;padding-right:74px;color:var(--m-charcoal);}
.pillar-desc{font-size:14px;color:var(--m-grey);line-height:1.5;}
/* split cards */
.split{display:grid;grid-template-columns:1fr 1fr;gap:20px;}
@media(max-width:1100px){.split{grid-template-columns:1fr;}}
.card{background:#fff;border-radius:var(--radius-lg);padding:26px;box-shadow:var(--shadow-soft);}
.card h3{font-size:16px;font-weight:800;margin-bottom:16px;color:var(--m-charcoal);}
.twin{border-left:3px solid var(--m-pink);padding-left:14px;margin-bottom:14px;}
.twin p{font-size:14px;font-style:italic;color:var(--m-charcoal);margin-bottom:6px;}
.twin span{font-size:12px;font-weight:600;color:var(--m-grey);}
.resolver{display:flex;gap:12px;align-items:flex-start;margin-bottom:14px;}
.rdot{width:22px;height:22px;background:var(--m-pink-light);color:var(--m-pink);border-radius:50%;
  display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;flex-shrink:0;margin-top:1px;}
.rtext{font-size:14px;color:var(--m-grey);line-height:1.5;}
.prov{font-size:12px;color:#94969f;margin-top:18px;}
.roadmap{font-size:12px;color:#94969f;margin-top:10px;}
/* left panel pills via radio */
div[role=radiogroup] label{border:1px solid #eaeaec;border-radius:8px;padding:6px 12px;margin:0 6px 6px 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

CATEGORY_ICON = {"kurta": "🥻", "jeans": "👖", "shirt": "👔", "ethnic": "🥻", "dress": "👗",
                 "footwear": "👟", "activewear": "🎽"}
def icon_for(cat: str) -> str:
    for k, v in CATEGORY_ICON.items():
        if k in cat.lower():
            return v
    return "🛍️"

FIT_TITLE = {"likely_fits": "True to size", "size_up": "Size up a size",
             "size_down": "Size down a size", "uncertain": "Fit uncertain"}
QUAL_TITLE = {"reassuring": "Reassuring quality", "mixed": "Mixed feedback",
              "concerning": "Quality concerns", "insufficient_reviews": "Too few reviews"}
LOOK_TITLE = {"yes": "Suits the occasion", "maybe": "Might suit", "no": "May not suit", "unclear": "Look unclear"}
CONF_CLASS = {"high": "conf-high", "med": "conf-med", "medium": "conf-med", "low": "conf-low"}
CONF_LABEL = {"high": "High Conf", "medium": "Med Conf", "med": "Med Conf", "low": "Low Conf"}
BADGE = {"ready": ("Ready to Buy", "badge-ready"), "check_first": ("Check First", "badge-check"),
         "not_yet": ("Not Yet", "badge-muted")}


def _conf(c): return CONF_CLASS.get(c, "conf-low"), CONF_LABEL.get(c, "Low Conf")
def esc(x): return html.escape(str(x or ""))


def verdict_html(product: dict, fit_prior: dict, v: dict) -> str:
    o = v["overall"]
    b_label, b_class = BADGE.get(o.get("buy_readiness", ""), ("Check First", "badge-check"))
    n_rev = len(product.get("reviews", []))
    k = len(v.get("_reviews_used", []))
    sub = (f"Analyzed against your size {esc(fit_prior.get('usual_size'))} prior · "
           f"{n_rev} reviews · {k} body-twin matches")

    fc, fl = _conf(v["fit"].get("confidence"))
    qc, ql = _conf(o.get("confidence"))
    lc, ll = _conf(o.get("confidence"))
    fit_t = FIT_TITLE.get(v["fit"].get("call"), "Fit")
    qual_t = QUAL_TITLE.get(v["quality"].get("read"), "Quality")
    look_t = LOOK_TITLE.get(v["look"].get("suits_occasion"), "Look")

    pillars = f"""
    <div class="pillars">
      <div class="pillar"><span class="conf-tag {fc}">{fl}</span><div class="pillar-icon">📏</div>
        <div class="pillar-title">{esc(fit_t)}</div><div class="pillar-desc">{esc(v['fit'].get('why'))}</div></div>
      <div class="pillar"><span class="conf-tag {qc}">{ql}</span><div class="pillar-icon">✨</div>
        <div class="pillar-title">{esc(qual_t)}</div><div class="pillar-desc">{esc(v['quality'].get('why'))}</div></div>
      <div class="pillar"><span class="conf-tag {lc}">{ll}</span><div class="pillar-icon">👗</div>
        <div class="pillar-title">{esc(look_t)}</div><div class="pillar-desc">{esc(v['look'].get('styling_tip') or '—')}</div></div>
    </div>"""

    twins = "".join(
        f'<div class="twin"><p>"{esc(r["text"])}"</p>'
        f'<span>★{r["rating"]} · relevance {r.get("score","")} · {esc(r.get("method",""))}</span></div>'
        for r in v.get("_reviews_used", [])[:2]) or '<p class="rtext">No matching reviews.</p>'

    resolvers = "".join(
        f'<div class="resolver"><div class="rdot">{i+1}</div><div class="rtext">{esc(s)}</div></div>'
        for i, s in enumerate(v.get("what_would_settle_it", []))) or '<p class="rtext">—</p>'

    prov = {"groq": "AI reasoning (free-tier LLM, cached)",
            "fallback": "review-derived fallback (LLM unavailable — still honest)"}.get(v.get("_engine"), v.get("_engine", ""))

    return f"""
    <div class="verdict-header">
      <div class="verdict-badge {b_class}">{esc(b_label)}</div>
      <div class="verdict-title">{esc(o.get('one_line'))}</div>
      <div class="verdict-sub">{sub}</div>
    </div>
    {pillars}
    <div class="split">
      <div class="card"><h3>Shoppers like you (body-twin reviews)</h3>{twins}
        <div class="roadmap">Creator/try-on clips (GlamStream) are a production roadmap item — not shown in this build.</div></div>
      <div class="card"><h3>What would settle it</h3>{resolvers}
        <div class="prov">How this was produced: {esc(prov)}. No price/discount logic anywhere in this tool.</div></div>
    </div>"""


# ------------------------------------------------------------------ header
st.markdown('<div class="sib-header"><div class="sib-logo">M</div>'
            '<span class="sib-logo-txt">Myntra</span>'
            '<span class="sib-sub">Wishlist Confidence Agent · honest, no-incentive</span></div>',
            unsafe_allow_html=True)

tab_check, tab_how = st.tabs(["Should I buy this?", "How it works"])

with tab_check:
    left, right = st.columns([1, 1.9], gap="large")

    with left:
        st.markdown("#### 1 · Select a saved item")
        catalog = product_source.load_catalog()
        opts = {f'{icon_for(p["category"])}  {p["brand"]} — {p["title"]}': p["id"] for p in catalog}
        pick = st.radio("Your wishlist", list(opts.keys()), label_visibility="collapsed")
        product = product_source.get_product(opts[pick])

        with st.expander("…or paste a Myntra link (experimental)"):
            url = st.text_input("Myntra URL", "", placeholder="https://www.myntra.com/…",
                                label_visibility="collapsed")
            if url.strip():
                st.info("Live fetch is bot-blocked; showing the selected demo item — reasoning is identical.")

        st.markdown("#### 2 · Your fit prior")
        usual_size = st.radio("Typical size", ["XS", "S", "M", "L", "XL", "XXL"], index=2, horizontal=True)
        last_fit = st.radio("How your last order fit", ["Tight", "Perfect", "Loose"], index=1, horizontal=True)
        concern = st.text_input("Any fit concern? (optional)", "",
                                placeholder="e.g. broad shoulders, runs small, petite")
        go = st.button("Should I buy this?", type="primary", use_container_width=True)
        st.caption("🔒 Used only for this check — never stored. In production this comes from your size history.")

    with right:
        fit_prior = {"usual_size": usual_size, "last_fit": last_fit, "concern": concern}
        key = reasoner._cache_key(product, fit_prior)
        cached = reasoner._load_cached(key)
        v = None
        if go:
            with st.spinner("Checking honestly — size chart + shoppers like you…"):
                try:
                    v = reasoner.assess(product, fit_prior)
                except Exception:
                    v = reasoner._fallback(product, reasoner.retriever.top_reviews(product, fit_prior))
                    st.warning("The AI service hiccuped — this is an honest read straight from the reviews.")
        elif cached and "_reviews_used" in cached:
            v = cached  # instant, no model load (default prior + previously-computed combos)

        if v:
            st.markdown(verdict_html(product, fit_prior, v), unsafe_allow_html=True)
        else:
            st.info("Set your size and tap **Should I buy this?** — this exact combination isn't "
                    "pre-computed, so it needs one live check.")

with tab_how:
    st.markdown(
        """
### How it works — honest confidence, no incentives
**Problem.** The wishlist captures intent in one tap, then abandons it: when a shopper is unsure about
**fit, quality, or how it'll look on them**, the app offers no way to resolve it, so they leave for
YouTube/other apps and the item stalls (KPI-tree node C).

**What this does.** For a saved item it returns an **honest, calibrated** read on fit / quality / look,
grounded in evidence, and names the one thing that would settle the doubt — bringing off-app research
back in-app.

**How (all free / $0):**
1. **Body-twin reviews** — a local MiniLM model finds reviews from shoppers with a *similar fit
   concern* (not just top reviews).
2. **Size-chart reasoning** — your usual size + last-fit vs the item's chart.
3. **Honest synthesizer** — a free Groq LLM fuses these into a calibrated verdict. It is the **opposite
   of a support bot**: it says *"I can't tell you this yet — here's what would"* when data is thin, and
   **never uses price, discounts, or urgency**.

**Why honesty matters.** Indian fashion returns run 30–35%. Pushing an unsure shopper to buy inflates
returns; genuinely resolving uncertainty *reduces* them — so "uncertain" is a feature, not a bug.

**Privacy.** Fit inputs are used only for the check and never stored.
""")
    st.caption(f"Reasoning: {config.GROQ_SYNTH_MODEL} (free) · embeddings: {config.EMBED_MODEL} (local) · "
               f"reviews are realistic demo data (Myntra PDPs are bot-blocked); vision is off (no free VLM).")
