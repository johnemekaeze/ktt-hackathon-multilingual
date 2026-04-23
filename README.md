# Multilingual Grant & Tender Matcher with Summarizer
### AIMS KTT Hackathon · T2.2 · Tier 2 · April 2026

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![CPU-only](https://img.shields.io/badge/hardware-CPU--only-green.svg)]()

---

## Problem Statement

African Union and regional bodies publish thousands of grants and tenders in EN/FR, in dense bureaucratic language. Entrepreneurs miss the right ones. This tool ranks the most relevant tenders for each business profile and writes a short summary explaining **why they match**, in the profile's preferred language.

---

## Quick Start (≤ 2 commands)

```bash
pip install -r requirements.txt
python generate_data.py && python matcher.py --profile 02 --topk 5
```

> Tested on Python 3.10+, CPU-only. Full run of all 10 profiles < 3 minutes.

## 🚀 Live Demo

```bash
streamlit run app.py
```

Opens a browser UI where you can:
- Select any of the 10 profiles and get ranked tenders with score breakdowns
- Type a custom query in **English or French** (code-switching supported)
- Toggle match summaries and "Why NOT" disqualifier sections

---

## Project Structure

```
.
├── generate_data.py      # Reproducible synthetic data generator
├── parser.py             # Document parser (.txt, .html, .pdf)
├── ranker.py             # Multilingual matcher (MiniLM embeddings + rules)
├── summarizer.py         # Summary generator (≤80 words, EN/FR)
├── matcher.py            # CLI entry point
├── evaluate.py           # MRR@5, Recall@5 evaluation script
├── eval_notebook.ipynb   # Evaluation notebook with charts
├── village_agent.md      # Product & Business adaptation artifact
├── profiles.json         # 10 business profiles (auto-generated)
├── gold_matches.csv      # Ground truth matches (auto-generated)
├── tenders/              # 40 tender documents (EN/FR, .txt/.html)
├── summaries/            # Generated match summaries (.md per pair)
├── process_log.md        # Hour-by-hour build log + LLM usage
├── SIGNED.md             # Honor code
└── requirements.txt      # Python dependencies
```

---

## CLI Usage

```bash
# Match top 5 tenders for profile 02
python matcher.py --profile 02 --topk 5

# Match profile 07 (French speaker)
python matcher.py --profile 07 --topk 5

# Run all 10 profiles, skip why-not section
python matcher.py --all --topk 5 --no-why-not

# Only print results, don't write summary files
python matcher.py --profile 03 --topk 5 --no-summaries
```

**Sample output:**
```
══════════════════════════════════════════════════════════════════════
  PROFILE 02  |  HEALTHTECH  |  Kenya  |  Lang: en
  Need: Seeking grants to deploy low-cost diagnostic kits in rural health clinics.
══════════════════════════════════════════════════════════════════════

  1. [EN] tender_02        score=0.8231 ████████░░
     Title   : African Development Fund — Healthtech Development Grant 02
     Sector  : healthtech   Budget: 50k      Deadline: 2026-09-14
     Score ↘  sem=0.71  sec=1.00  bud=0.82  dea=1.00  lan=1.00
```

---

## How It Works

### 1. Parsing (`parser.py`)
- Reads `.txt`, `.html`, `.pdf` tender files
- Extracts: title, sector, budget, deadline, region, eligibility
- Language detection via `langdetect` (fallback: keyword heuristic)
- Budget normalization to canonical tiers: `5k / 50k / 200k / 1M`

### 2. Ranking (`ranker.py`)
Scoring formula — transparent and defensible:

```python
score = (
    0.40 * semantic_similarity     # MiniLM-L12-v2 cosine similarity
  + 0.25 * sector_match            # exact=1.0, partial=0.5, none=0.0
  + 0.20 * budget_fit              # log-scale proximity to profile needs
  + 0.10 * deadline_score          # 1.0 if 30-180 days, 0.0 if expired
  + 0.05 * language_match          # 1.0 if tender lang == profile lang
)
```

**Model:** `paraphrase-multilingual-MiniLM-L12-v2`
- Size: ~118 MB (under 150 MB constraint ✅)
- Supports: EN, FR, SW, AR, and 50+ languages
- CPU inference: ~2s per profile for 40 tenders

### 3. Summarization (`summarizer.py`)
- Template-based, ≤ 80 words, in the profile's primary language
- Cites: sector, budget, deadline, region, profile need
- Optional **"Why NOT"** section flags the single biggest disqualifier
  (expired deadline, geographic scope mismatch)

### 4. Evaluation (`evaluate.py` / `eval_notebook.ipynb`)
- **MRR@5** (Mean Reciprocal Rank)
- **Recall@5** (fraction of gold matches retrieved in top 5)
- 3 confusion case analyses with root-cause explanation

---

## Evaluation Results

| Metric | Score |
|--------|-------|
| MRR@5 | **0.81** |
| Recall@5 | **0.80** |

> All 10 profiles retrieved at least 2 of 3 gold matches in top 5.

> See `eval_notebook.ipynb` for full breakdown, confusion cases, and visualisations.

---

## Model Hosting

The multilingual embedding model is downloaded automatically from Hugging Face on first run:

**`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`**
- 🤗 https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- Size: ~118 MB | CPU-only | 50+ languages

No checkpoint is uploaded separately — the model is pulled from the public HF Hub.

---

## Dataset

All 40 tenders and 10 profiles are generated by `generate_data.py` (reproducible, seed=42).  
No external data files required.

---

## Product & Business Adaptation

See [`village_agent.md`](village_agent.md) for the full offline distribution design:
- Target: illiterate cooperative leader, rural Africa
- **Recommended channel: WhatsApp Audio Broadcast**
- Weekly cost at 500 cooperatives: **RWF 9,000/week** (RWF 18/coop/week)
- CAC: **RWF 1,200/cooperative**
- Privacy/consent plan, 90-day scale roadmap, and sample Kinyarwanda script included

---

## Video Demo

📹 **[Video link — add before submission]**

Structure:
- `0:00–0:30` On-camera intro
- `0:30–1:30` Code walkthrough (`matcher.py::rank()`)
- `1:30–2:30` Live demo: profiles 02 and 07
- `2:30–3:30` Read FR + EN summaries aloud; walk through `village_agent.md`
- `3:30–4:00` Three Q&A answers

---

## Requirements

```
sentence-transformers>=2.2.0
scikit-learn>=1.3.0
langdetect>=1.0.9
beautifulsoup4>=4.12.0
pdfplumber>=0.10.0
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
```

Install: `pip install -r requirements.txt`

---

## Reproducing Results

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate data
python generate_data.py

# 3. Run matcher
python matcher.py --all --topk 5

# 4. Evaluate
python evaluate.py

# 5. Open notebook
jupyter notebook eval_notebook.ipynb
```

---

## License

MIT — see [LICENSE](LICENSE)

---

*AIMS KTT Fellowship Hackathon · T2.2 · John Eze · April 2026*
