"""
parser.py — Parse tenders/ folder into structured records.
Handles .txt, .html, and .pdf files.
Detects language automatically.
"""

import os
import re
from pathlib import Path

try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# ── Budget normalizer ─────────────────────────────────────────────────────────
BUDGET_PATTERN = re.compile(
    r"(USD\s?[\d,]+|[\d\s]+USD|\$[\d,]+|\d[\d\s]*000[\s]*USD|"
    r"\d+[\s]?[kKmM][\s]?USD|[\d\s]+\s?(?:dollars?|USD))",
    re.IGNORECASE,
)

BUDGET_TIER = {
    5_000:       "5k",
    50_000:      "50k",
    200_000:     "200k",
    1_000_000:   "1M",
}


def normalize_budget(raw: str) -> str:
    """Return a canonical budget tier string."""
    if not raw:
        return "unknown"
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        return raw.strip()
    amount = int(digits)
    # snap to nearest tier
    for threshold, label in BUDGET_TIER.items():
        if abs(amount - threshold) / threshold < 0.5:
            return label
    return f"{amount:,} USD"


# ── Date normalizer ───────────────────────────────────────────────────────────
DATE_PATTERN = re.compile(
    r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|"
    r"janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)"
    r"\s+\d{4})\b",
    re.IGNORECASE,
)


def extract_field(text: str, *keys: str) -> str:
    """Extract value after a label key in text."""
    for key in keys:
        pattern = re.compile(
            rf"(?:^|\n){re.escape(key)}\s*[:\-]\s*(.+)", re.IGNORECASE
        )
        m = pattern.search(text)
        if m:
            return m.group(1).strip()
    return ""


def detect_language(text: str) -> str:
    """Return ISO 639-1 language code ('en' or 'fr')."""
    if not LANGDETECT_AVAILABLE:
        # Heuristic fallback
        fr_words = {"subvention", "secteur", "région", "éligibilité", "délai",
                    "organisme", "titre", "budget", "bénéficiaires", "candidature"}
        words = set(re.findall(r"\b\w+\b", text.lower()))
        return "fr" if len(words & fr_words) >= 2 else "en"
    try:
        return detect(text[:500])
    except Exception:
        return "en"


# ── File readers ──────────────────────────────────────────────────────────────
def read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_html(path: str) -> str:
    raw = read_txt(path)
    if BS4_AVAILABLE:
        soup = BeautifulSoup(raw, "html.parser")
        return soup.get_text(separator="\n")
    # Fallback: strip tags with regex
    return re.sub(r"<[^>]+>", " ", raw)


def read_pdf(path: str) -> str:
    if not PDF_AVAILABLE:
        return ""
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)


# ── Main parser ───────────────────────────────────────────────────────────────
def parse_tender(filepath: str) -> dict:
    """
    Parse a single tender file into a structured record.

    Returns:
        {
          id, file, title, sector, budget, budget_norm,
          deadline, region, eligibility, language, text
        }
    """
    path = Path(filepath)
    ext  = path.suffix.lower()

    if ext == ".txt":
        text = read_txt(filepath)
    elif ext in (".htm", ".html"):
        text = read_html(filepath)
    elif ext == ".pdf":
        text = read_pdf(filepath)
    else:
        text = read_txt(filepath)

    lang = detect_language(text)

    # Field extraction (bilingual keys)
    title = (
        extract_field(text, "TITLE", "TITRE")
        or path.stem.replace("_", " ").title()
    )
    sector = (
        extract_field(text, "SECTOR", "SECTEUR") or ""
    ).lower().strip()
    budget_raw = (
        extract_field(text, "BUDGET")
        or (BUDGET_PATTERN.search(text).group(0) if BUDGET_PATTERN.search(text) else "")
    )
    deadline = extract_field(text, "DEADLINE", "DATE LIMITE", "ÉCHÉANCE")
    region   = extract_field(text, "REGION", "RÉGION")
    eligibility = extract_field(text, "ELIGIBILITY", "ÉLIGIBILITÉ")

    return {
        "id":          path.stem,
        "file":        str(path),
        "title":       title,
        "sector":      sector,
        "budget_raw":  budget_raw,
        "budget_norm": normalize_budget(budget_raw),
        "deadline":    deadline,
        "region":      region,
        "eligibility": eligibility,
        "language":    lang,
        "text":        text,
    }


def parse_all(tenders_dir: str = "tenders") -> list[dict]:
    """Parse every file in tenders_dir and return list of records."""
    records = []
    supported = {".txt", ".html", ".htm", ".pdf"}
    for fname in sorted(os.listdir(tenders_dir)):
        ext = Path(fname).suffix.lower()
        if ext in supported:
            fpath = os.path.join(tenders_dir, fname)
            try:
                rec = parse_tender(fpath)
                records.append(rec)
            except Exception as e:
                print(f"  ⚠️  Could not parse {fname}: {e}")
    return records


if __name__ == "__main__":
    records = parse_all()
    print(f"\nParsed {len(records)} tenders:")
    for r in records:
        print(f"  [{r['language'].upper()}] {r['id']:12s} | {r['sector']:10s} | "
              f"{r['budget_norm']:8s} | {r['deadline']}")
