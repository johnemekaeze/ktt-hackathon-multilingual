"""
push_to_hf.py — Upload dataset and model card to Hugging Face Hub.

Usage:
    python push_to_hf.py --token YOUR_HF_TOKEN

Or set env variable HF_TOKEN and run:
    python push_to_hf.py

Creates:
  - Dataset repo : johneze/ktt-t22-grants-tenders
  - Model repo   : johneze/ktt-t22-grant-matcher
"""

import argparse
import os
import shutil
import sys

HF_USERNAME  = "johneze"
DATASET_REPO = f"{HF_USERNAME}/ktt-t22-grants-tenders"
MODEL_REPO   = f"{HF_USERNAME}/ktt-t22-grant-matcher"


def push(token: str):
    try:
        from huggingface_hub import HfApi, CommitOperationAdd
    except ImportError:
        print("Installing huggingface_hub …")
        os.system(f"{sys.executable} -m pip install huggingface_hub -q")
        from huggingface_hub import HfApi, CommitOperationAdd

    api = HfApi(token=token)

    # ── 1. Verify token ────────────────────────────────────────────────────────
    user = api.whoami()
    print(f"✅ Logged in as: {user['name']}")

    # ── 2. Dataset repo ────────────────────────────────────────────────────────
    print(f"\n📦 Creating dataset repo: {DATASET_REPO}")
    api.create_repo(
        repo_id=DATASET_REPO,
        repo_type="dataset",
        exist_ok=True,
        private=False,
    )

    # Upload dataset_card.md as README.md
    api.upload_file(
        path_or_fileobj="dataset_card.md",
        path_in_repo="README.md",
        repo_id=DATASET_REPO,
        repo_type="dataset",
        commit_message="Add dataset card",
    )
    print("  ✅ README.md uploaded")

    # Upload profiles.json and gold_matches.csv
    for fname in ["profiles.json", "gold_matches.csv"]:
        api.upload_file(
            path_or_fileobj=fname,
            path_in_repo=fname,
            repo_id=DATASET_REPO,
            repo_type="dataset",
            commit_message=f"Add {fname}",
        )
        print(f"  ✅ {fname} uploaded")

    # Upload all tenders as a folder
    print("  📂 Uploading tenders/ folder …")
    api.upload_folder(
        folder_path="tenders",
        path_in_repo="tenders",
        repo_id=DATASET_REPO,
        repo_type="dataset",
        commit_message="Add tender documents (40 EN/FR)",
    )
    print("  ✅ tenders/ uploaded (40 documents)")

    # Upload generator script
    api.upload_file(
        path_or_fileobj="generate_data.py",
        path_in_repo="generate_data.py",
        repo_id=DATASET_REPO,
        repo_type="dataset",
        commit_message="Add reproducible data generator",
    )
    print("  ✅ generate_data.py uploaded")

    print(f"\n🎉 Dataset live: https://huggingface.co/datasets/{DATASET_REPO}")

    # ── 3. Model repo ──────────────────────────────────────────────────────────
    print(f"\n🤖 Creating model repo: {MODEL_REPO}")
    api.create_repo(
        repo_id=MODEL_REPO,
        repo_type="model",
        exist_ok=True,
        private=False,
    )

    # Upload model card as README.md
    api.upload_file(
        path_or_fileobj="hf_model_card.md",
        path_in_repo="README.md",
        repo_id=MODEL_REPO,
        repo_type="model",
        commit_message="Add model card",
    )
    print("  ✅ Model card uploaded")

    # Upload core Python modules so the repo is self-contained
    for fname in ["matcher.py", "ranker.py", "parser.py",
                  "summarizer.py", "evaluate.py", "requirements.txt"]:
        api.upload_file(
            path_or_fileobj=fname,
            path_in_repo=fname,
            repo_id=MODEL_REPO,
            repo_type="model",
            commit_message=f"Add {fname}",
        )
        print(f"  ✅ {fname} uploaded")

    print(f"\n🎉 Model repo live: https://huggingface.co/{MODEL_REPO}")

    print("\n" + "="*60)
    print("✅ HuggingFace upload complete!")
    print(f"  Dataset : https://huggingface.co/datasets/{DATASET_REPO}")
    print(f"  Model   : https://huggingface.co/{MODEL_REPO}")
    print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", type=str, default=os.environ.get("HF_TOKEN", ""))
    args = parser.parse_args()

    if not args.token:
        print("❌  No HF token found.")
        print("    Get yours at: https://huggingface.co/settings/tokens")
        print("    Then run:  python push_to_hf.py --token hf_xxxxxxxxxxxx")
        sys.exit(1)

    push(args.token)
