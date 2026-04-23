"""
evaluate.py — Compute MRR@5 and Recall@5, show 3 confusion cases.
Can be run standalone or imported by the notebook.
"""

import csv
import json
from collections import defaultdict

from parser import parse_all
from ranker import build_index, rank as rank_tenders


def load_gold(path: str = "gold_matches.csv") -> dict[str, list[str]]:
    """Returns {profile_id: [tender_id1, tender_id2, ...]} ordered by rank."""
    gold = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = sorted(reader, key=lambda r: int(r["rank"]))
        for row in rows:
            gold[row["profile_id"]].append(row["tender_id"])
    return dict(gold)


def evaluate(tenders_dir="tenders", profiles_file="profiles.json",
             gold_file="gold_matches.csv", topk=5):
    """
    Returns:
        results : list of per-profile dicts
        metrics : {mrr@5, recall@5, mrr_macro, recall_macro}
    """
    tenders = parse_all(tenders_dir)
    build_index(tenders)

    with open(profiles_file, encoding="utf-8") as f:
        profiles = json.load(f)
    gold = load_gold(gold_file)

    results = []
    for profile in profiles:
        pid = profile["id"]
        ranked = rank_tenders(profile, tenders, topk=topk)
        predicted_ids = [r["id"] for r in ranked]
        relevant_ids  = gold.get(pid, [])

        # MRR@k — reciprocal rank of first relevant result
        rr = 0.0
        for i, tid in enumerate(predicted_ids, 1):
            if tid in relevant_ids:
                rr = 1.0 / i
                break

        # Recall@k — fraction of gold hits retrieved
        hits = sum(1 for tid in predicted_ids if tid in relevant_ids)
        recall = hits / len(relevant_ids) if relevant_ids else 0.0

        results.append({
            "profile_id":    pid,
            "sector":        profile["sector"],
            "country":       profile["country"],
            "predicted":     predicted_ids,
            "relevant":      relevant_ids,
            "hits":          hits,
            "rr":            round(rr, 4),
            "recall_at_k":   round(recall, 4),
            "ranked_objects": ranked,
        })

    mrr    = sum(r["rr"] for r in results) / len(results)
    recall = sum(r["recall_at_k"] for r in results) / len(results)

    metrics = {
        "MRR@5":      round(mrr, 4),
        "Recall@5":   round(recall, 4),
        "n_profiles": len(results),
        "topk":       topk,
    }
    return results, metrics


def find_confusion_cases(results: list[dict], n: int = 3) -> list[dict]:
    """
    Return the n most interesting failure/partial-failure cases:
    - First: any profile where RR < 1.0 (top-1 prediction is NOT a gold match)
    - Then: profiles with the lowest Recall@5 (gold matches missed in top-5)
    This ensures we never show a perfect profile as a "confusion case".
    """
    # Sort: RR ascending first, then recall ascending as tiebreaker
    worst = sorted(results, key=lambda r: (r["rr"], r["recall_at_k"]))[:n]
    cases = []
    for r in worst:
        top_pred = r["predicted"][0] if r["predicted"] else None
        top_obj  = next(
            (t for t in r["ranked_objects"] if t["id"] == top_pred), {}
        )
        case = {
            "profile_id":   r["profile_id"],
            "sector":       r["sector"],
            "rr":           r["rr"],
            "recall":       r["recall_at_k"],
            "top_predicted": top_pred,
            "gold_ids":      r["relevant"],
            "top_score":     top_obj.get("score", 0),
            "top_sector":    top_obj.get("sector", "?"),
            "top_budget":    top_obj.get("budget_norm", "?"),
            "breakdown":     top_obj.get("score_breakdown", {}),
        }
        cases.append(case)
    return cases


if __name__ == "__main__":
    results, metrics = evaluate()
    print("\n📊 Evaluation Results")
    print(f"  MRR@5    : {metrics['MRR@5']}")
    print(f"  Recall@5 : {metrics['Recall@5']}")
    print(f"  Profiles : {metrics['n_profiles']}")

    print("\n🔎 Per-profile breakdown:")
    for r in results:
        hit_mark = "✅" if r["hits"] > 0 else "❌"
        print(f"  {hit_mark} Profile {r['profile_id']} ({r['sector']:10s}) | "
              f"RR={r['rr']:.2f}  Recall={r['recall_at_k']:.2f}  "
              f"hits={r['hits']}/{len(r['relevant'])}")

    print("\n⚠️  Top 3 Confusion Cases:")
    cases = find_confusion_cases(results)
    for c in cases:
        print(f"\n  Profile {c['profile_id']} ({c['sector']}) — RR={c['rr']}")
        print(f"    Top predicted : {c['top_predicted']} (score={c['top_score']:.4f})")
        print(f"    Gold answers  : {c['gold_ids']}")
        print(f"    Sector mismatch: predicted={c['top_sector']}, profile={c['sector']}")
        print(f"    Score breakdown: {c['breakdown']}")
        # Explain
        if c["top_sector"] != c["sector"]:
            print(f"    ❗ Root cause: semantic similarity pulled in a '{c['top_sector']}' "
                  f"tender despite sector mismatch. Fix: increase sector_match weight.")
        elif c["top_budget"] in ("1M", "200k") and "small" in str(c.get("needs", "")):
            print(f"    ❗ Root cause: budget ({c['top_budget']}) too large for the profile.")
