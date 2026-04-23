"""
matcher.py — CLI entry point for the Multilingual Grant & Tender Matcher.

Usage:
    python matcher.py --profile 02 --topk 5
    python matcher.py --profile 07 --topk 3 --no-why-not
    python matcher.py --all --topk 5

Output:
    - Ranked tender list printed to stdout (with scores and language labels)
    - Summary .md files written to summaries/
"""

import argparse
import json
import os
import sys
import time

from parser import parse_all
from ranker import build_index, rank as rank_tenders
from summarizer import generate_all_summaries


# ── Helpers ───────────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
CYAN   = "\033[36m"
YELLOW = "\033[33m"
RED    = "\033[31m"
BLUE   = "\033[34m"


def _color(text: str, code: str) -> str:
    """Apply ANSI color if stdout is a tty."""
    if sys.stdout.isatty():
        return f"{code}{text}{RESET}"
    return text


def _budget_bar(score: float, width: int = 10) -> str:
    filled = int(score * width)
    return "█" * filled + "░" * (width - filled)


def print_results(profile: dict, results: list[dict], show_breakdown: bool = True):
    """Pretty-print ranked tender results."""
    print()
    print(_color(f"{'═'*70}", CYAN))
    print(_color(
        f"  PROFILE {profile['id']}  |  {profile['sector'].upper()}  "
        f"|  {profile['country']}  |  "
        f"Lang: {', '.join(profile.get('languages', ['en']))}",
        BOLD
    ))
    print(_color(f"  Need: {profile.get('needs_text', '')[:80]}…", CYAN))
    print(_color(f"{'═'*70}", CYAN))
    print()

    for i, r in enumerate(results, 1):
        lang_tag   = _color(f"[{r.get('language','?').upper()}]", YELLOW if r.get('language') == 'fr' else GREEN)
        score_bar  = _budget_bar(r["score"])
        score_str  = _color(f"{r['score']:.4f}", BOLD)

        print(f"  {_color(str(i), BOLD)}. {lang_tag} {_color(r['id'], BLUE):20s} "
              f"score={score_str} {score_bar}")
        print(f"     Title   : {r.get('title','')[:65]}")
        print(f"     Sector  : {r.get('sector',''):12s}  Budget: {r.get('budget_norm',''):8s}  "
              f"Deadline: {r.get('deadline','')}")

        if show_breakdown:
            bd = r.get("score_breakdown", {})
            parts = "  ".join(
                f"{k[:3]}={v:.2f}" for k, v in bd.items()
            )
            print(f"     Score ↘  {parts}")
        print()

    print(_color(f"{'─'*70}", CYAN))
    print()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Multilingual Grant & Tender Matcher (T2.2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python matcher.py --profile 02 --topk 5
  python matcher.py --profile 07 --topk 3 --no-why-not
  python matcher.py --all --topk 5 --no-summaries
        """,
    )
    parser.add_argument("--profile",     type=str, help="Profile ID (e.g. 02)")
    parser.add_argument("--all",         action="store_true", help="Run all 10 profiles")
    parser.add_argument("--topk",        type=int, default=5,  help="Number of results (default 5)")
    parser.add_argument("--tenders-dir", type=str, default="tenders", help="Path to tenders folder")
    parser.add_argument("--profiles-file", type=str, default="profiles.json")
    parser.add_argument("--summaries-dir", type=str, default="summaries")
    parser.add_argument("--no-summaries", action="store_true", help="Skip writing summary files")
    parser.add_argument("--no-why-not",   action="store_true", help="Omit disqualifier section")
    args = parser.parse_args()

    if not args.profile and not args.all:
        parser.print_help()
        sys.exit(0)

    # ── Load data ──────────────────────────────────────────────────────────────
    t0 = time.time()
    if not os.path.exists(args.tenders_dir):
        print(f"❌  Tenders folder '{args.tenders_dir}' not found.")
        print("    Run:  python generate_data.py   first.")
        sys.exit(1)

    print(f"\n📂 Parsing tenders from '{args.tenders_dir}' …")
    tenders = parse_all(args.tenders_dir)
    print(f"   {len(tenders)} tenders loaded  "
          f"(EN: {sum(1 for t in tenders if t['language']=='en')}  "
          f"FR: {sum(1 for t in tenders if t['language']=='fr')})")

    print("🔍 Building search index …")
    build_index(tenders)

    with open(args.profiles_file, encoding="utf-8") as f:
        all_profiles = json.load(f)

    # ── Select profiles ────────────────────────────────────────────────────────
    if args.all:
        selected = all_profiles
    else:
        selected = [p for p in all_profiles if p["id"] == args.profile]
        if not selected:
            print(f"❌  Profile '{args.profile}' not found in {args.profiles_file}")
            sys.exit(1)

    # ── Run matching ───────────────────────────────────────────────────────────
    total_summaries = 0
    for profile in selected:
        results = rank_tenders(profile, tenders, topk=args.topk)
        print_results(profile, results)

        if not args.no_summaries:
            paths = generate_all_summaries(
                profile, results,
                output_dir=args.summaries_dir,
                include_why_not=not args.no_why_not,
            )
            total_summaries += len(paths)
            print(f"  📝 Wrote {len(paths)} summary files → {args.summaries_dir}/")

    elapsed = time.time() - t0
    print(_color(f"\n✅  Done in {elapsed:.1f}s", GREEN))
    if total_summaries:
        print(f"   {total_summaries} summary file(s) in {args.summaries_dir}/")
    print()


if __name__ == "__main__":
    main()
