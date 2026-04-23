# process_log.md — T2.2 Build Log

**Challenge:** T2.2 · Multilingual Grant & Tender Matcher with Summarizer  
**Candidate:** John Eze  
**Date:** April 23, 2026  
**Hard cap:** 4 hours

---

## Hour-by-Hour Timeline

| Time | Activity |
|------|----------|
| 00:00 – 00:20 | Read brief end-to-end, identified 5 key deliverables, sketched file architecture |
| 00:20 – 00:40 | Set up project structure, created directories, `requirements.txt`, `LICENSE` |
| 00:40 – 01:20 | Built `generate_data.py` — 40 EN/FR tenders (txt/html), 10 profiles, gold_matches.csv |
| 01:20 – 01:50 | Built `parser.py` — txt/html/pdf reading, language detection, field extraction, budget normalizer |
| 01:50 – 02:30 | Built `ranker.py` — designed 5-component scoring formula, integrated MiniLM embeddings + TF-IDF fallback |
| 02:30 – 02:50 | Built `summarizer.py` — bilingual templates (EN/FR), "why not" disqualifier logic |
| 02:50 – 03:10 | Built `matcher.py` CLI, tested `--profile 02 --topk 5` and `--all` flags |
| 03:10 – 03:30 | Built `evaluate.py`, `eval_notebook.ipynb` — MRR@5, Recall@5, confusion analysis |
| 03:30 – 03:45 | Wrote `village_agent.md` — WhatsApp audio design, cost math, 90-day roadmap |
| 03:45 – 04:00 | Wrote `README.md`, `process_log.md`, `SIGNED.md`, final review |

---

## LLM / Tool Usage

| Tool | Used for | Why |
|------|----------|-----|
| **GitHub Copilot (Claude Sonnet 4.6)** | Code scaffolding, boilerplate generation, template design | Speed up file creation; I reviewed and modified all logic, especially the scoring formula weights and budget normalization |
| **None other** | — | No ChatGPT, no external prompting tools used for final code |

---

## Three Sample Prompts Sent

### Prompt 1 (kept)
> *"Build ranker.py for a multilingual grant matcher. Use paraphrase-multilingual-MiniLM-L12-v2 embeddings. The scoring formula should combine semantic similarity (40%), sector match (25%), budget fit (20%), deadline proximity (10%), and language match (5%). Include a TF-IDF fallback if sentence-transformers is unavailable. Explain each component."*

**Why I kept it:** This produced the backbone of `ranker.py`. I then manually tuned the budget_fit sigmoid and the deadline_score thresholds (30–180 day sweet spot) based on the brief's spec.

### Prompt 2 (kept)
> *"Write a village_agent.md for an illiterate cooperative leader in rural Rwanda. Compare three distribution options: IVR voice centre, WhatsApp audio broadcast, printed bulletin board. Show weekly cost at 500 cooperatives in RWF. Recommend one with reasoning. Include privacy/consent plan."*

**Why I kept it:** The cost structure required real RWF math. I verified the WhatsApp API pricing (~USD 0.005/message) and the agent hourly rate (RWF 3,500/hr) against current market rates and adjusted accordingly.

### Prompt 3 (discarded)
> *"Use an LLM API to generate the 80-word summaries dynamically."*

**Why I discarded it:** The brief specifies CPU-only, < 3 minute total run time. An LLM API call per (profile × tender) pair would be 50+ API calls, adding latency, cost, and a network dependency. Template-based summarization is deterministic, fast, and sufficient for the 80-word constraint. I kept the template approach.

---

## Hardest Decision

The hardest decision was **how to weight the five scoring components** in `ranker.py`. 

The naive approach is equal weights (20% each), but this fails when a semantically similar tender is in the wrong sector — the semantic score inflates its rank. After experimenting, I settled on **40% semantic / 25% sector** because:

1. Semantic similarity captures cross-lingual alignment (a French agritech tender should match an English agritech profile even if no keywords overlap).
2. Sector match at 25% is strong enough to demote cross-sector false positives, but not so high that it makes the semantic score irrelevant.
3. Budget fit at 20% prevents micro-SMEs from being matched to USD 1M grants they can't absorb.

The tradeoff: if the sector field is missing from a tender (common in poorly structured PDFs), the score degrades to pure semantic + budget + deadline. The `parse_tender()` function's robustness in extracting the sector field is therefore critical. This was tested and verified with the synthetic data generator.

---

*Log completed: April 23, 2026*
