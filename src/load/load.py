"""Stage 3: post the Zendesk-ready articles in data/out/ to Zendesk as drafts.

  ./doc-loader.sh load one CC-00001 --dry-run     print the payload, send nothing (needs no login)
  ./doc-loader.sh load one CC-00001               post one article (demo)
  ./doc-loader.sh load all                        post every article in data/out/

Each data/out/<number>/article.json (written by the transform stage) holds "title" and "body".
After a successful post, the Zendesk article ID is saved next to it in posted.json,
so running again skips articles that are already in Zendesk.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so "src" imports work

from src import config
from src.load.zendesk import ZendeskClient

OUT_DIR = config.ROOT / "data" / "out"
LOCALE = "en-us"


def build_payload(article, permission_group_id):
    """Turn a transformed article into the Zendesk "article" object (always a draft)."""
    return {
        "title": article["title"],
        "body": article["body"],
        "locale": LOCALE,
        "draft": True,
        "permission_group_id": permission_group_id,
    }


def load_article(number):
    path = OUT_DIR / number / "article.json"
    if not path.exists():
        raise SystemExit(f"No transformed article at {path}. Run the transform stage first.")
    return json.loads(path.read_text())


def post_article(client, number):
    """Post one article and record its Zendesk ID. Returns the ID."""
    article = load_article(number)
    zendesk_id = client.create_article(build_payload(article, client.permission_group_id))
    (OUT_DIR / number / "posted.json").write_text(json.dumps({"zendesk_id": zendesk_id}))
    return zendesk_id


def dry_run(number):
    config.load_dotenv()
    group = os.environ.get("ZENDESK_PERMISSION_GROUP_ID") or "<ZENDESK_PERMISSION_GROUP_ID>"
    payload = build_payload(load_article(number), group)
    print(json.dumps({"article": payload}, indent=2))


def load_all(client):
    """Post every article not yet posted. One failure doesn't stop the run."""
    posted, skipped, failed = 0, 0, []
    for folder in sorted(p for p in OUT_DIR.iterdir() if p.is_dir()):
        number = folder.name
        if (folder / "posted.json").exists():
            skipped += 1
            continue
        try:
            post_article(client, number)
            posted += 1
            print(f"posted {number}")
        except Exception as err:  # keep going; report at the end
            failed.append((number, str(err)))
            print(f"FAILED {number}: {err}")
    print(f"\n{posted} posted, {skipped} already posted, {len(failed)} failed")
    for number, err in failed:
        print(f"  {number}: {err}")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(prog="load", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("one", help="post a single article by number")
    one.add_argument("number")
    one.add_argument("--dry-run", action="store_true", help="print the payload only")
    sub.add_parser("all", help="post every article in data/out/")
    args = parser.parse_args()

    if args.command == "one":
        number = args.number.upper()
        if args.dry_run:
            dry_run(number)
            return 0
        if (OUT_DIR / number / "posted.json").exists():
            print(f"{number} is already in Zendesk, skipping.")
            return 0
        zendesk_id = post_article(ZendeskClient(), number)
        print(f"posted {number} as Zendesk article {zendesk_id} (draft)")
        return 0
    return load_all(ZendeskClient())


if __name__ == "__main__":
    sys.exit(main())
