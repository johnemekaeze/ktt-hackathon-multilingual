"""
app.py — Streamlit demo for T2.2 Multilingual Grant & Tender Matcher.

Run:  streamlit run app.py
"""

import json
import os
import sys

import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multilingual Grant & Tender Matcher",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimal CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.score-bar-outer {
    background: #3a3a3a; border-radius: 6px; height: 10px; width: 100%;
}
.score-bar-inner {
    background: linear-gradient(90deg, #2ecc71, #27ae60);
    height: 10px; border-radius: 6px;
}
.tender-card {
    background: #1e2a1e; border-left: 4px solid #2ecc71;
    padding: 14px 18px; border-radius: 8px; margin-bottom: 14px;
    color: #e8f5e9;
}
.tender-card-fr {
    background: #2a1e0e; border-left: 4px solid #e67e22;
    padding: 14px 18px; border-radius: 8px; margin-bottom: 14px;
    color: #fff3e0;
}
.tender-card b, .tender-card-fr b {
    color: #ffffff;
}
.tender-card small, .tender-card-fr small {
    color: #cccccc;
}
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 0.75em; font-weight: bold; color: white;
    margin-right: 4px;
}
.badge-en  { background: #27ae60; }
.badge-fr  { background: #d35400; }
.badge-sec { background: #2980b9; }
.metric-box {
    text-align: center; padding: 16px;
    background: #1a1f2e; border: 1px solid #2c3e6e;
    border-radius: 8px; margin-bottom: 8px; color: #cdd8ff;
}
</style>
""", unsafe_allow_html=True)


# ── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_resource(show_spinner="🔍 Building search index…")
def load_engine():
    """Load tenders, build index once per session."""
    # Ensure data exists
    if not os.path.exists("tenders") or not os.listdir("tenders"):
        st.warning("Generating data…")
        exec(open("generate_data.py").read(), {})

    from parser import parse_all
    from ranker import build_index

    tenders = parse_all("tenders")
    build_index(tenders)
    return tenders


@st.cache_data
def load_profiles():
    with open("profiles.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_gold():
    import csv
    from collections import defaultdict
    gold = defaultdict(list)
    if os.path.exists("gold_matches.csv"):
        with open("gold_matches.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                gold[row["profile_id"]].append(row["tender_id"])
    return dict(gold)


# ── Helpers ───────────────────────────────────────────────────────────────────
def score_bar_html(score: float) -> str:
    pct = int(score * 100)
    color = "#2ecc71" if score >= 0.6 else "#e67e22" if score >= 0.4 else "#e74c3c"
    return (
        f'<div class="score-bar-outer">'
        f'<div style="background:{color};height:10px;border-radius:6px;width:{pct}%"></div>'
        f'</div>'
    )


def lang_badge(lang: str) -> str:
    cls = "badge-en" if lang == "en" else "badge-fr"
    return f'<span class="badge {cls}">{lang.upper()}</span>'


def sector_badge(sector: str) -> str:
    return f'<span class="badge badge-sec">{sector}</span>'


SECTOR_ICONS = {
    "agritech":   "🌾",
    "healthtech": "🏥",
    "cleantech":  "⚡",
    "edtech":     "📚",
    "fintech":    "💳",
    "wastetech":  "♻️",
}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Africa_globe.svg/240px-Africa_globe.svg.png", width=80)
    st.title("🌍 Grant Matcher")
    st.caption("T2.2 · AIMS KTT Hackathon · April 2026")
    st.divider()

    mode = st.radio("Mode", ["🔍 Match by Profile", "✏️ Custom Query"], index=0)
    st.divider()

    topk = st.slider("Top-K results", min_value=1, max_value=10, value=5)
    show_breakdown = st.toggle("Show score breakdown", value=True)
    show_summary = st.toggle("Show match summary", value=True)
    show_why_not = st.toggle("Show 'Why NOT' disqualifiers", value=True)
    st.divider()

    st.markdown("**About**")
    st.caption(
        "Ranks tenders for business profiles using TF-IDF + "
        "multilingual embeddings (MiniLM-L12-v2). "
        "Scoring: 40% semantic · 25% sector · 20% budget · 10% deadline · 5% language."
    )

# ── Load data ─────────────────────────────────────────────────────────────────
tenders  = load_engine()
profiles = load_profiles()
gold     = load_gold()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🌍 Multilingual Grant & Tender Matcher")
st.markdown(
    "Matches African business profiles to the most relevant EU/AU/regional grants and tenders. "
    "Summaries generated in the profile's preferred language (EN/FR)."
)
st.divider()

# ── Mode: Match by Profile ────────────────────────────────────────────────────
if "Match by Profile" in mode:
    profile_options = {
        f"Profile {p['id']} — {SECTOR_ICONS.get(p['sector'], '🏢')} {p['sector'].capitalize()} · {p['country']}": p
        for p in profiles
    }
    selected_label = st.selectbox("Select a business profile", list(profile_options.keys()))
    profile = profile_options[selected_label]

    # Profile card
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sector", f"{SECTOR_ICONS.get(profile['sector'], '')} {profile['sector']}")
    col2.metric("Country", profile["country"])
    col3.metric("Employees", profile["employees"])
    col4.metric("Language(s)", ", ".join(profile["languages"]).upper())
    st.info(f"📋 **Need:** {profile['needs_text']}")
    if profile.get("past_funding") and profile["past_funding"] != "None":
        st.caption(f"💰 Past funding: {profile['past_funding']}")

    run = st.button("🚀 Find Matching Grants", type="primary", use_container_width=True)

    if run:
        from ranker import rank as rank_tenders
        from summarizer import generate_summary

        with st.spinner("Ranking tenders…"):
            results = rank_tenders(profile, tenders, topk=topk)

        gold_ids = gold.get(profile["id"], [])

        st.subheader(f"Top {topk} Matches for Profile {profile['id']}")

        # Quick metrics row
        hits = sum(1 for r in results if r["id"] in gold_ids)
        top1_in_gold = results[0]["id"] in gold_ids if results else False
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric-box"><b style="font-size:2em">{len(results)}</b><br>Tenders ranked</div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box"><b style="font-size:2em">{hits}/{len(gold_ids) or "?"}</b><br>Gold matches found</div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box"><b style="font-size:2em">{"✅" if top1_in_gold else "⚠️"}</b><br>Top-1 is gold</div>', unsafe_allow_html=True)

        st.write("")

        for i, r in enumerate(results, 1):
            is_gold = r["id"] in gold_ids
            card_cls = "tender-card-fr" if r.get("language") == "fr" else "tender-card"
            gold_tag = " 🥇 **GOLD MATCH**" if is_gold else ""

            with st.container():
                st.markdown(
                    f'<div class="{card_cls}">'
                    f'<b>#{i}</b>  {lang_badge(r.get("language","en"))}  {sector_badge(r.get("sector","?"))}'
                    f'  <b>{r.get("title","")[:70]}</b>{gold_tag}'
                    f'<br><small>📁 {r["id"]}  |  💰 {r.get("budget_norm","?")}  |  '
                    f'📅 Deadline: {r.get("deadline","?")}  |  🌍 {r.get("region","?")}</small>'
                    f'<br>{score_bar_html(r["score"])}'
                    f'<small>Score: <b>{r["score"]:.4f}</b></small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if show_breakdown:
                    bd = r.get("score_breakdown", {})
                    cols = st.columns(len(bd))
                    labels = {"semantic": "🧠 Semantic", "sector_match": "🏷️ Sector",
                              "budget_fit": "💰 Budget", "deadline": "📅 Deadline",
                              "language": "🌐 Language"}
                    for col, (k, v) in zip(cols, bd.items()):
                        col.metric(labels.get(k, k), f"{v:.2f}")

                if show_summary:
                    summary = generate_summary(profile, r, include_why_not=show_why_not)
                    with st.expander("📝 Match Summary", expanded=(i == 1)):
                        st.markdown(summary)

# ── Mode: Custom Query ────────────────────────────────────────────────────────
else:
    st.subheader("✏️ Custom Query Search")
    st.caption("Type your needs in English or French — the matcher handles both.")

    col_a, col_b = st.columns([3, 1])
    with col_a:
        query_text = st.text_area(
            "Describe your funding needs",
            placeholder="e.g.  je cherche un grant pour agritech, 50k or less, Rwanda\n"
                        "or:   We need funding for solar micro-grids in East Africa",
            height=100,
        )
    with col_b:
        query_sector = st.selectbox("Sector (optional)", ["(any)"] + [
            "agritech", "healthtech", "cleantech", "edtech", "fintech", "wastetech"
        ])
        query_lang = st.selectbox("Language preference", ["en", "fr"])
        query_country = st.text_input("Country", placeholder="e.g. Rwanda")

    run_custom = st.button("🔍 Search", type="primary", use_container_width=True)

    if run_custom and query_text.strip():
        from ranker import rank as rank_tenders
        from summarizer import generate_summary

        # Build an ad-hoc profile from the query
        custom_profile = {
            "id":          "custom",
            "sector":      query_sector if query_sector != "(any)" else "",
            "country":     query_country or "Africa",
            "employees":   10,
            "languages":   [query_lang],
            "needs_text":  query_text,
            "past_funding": "None",
        }

        with st.spinner("Searching…"):
            results = rank_tenders(custom_profile, tenders, topk=topk)

        st.subheader(f"Top {topk} Results for Your Query")
        for i, r in enumerate(results, 1):
            card_cls = "tender-card-fr" if r.get("language") == "fr" else "tender-card"
            st.markdown(
                f'<div class="{card_cls}">'
                f'<b>#{i}</b>  {lang_badge(r.get("language","en"))}  {sector_badge(r.get("sector","?"))}'
                f'  <b>{r.get("title","")[:70]}</b>'
                f'<br><small>📁 {r["id"]}  |  💰 {r.get("budget_norm","?")}  |  '
                f'📅 {r.get("deadline","?")}  |  🌍 {r.get("region","?")}</small>'
                f'<br>{score_bar_html(r["score"])}'
                f'<small>Score: <b>{r["score"]:.4f}</b></small>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if show_summary:
                summary = generate_summary(custom_profile, r, include_why_not=show_why_not)
                with st.expander("📝 Summary", expanded=(i == 1)):
                    st.markdown(summary)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "T2.2 · AIMS KTT Fellowship Hackathon · April 2026 · "
    "Model: paraphrase-multilingual-MiniLM-L12-v2 (HuggingFace) · "
    "CPU-only · < 3 min full run"
)
