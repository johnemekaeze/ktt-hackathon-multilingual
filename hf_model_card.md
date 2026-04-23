---
license: mit
base_model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
tags:
  - sentence-transformers
  - feature-extraction
  - information-retrieval
  - multilingual
  - grants
  - tenders
  - africa
  - govtech
language:
  - en
  - fr
  - sw
metrics:
  - mrr
  - recall
---

# T2.2 — Multilingual Grant & Tender Matcher

**AIMS KTT Fellowship Hackathon · Tier 2 · April 2026**  
**Challenge:** T2.2 · Multilingual Grant & Tender Matching with Summarization  
**Author:** John Eze ([@johneze](https://huggingface.co/johneze))  
**Code:** [github.com/johnemekaeze/ktt-hackathon-multilingual](https://github.com/johnemekaeze/ktt-hackathon-multilingual)

---

## Model Description

This is an **applied retrieval system** built on top of
[`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
for matching African business profiles to the most relevant grant and tender
opportunities published by AU, ECOWAS, EAC, and other regional bodies.

The base model is used **as-is** (no fine-tuning). The contribution of this
project is the **scoring pipeline** that combines semantic similarity from the
model with structured rule-based features.

---

## Scoring Formula

```python
score = (
    0.40 * semantic_similarity   # cosine similarity via MiniLM-L12-v2
  + 0.25 * sector_match          # exact=1.0 | partial=0.5 | none=0.0
  + 0.20 * budget_fit            # log-scale proximity to profile needs
  + 0.10 * deadline_score        # 1.0 if 30–180 days remaining
  + 0.05 * language_match        # 1.0 if tender lang == profile lang
)
```

---

## Evaluation Results

Evaluated against `gold_matches.csv` (3 expert-curated matches × 10 profiles).

| Metric | Score |
|--------|-------|
| **MRR@5** | **0.95** |
| **Recall@5** | **0.77** |
| Profiles evaluated | 10 |
| Tender corpus | 40 (EN: 32, FR: 8) |

- **MRR@5 = 0.95** → 9 of 10 profiles have their top-1 recommendation be a gold match  
- **Recall@5 = 0.77** → on average 2.3 of 3 gold tenders appear in the top-5

---

## Base Model

| Property | Value |
|----------|-------|
| Model | `paraphrase-multilingual-MiniLM-L12-v2` |
| Size | ~118 MB |
| Languages | 50+ (EN, FR, SW natively) |
| Hardware | CPU-only |
| Inference time | < 3 min for 40 tenders × 10 profiles |

---

## Usage

```bash
git clone https://github.com/johnemekaeze/ktt-hackathon-multilingual
cd ktt-hackathon-multilingual
pip install -r requirements.txt
python generate_data.py
python matcher.py --profile 02 --topk 5
```

**Live demo (Streamlit):**
```bash
streamlit run app.py
```

---

## Dataset

The dataset used to evaluate this model is hosted at:
[huggingface.co/datasets/johneze/ktt-t22-grants-tenders](https://huggingface.co/datasets/johneze/ktt-t22-grants-tenders)

---

## Product Adaptation

This matcher is designed for deployment to **illiterate cooperative leaders**
in rural Africa via **WhatsApp audio broadcast** (weekly cadence, RWF 18/cooperative/week
at 500 cooperatives scale). See [`village_agent.md`](https://github.com/johnemekaeze/ktt-hackathon-multilingual/blob/main/village_agent.md) for full design.

---

## Citation

```bibtex
@misc{eze2026t22,
  author       = {John Eze},
  title        = {T2.2 Multilingual Grant & Tender Matcher},
  year         = {2026},
  publisher    = {Hugging Face},
  howpublished = {\\url{https://huggingface.co/johneze/ktt-t22-grant-matcher}}
}
```
