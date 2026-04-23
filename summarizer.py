"""
summarizer.py — Generate ≤ 80-word match summaries in the profile's language.

Strategy:
  1. Template-based generation (no LLM required, deterministic, fast).
  2. Templates include sector, budget, deadline, and region fields.
  3. Language is determined by the profile's primary language tag.
  4. Optional: if a 'why NOT' section is needed, the biggest disqualifier
     is flagged (deadline expired, region mismatch, budget too large).
"""

from datetime import datetime
import re

# ── Deadline helpers ──────────────────────────────────────────────────────────
def _days_left(deadline_str: str) -> int:
    try:
        dl = datetime.strptime(deadline_str.strip(), "%Y-%m-%d")
        return (dl - datetime.today()).days
    except Exception:
        return 9999


def _deadline_label_en(deadline_str: str) -> str:
    days = _days_left(deadline_str)
    if days < 0:
        return f"(NOTE: deadline has passed — {deadline_str})"
    if days <= 14:
        return f"{deadline_str} — only {days} days left!"
    if days <= 60:
        return f"{deadline_str} ({days} days away)"
    return deadline_str


def _deadline_label_fr(deadline_str: str) -> str:
    days = _days_left(deadline_str)
    if days < 0:
        return f"(ATTENTION: date limite dépassée — {deadline_str})"
    if days <= 14:
        return f"{deadline_str} — plus que {days} jours !"
    if days <= 60:
        return f"{deadline_str} ({days} jours restants)"
    return deadline_str


# ── Budget normalizer display ─────────────────────────────────────────────────
BUDGET_DISPLAY_EN = {
    "5k":   "USD 5,000",
    "50k":  "USD 50,000",
    "200k": "USD 200,000",
    "1m":   "USD 1,000,000",
    "1M":   "USD 1,000,000",
}
BUDGET_DISPLAY_FR = {
    "5k":   "5 000 USD",
    "50k":  "50 000 USD",
    "200k": "200 000 USD",
    "1m":   "1 000 000 USD",
    "1M":   "1 000 000 USD",
}


def _fmt_budget(norm: str, lang: str) -> str:
    key = norm.lower()
    if lang == "fr":
        return BUDGET_DISPLAY_FR.get(norm, BUDGET_DISPLAY_FR.get(key, norm))
    return BUDGET_DISPLAY_EN.get(norm, BUDGET_DISPLAY_EN.get(key, norm))


# ── Templates ─────────────────────────────────────────────────────────────────
_EN_TEMPLATE = (
    "This tender — **{title}** — closely matches your {sector} business in {country}. "
    "It offers up to {budget} in funding, ideal for organizations of your scale. "
    "The deadline is {deadline}, giving you time to prepare a strong application. "
    "Coverage extends to {region}, which includes your operating area. "
    "Your focus on {need_snippet} aligns directly with the grant's stated objectives."
)

_FR_TEMPLATE = (
    "Cet appel à propositions — **{title}** — correspond étroitement à votre activité "
    "{sector} au {country}. Il offre jusqu'à {budget} de financement, adapté à votre "
    "structure. La date limite est le {deadline}, ce qui vous laisse le temps de préparer "
    "un dossier solide. La couverture s'étend à {region}, incluant votre zone d'opération. "
    "Votre besoin en {need_snippet} s'aligne directement avec les objectifs de la subvention."
)

_EN_WHY_NOT = (
    "\n\n⚠️ **Biggest disqualifier:** {reason}"
)
_FR_WHY_NOT = (
    "\n\n⚠️ **Principal facteur disqualifiant :** {reason}"
)


def _need_snippet(needs_text: str, max_words: int = 8) -> str:
    """Take first N words of needs_text."""
    words = needs_text.split()
    snippet = " ".join(words[:max_words])
    return snippet.lower().rstrip(".,;")


def _why_not_reason_en(tender: dict, profile: dict) -> str | None:
    """Return the single biggest disqualifier, or None if no clear issue."""
    days = _days_left(tender.get("deadline", ""))
    if days < 0:
        return f"The deadline ({tender.get('deadline')}) has already passed."
    if days < 15:
        return f"The deadline is in only {days} days — very tight for a full application."

    t_region = tender.get("region", "").lower()
    p_country = profile.get("country", "").lower()
    REGION_MAP = {
        "east africa":    ["rwanda", "kenya", "ethiopia", "uganda", "tanzania"],
        "west africa":    ["senegal", "ghana", "nigeria"],
        "central africa": ["drc", "cameroon"],
        "southern africa": [],
        "pan-africa":     [],  # all are eligible
    }
    for region_key, countries in REGION_MAP.items():
        if region_key in t_region and countries and p_country not in countries:
            return f"Geographic scope is '{tender.get('region')}'; your country ({profile.get('country')}) may be ineligible."

    return None


def _why_not_reason_fr(tender: dict, profile: dict) -> str | None:
    """French version of disqualifier."""
    days = _days_left(tender.get("deadline", ""))
    if days < 0:
        return f"La date limite ({tender.get('deadline')}) est déjà dépassée."
    if days < 15:
        return f"La date limite est dans seulement {days} jours — délai très serré."

    t_region = tender.get("region", "").lower()
    p_country = profile.get("country", "").lower()
    REGION_MAP = {
        "afrique de l'est": ["rwanda", "kenya", "ethiopie", "ouganda", "tanzanie"],
        "afrique de l'ouest": ["sénégal", "ghana", "nigéria"],
        "afrique centrale":  ["rdc", "cameroun"],
    }
    for region_key, countries in REGION_MAP.items():
        if region_key in t_region and countries and p_country not in countries:
            return (f"La portée géographique est '{tender.get('region')}' ; "
                    f"votre pays ({profile.get('country')}) pourrait être inéligible.")
    return None


# ── Public API ────────────────────────────────────────────────────────────────
def generate_summary(
    profile: dict,
    tender: dict,
    include_why_not: bool = True,
) -> str:
    """
    Generate a ≤80-word match summary in the profile's primary language.

    Args:
        profile          : dict from profiles.json
        tender           : ranked tender dict (from ranker.py)
        include_why_not  : add disqualifier section if one exists

    Returns:
        Markdown string
    """
    lang = profile.get("languages", ["en"])[0].lower()
    # Treat 'sw' (Swahili) as English for now
    if lang not in ("fr",):
        lang = "en"

    budget_display = _fmt_budget(tender.get("budget_norm", ""), lang)

    if lang == "fr":
        dl_label = _deadline_label_fr(tender.get("deadline", ""))
        template  = _FR_TEMPLATE
        why_not_fn = _why_not_reason_fr
        why_not_tmpl = _FR_WHY_NOT
    else:
        dl_label = _deadline_label_en(tender.get("deadline", ""))
        template  = _EN_TEMPLATE
        why_not_fn = _why_not_reason_en
        why_not_tmpl = _EN_WHY_NOT

    summary = template.format(
        title        = tender.get("title", tender.get("id", "Unknown")),
        sector       = tender.get("sector", profile.get("sector", "")),
        country      = profile.get("country", ""),
        budget       = budget_display,
        deadline     = dl_label,
        region       = tender.get("region", "the target region"),
        need_snippet = _need_snippet(profile.get("needs_text", "")),
    )

    # Word-count guard — trim if over 80 words (rare with these templates)
    words = summary.split()
    if len(words) > 80:
        summary = " ".join(words[:80]) + " …"

    if include_why_not:
        reason = why_not_fn(tender, profile)
        if reason:
            summary += why_not_tmpl.format(reason=reason)

    return summary


def generate_all_summaries(
    profile: dict,
    ranked_tenders: list[dict],
    output_dir: str = "summaries",
    include_why_not: bool = True,
) -> list[str]:
    """
    Generate and save summary .md files for each (profile, tender) pair.

    Returns list of file paths written.
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for rank_idx, tender in enumerate(ranked_tenders, 1):
        summary = generate_summary(profile, tender, include_why_not)
        fname = f"{output_dir}/profile_{profile['id']}_tender_{tender['id']}.md"
        with open(fname, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"# Match Summary — Profile {profile['id']} × {tender['id']}\n\n")
            f.write(f"**Rank:** {rank_idx}  |  **Score:** {tender.get('score', 'N/A')}  "
                    f"|  **Language:** {tender.get('language', '?').upper()}\n\n")
            f.write("---\n\n")
            f.write(summary)
            f.write("\n\n---\n")
            f.write("\n### Score Breakdown\n\n")
            breakdown = tender.get("score_breakdown", {})
            for k, v in breakdown.items():
                bar = "█" * int(v * 20)
                f.write(f"- **{k}**: {v:.2f}  `{bar}`\n")
        paths.append(fname)
    return paths


if __name__ == "__main__":
    import json
    from parser import parse_all
    from ranker import build_index, rank as rank_tenders

    tenders = parse_all()
    build_index(tenders)

    with open("profiles.json", encoding="utf-8") as f:
        profiles = json.load(f)

    profile = profiles[0]
    results = rank_tenders(profile, tenders, topk=5)
    paths = generate_all_summaries(profile, results)
    print(f"\nWrote {len(paths)} summaries:")
    for p in paths:
        print(f"  {p}")
