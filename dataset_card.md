---
license: mit
task_categories:
  - text-classification
  - text-retrieval
language:
  - en
  - fr
tags:
  - grants
  - tenders
  - multilingual
  - africa
  - govtech
  - information-retrieval
  - synthetic
pretty_name: "T2.2 Multilingual Grant & Tender Dataset"
size_categories:
  - n<1K
---

# T2.2 — Multilingual Grant & Tender Dataset

Synthetic dataset for the AIMS KTT Fellowship Hackathon, Challenge T2.2:
**Multilingual Grant & Tender Matcher with Summarizer**.

## Dataset Description

Reproducible synthetic dataset of African Union and regional grant/tender documents,
designed to test multilingual information retrieval and summarization systems.

### Files

| File | Description |
|------|-------------|
| `tenders/*.txt` | 32 English tender documents (24 plain text + 8 HTML) |
| `tenders/*.txt` | 8 French tender documents |
| `profiles.json` | 10 business profiles (Rwanda, Kenya, Senegal, DRC, Ethiopia) |
| `gold_matches.csv` | 30 expert-curated (profile, tender) gold match pairs |

### Tender Fields

Each tender document contains:
- `TITLE` / `TITRE`
- `SECTOR` / `SECTEUR` — one of: agritech, healthtech, cleantech, edtech, fintech, wastetech
- `BUDGET` — one of: USD 5,000 / 50,000 / 200,000 / 1,000,000
- `DEADLINE` / `DATE LIMITE` — ISO date
- `REGION` / `RÉGION` — East/West/Central/Southern Africa or Pan-Africa
- `ELIGIBILITY` / `ÉLIGIBILITÉ`
- Boilerplate bureaucratic text

### Profile Fields

```json
{
  "id": "01",
  "sector": "agritech",
  "country": "Rwanda",
  "employees": 5,
  "languages": ["en"],
  "needs_text": "We need funding to scale our drone-based crop monitoring service...",
  "past_funding": "World Bank small grant 2023"
}
```

## Generation

Fully reproducible:

```bash
git clone https://github.com/YOUR_USERNAME/ktt-hackathon-multilingual
cd ktt-hackathon-multilingual
pip install -r requirements.txt
python generate_data.py   # regenerates all files with seed=42
```

## Usage

```bash
python matcher.py --profile 02 --topk 5
```

## License

MIT
