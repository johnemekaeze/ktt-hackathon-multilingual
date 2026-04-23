"""
ranker.py — Rank tenders for a given business profile.

Scoring formula (transparent & defensible):
    score = 0.40 * semantic_sim
          + 0.25 * sector_match
          + 0.20 * budget_fit
          + 0.10 * deadline_score
          + 0.05 * language_match

Uses: paraphrase-multilingual-MiniLM-L12-v2  (<150 MB, CPU-only, multilingual)
Falls back to TF-IDF if sentence-transformers is unavailable.
"""

import re
import math
import numpy as np
from datetime import datetime
from typing import Optional

# ── Optional heavy imports ────────────────────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    USE_EMBEDDINGS = True
    print("✅ Using multilingual embeddings (MiniLM-L12-v2)")
except (ImportError, OSError, Exception):
    USE_EMBEDDINGS = False
    print("⚠️  sentence-transformers unavailable — falling back to TF-IDF")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ── Budget normalizer (mirrors parser.py) ─────────────────────────────────────
BUDGET_MAP = {
    "5k":  5_000,
    "50k": 50_000,
    "200k": 200_000,
    "1m":  1_000_000,
}

def budget_to_usd(raw: str) -> Optional[float]:
    """Convert budget string to USD float."""
    if not raw:
        return None
    lower = raw.lower().replace(",", "").replace(" ", "")
    for k, v in BUDGET_MAP.items():
        if k in lower:
            return float(v)
    digits = re.sub(r"[^\d]", "", raw)
    return float(digits) if digits else None


def budget_fit_score(profile_needs: str, tender_budget_raw: str) -> float:
    """
    0-1 score. Profiles implicitly need budgets ≥ 5k; penalise very large
    grants that a micro-SME cannot absorb, reward exact-ish matches.
    """
    tender_usd = budget_to_usd(tender_budget_raw)
    if tender_usd is None:
        return 0.5  # neutral when unknown

    # Extract any mentioned amount from the profile needs
    profile_amounts = re.findall(r"\b(\d[\d,]*)\s*k?\b", profile_needs, re.IGNORECASE)
    if profile_amounts:
        # Take the largest mentioned figure as upper limit
        profile_usd = max(
            float(a.replace(",", "")) * (1000 if "k" in profile_needs.lower() else 1)
            for a in profile_amounts
        )
        ratio = min(tender_usd, profile_usd) / max(tender_usd, profile_usd)
        return float(ratio)

    # No explicit amount in profile — sigmoid on log scale
    # Peak at 50k (typical SME grant)
    log_diff = abs(math.log10(tender_usd + 1) - math.log10(50_000))
    return float(math.exp(-0.5 * log_diff))


def deadline_score(deadline_str: str) -> float:
    """
    Returns 1.0 if deadline is 30-180 days away (sweet spot),
    decays for very close (rushed) or very far (irrelevant now).
    """
    if not deadline_str:
        return 0.5
    # Try ISO format
    try:
        dl = datetime.strptime(deadline_str.strip(), "%Y-%m-%d")
    except ValueError:
        return 0.5
    days_left = (dl - datetime.today()).days
    if days_left < 0:
        return 0.0   # already expired
    if 30 <= days_left <= 180:
        return 1.0
    if days_left < 30:
        return days_left / 30.0
    # > 180 days — slight decay
    return max(0.3, 1.0 - (days_left - 180) / 365.0)


# ── TF-IDF fallback ───────────────────────────────────────────────────────────
_tfidf_vec: Optional[object] = None
_tfidf_matrix = None
_tfidf_tender_ids: list = []


def _build_tfidf(tenders: list[dict]):
    global _tfidf_vec, _tfidf_matrix, _tfidf_tender_ids
    if not SKLEARN_AVAILABLE:
        return
    corpus = [t.get("text", t.get("title", "")) for t in tenders]
    _tfidf_vec = TfidfVectorizer(
        strip_accents="unicode",
        ngram_range=(1, 2),
        max_features=20_000,
        sublinear_tf=True,
    )
    _tfidf_matrix = _tfidf_vec.fit_transform(corpus)
    _tfidf_tender_ids = [t["id"] for t in tenders]


def _tfidf_similarity(query: str, tender_idx: int) -> float:
    if _tfidf_vec is None or _tfidf_matrix is None:
        return 0.0
    q_vec = _tfidf_vec.transform([query])
    sim = sk_cosine(q_vec, _tfidf_matrix[tender_idx])[0][0]
    return float(sim)


# ── Embedding similarity ──────────────────────────────────────────────────────
_embed_cache: dict = {}


def _embed(text: str) -> np.ndarray:
    if text not in _embed_cache:
        _embed_cache[text] = _model.encode(text, normalize_embeddings=True)
    return _embed_cache[text]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))   # already normalized


# ── Public API ────────────────────────────────────────────────────────────────
def build_index(tenders: list[dict]):
    """Pre-compute embeddings / TF-IDF matrix for all tenders."""
    if USE_EMBEDDINGS:
        texts = [t.get("text", t.get("title", "")) for t in tenders]
        print(f"  📐 Encoding {len(texts)} tenders with MiniLM …", end=" ", flush=True)
        vecs = _model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        for i, t in enumerate(tenders):
            t["_embedding"] = vecs[i]
        print("done")
    else:
        _build_tfidf(tenders)


def rank(profile: dict, tenders: list[dict], topk: int = 5) -> list[dict]:
    """
    Rank tenders for a profile.

    Args:
        profile : dict from profiles.json
        tenders : parsed tender records (must have called build_index first)
        topk    : number of results to return

    Returns:
        list of dicts sorted by score descending, each extended with
        { score, score_breakdown }
    """
    # Build profile query from needs text + sector + country
    query = (
        f"{profile.get('needs_text', '')} "
        f"sector:{profile.get('sector', '')} "
        f"country:{profile.get('country', '')}"
    )
    profile_sector = profile.get("sector", "").lower().strip()
    profile_langs  = [l.lower() for l in profile.get("languages", ["en"])]
    primary_lang   = profile_langs[0]

    if USE_EMBEDDINGS:
        q_emb = _embed(query)
    else:
        q_emb = None

    scored = []
    for i, tender in enumerate(tenders):
        # 1. Semantic / lexical similarity
        if USE_EMBEDDINGS and "_embedding" in tender:
            sem = _cosine(q_emb, tender["_embedding"])
        elif SKLEARN_AVAILABLE and _tfidf_vec is not None:
            sem = _tfidf_similarity(query, i)
        else:
            sem = 0.5

        # 2. Sector match (exact = 1, partial = 0.5, none = 0)
        t_sector = tender.get("sector", "").lower().strip()
        if t_sector == profile_sector:
            sec_score = 1.0
        elif t_sector and profile_sector and (
            t_sector in profile_sector or profile_sector in t_sector
        ):
            sec_score = 0.5
        else:
            sec_score = 0.0

        # 3. Budget fit
        bud_score = budget_fit_score(
            profile.get("needs_text", ""),
            tender.get("budget_raw", tender.get("budget_norm", ""))
        )

        # 4. Deadline
        dl_score = deadline_score(tender.get("deadline", ""))

        # 5. Language match
        t_lang = tender.get("language", "en").lower()
        lang_score = 1.0 if t_lang in profile_langs else 0.3

        # Weighted composite
        score = (
            0.40 * sem
            + 0.25 * sec_score
            + 0.20 * bud_score
            + 0.10 * dl_score
            + 0.05 * lang_score
        )

        entry = {**tender, "score": round(score, 4),
                 "score_breakdown": {
                     "semantic":      round(sem, 4),
                     "sector_match":  round(sec_score, 4),
                     "budget_fit":    round(bud_score, 4),
                     "deadline":      round(dl_score, 4),
                     "language":      round(lang_score, 4),
                 }}
        scored.append(entry)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:topk]


if __name__ == "__main__":
    from parser import parse_all
    import json

    tenders  = parse_all()
    build_index(tenders)

    with open("profiles.json", encoding="utf-8") as f:
        profiles = json.load(f)

    profile = profiles[0]
    results = rank(profile, tenders, topk=5)
    print(f"\nTop 5 for profile {profile['id']} ({profile['sector']}, {profile['country']}):")
    for r in results:
        print(f"  [{r['score']:.4f}] {r['id']:12s} [{r['language'].upper()}] "
              f"{r['sector']:10s} {r['budget_norm']:8s}  deadline:{r['deadline']}")
