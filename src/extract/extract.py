"""Stage 1: pull articles out of Confluence into data/raw/.

  ./doc-loader.sh extract check
  ./doc-loader.sh extract search "CC-00001"
  ./doc-loader.sh extract all "<URL of the parent page>"        every article under it
  ./doc-loader.sh extract all "<URL of the parent page>" --overwrite
  ./doc-loader.sh extract fetch CC-00001                        just one (demo)
  ./doc-loader.sh extract fetch "<URL of one article>"          same, by URL
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so "src" imports work

from src import config
from src.extract.confluence import ConfluenceClient

RAW_DIR = config.ROOT / "data" / "raw"
ARTICLE_TITLE = re.compile(r"^[A-Z]+\d*-\d+\b")
MIGRATION_PARENT_ID = "4295229446"  # "GG Knowledge Articles (unpublished) GG-Migration"


def page_id_from_url(url):
    """Pull the page ID out of a Confluence page URL (.../pages/<id>/<title>)."""
    match = re.search(r"/pages/(\d+)", url)
    if not match:
        raise SystemExit(
            "That doesn't look like a Confluence page URL (expected .../pages/<id>/<title>)."
        )
    return match.group(1)


def pick_articles(pages):
    """Return {article number: (page id, title)} for the numbered articles in a page list.

    Some articles exist twice: the original and a copy titled "GG8-00007 [UPDATE]: ...".
    The [UPDATE] copy replaces the original, so only that one is kept.
    """
    articles = {}
    for page_id, title in pages:
        match = ARTICLE_TITLE.match(title)
        if not match:
            continue
        number = match.group(0)
        if number not in articles or "[UPDATE]" in title:
            articles[number] = (page_id, title)
    return articles


def page_id_from_article_number(client, article_number):
    """Find the page for an article number such as CC-00001."""
    articles = pick_articles(client.list_descendants(MIGRATION_PARENT_ID))
    number = article_number.upper()
    if number not in articles:
        raise SystemExit(f"No article {article_number} found under the migration page.")
    return articles[number][0]


def resolve_page_id(client, target):
    """Accept an article number (CC-00001) or a Confluence page URL."""
    if ARTICLE_TITLE.match(target.upper()) and "/" not in target:
        return page_id_from_article_number(client, target)
    return page_id_from_url(target)


def slim(page, base_url):
    """Keep only the fields later stages need. The body is passed through untouched."""
    return {
        "id": page["id"],
        "title": page["title"],
        "body": page["body"]["storage"]["value"],
        "labels": [label["name"] for label in page["metadata"]["labels"]["results"]],
        "version": page["version"]["number"],
        "space": page["space"]["key"],
        "source_url": base_url + page["_links"]["webui"],
    }


def article_dir(title):
    """Folder for an article, named by its article number, e.g. data/raw/CC-00001."""
    return RAW_DIR / ARTICLE_TITLE.match(title).group(0)


def save_article(client, page_id):
    """Save a page as data/raw/<article number>/article.json, plus attachments/ if it has any."""
    article = slim(client.get_page(page_id), client.base_url)
    folder = article_dir(article["title"])
    folder.mkdir(parents=True, exist_ok=True)

    attachments = client.list_attachments(page_id)
    if attachments:
        (folder / "attachments").mkdir(exist_ok=True)
        for filename, download_path in attachments:
            client.download(download_path, folder / "attachments" / filename)
    article["attachments"] = [filename for filename, _ in attachments]

    (folder / "article.json").write_text(json.dumps(article, indent=2))
    return article


def extract_all(client, parent_id, overwrite):
    """Save every article under parent_id. One failure doesn't stop the rest."""
    # Knowledge articles have a numbered title like "GG8-00164: ...", "GG9-00036: ...", "CC-00012: ...".
    everything = client.list_descendants(parent_id)
    pages = list(pick_articles(everything).values())
    print(
        f"Found {len(pages)} articles under page {parent_id} "
        f"({len(everything) - len(pages)} other or superseded pages ignored)."
    )
    saved, skipped, failed = 0, 0, []
    for number, (page_id, title) in enumerate(pages, start=1):
        if not overwrite and (article_dir(title) / "article.json").exists():
            skipped += 1
            continue
        try:
            save_article(client, page_id)
            saved += 1
            print(f"[{number}/{len(pages)}] saved {page_id} {title}")
        except Exception as error:  # report and carry on with the remaining articles
            failed.append((page_id, title, error))
            print(f"[{number}/{len(pages)}] FAILED {page_id} {title}: {error}")
    print(f"\nDone: {saved} saved, {skipped} skipped (already saved), {len(failed)} failed.")
    for page_id, title, error in failed:
        print(f"  FAILED {page_id} {title}: {error}")
    return not failed


def main():
    parser = argparse.ArgumentParser(prog="doc-loader.sh extract")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="verify the Confluence credentials work")
    search = sub.add_parser("search", help="find page IDs by title or text")
    search.add_argument("text")
    all_cmd = sub.add_parser("all", help="save every article under a parent page")
    all_cmd.add_argument("url", help="URL of the parent page")
    all_cmd.add_argument(
        "--overwrite", action="store_true", help="re-fetch articles that are already saved"
    )
    fetch = sub.add_parser("fetch", help="save one article to data/raw/")
    fetch.add_argument("article", help="article number (CC-00001) or Confluence page URL")
    args = parser.parse_args()

    client = ConfluenceClient()
    if args.command == "check":
        print(f"Connected to Confluence as {client.check_connection()}")
    elif args.command == "search":
        rows = client.search_pages(args.text)
        for page_id, title, space in rows:
            print(f"{page_id}\t{space}\t{title}")
        if not rows:
            print("No pages found.")
    elif args.command == "all":
        if not extract_all(client, page_id_from_url(args.url), args.overwrite):
            sys.exit(1)
    else:
        page_id = resolve_page_id(client, args.article)
        article = save_article(client, page_id)
        folder = article_dir(article["title"]).relative_to(config.ROOT)
        print(f"Saved '{article['title']}' to {folder}/")


if __name__ == "__main__":
    main()
