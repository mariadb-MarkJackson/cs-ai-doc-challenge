# CLAUDE.md

## Project
Work challenge (team of two, demo due **Oct 14**): build, with Claude Code, a tool that imports knowledge base articles into Zendesk (Dev first, then Prod). Details are in `docs/` (challenge PDF).

- The demo must show one article imported into Zendesk Dev, and that article must contain a code block. The tool must be viable for the full collection.
- Content must not change during import, only formatting.
- Not in scope: validating the technical accuracy of articles.
- Eligibility: team of two, each presenting their own AI-assisted workflow; successful recorded Dev import; **no credentials hard-coded or committed**.
- Scoring: learning/reflection 28%, teamwork 18%, AI-assisted workflow 18%, import quality 18%, engineering soundness 18%.

## Zendesk article requirements
- `body` HTML has exactly four sections in this order: **Issue, Environment, Cause, Resolution**. If the source lacks a section, still include it with "Not applicable".
- Articles are created in **Draft** status (`draft: true`).
- Articles are set to the permission group **"KCS Content"** (`permission_group_id`, the PDF's "Management permissions" link). It is a permission group, not a content tag.
- Style: sentence case for the title and headings; `<code>` for literals and identifiers; `<em>` for placeholders; Resolution is a numbered list with destructive steps flagged in `<strong>`; "primary"/"replica" never "master"/"slave"; no "kill", "abort", "hang", "simply", "obviously", "basically", "easy".
- API: `POST /api/v2/help_center/sections/{section_id}/articles`. Needs title, locale, permission_group_id; body is HTML (unsafe tags are stripped). Attachments use the article attachments endpoint.

## Architecture
Three stages, each saving output to disk so it can be inspected and re-run on its own:

1. `src/extract/`: pull articles from the MariaDB Confluence into `data/raw/` (built, see below).
2. `src/transform/`: convert each raw article into Zendesk article JSON in `data/out/` (not started).
3. `src/load/`: read `data/out/` and POST to Zendesk as drafts (not started).

The tool is specific to this challenge, not a generic migration tool.

### Extract (built)
- Source: all knowledge articles live under the Confluence page "GG Knowledge Articles (unpublished) GG-Migration" (page ID `4295229446`, set as `MIGRATION_PARENT_ID` in `src/extract/extract.py`).
- An article is a page with a numbered title: `CC-nnnnn`, `GG8-nnnnn`, or `GG9-nnnnn`. Other pages under the parent (large guides, index page, challenge pages) are ignored.
- If an article exists twice, as the original and a copy titled `... [UPDATE]: ...` (GG8-00007, GG8-00012, GG8-00015), only the `[UPDATE]` copy is kept.
- Output is one folder per article, named by article number: `data/raw/<number>/article.json`, plus `data/raw/<number>/attachments/` only when the article has attachments. `article.json` holds `id` (page ID), `title`, `body` (Confluence storage HTML, untouched), `labels`, `version`, `space`, `source_url`, `attachments`.
- Extract never changes content. All reshaping happens in transform.
- Result of the first full run: 246 articles, 0 failures, and none of them have attachments or images (so attachment download is written but untested).

### Still to design
- Load: images/attachments (if any appear) would be uploaded to the Zendesk article as inline attachments and the body links rewritten. The Zendesk docs mention a Guide media object / `guide_media_id` requirement for attachment uploads; confirm against Zendesk Dev before building.
- A demo mode (one article, `--dry-run` prints the payload) and an all mode (success/failure report, one failure not stopping the batch, no duplicate posts on re-run) for load.

## Credentials
Token-based so anyone can run the tool; no dependence on Claude or MCP access at runtime. Each user puts their own tokens in a local, gitignored `.env`. `.env.example` lists the variable names only. The tool must fail fast listing missing variables and must never log or print tokens.

## Status and open decisions
- Extract is built and working against the MariaDB Confluence. Transform and load are not started. Nothing is committed beyond the folder skeleton.
- Language: Python (requests; pytest planned). The tool is run through `./doc-loader.sh`, which creates `.venv` and installs `requirements.txt` on first use.
- Source: the MariaDB Confluence (mariadbcorp.atlassian.net) via REST API token. The cloned article repo is no longer being considered.
- Whether Claude's API assists with sorting content into the four sections, or this is rule-based only. If used, a validator must confirm no source text was changed.
- Still needed from Zendesk Dev: API token, subdomain, section_id, permission_group_id, and the id of the "KCS Content" permission group (contact Caleb Terry or William Fong).

## Working notes
- Keep a `docs/LEARNINGS.md` log of prompts used, what was accepted vs rewritten, and where AI helped or got in the way; it feeds the reflection criterion.
- Both teammates should be able to explain the whole solution; review each other's changes.

## Decisions
- **Titles are migrated as-is** (no rewording into the "customer question" form). Revisit after the demo.
- Demo article: `CC-00001` (Confluence page `4295950337`), "Control Center Okta Integration with OAuth2 and OIDC" (has a `code` macro, no images). Source is the MariaDB Confluence (mariadbcorp.atlassian.net).
- "All articles" means the numbered articles under the migration parent page (246 after keeping only `[UPDATE]` copies). Un-numbered guides are out of scope for now.
- Standards reference: "KCS Content Standards" (Support space, page `4321607725`). Every article uses Title, Issue, Environment, Cause, Resolution, Metadata; there is no separate informational template.
- Extract saves articles untouched. Transform checks for each of Issue, Environment, Cause, Resolution: sections the source already has are kept, and missing ones are added (Cause is "Informational" for informational guides). Still open: where "Additional Information" / "Related Topics" go under the four-section rule.

## Running the tool
`./doc-loader.sh <stage> [args]`. Settings come from a local `.env` (copy `.env.example`; never commit `.env`).

```
./doc-loader.sh extract check                      # test the Confluence login
./doc-loader.sh extract fetch CC-00001             # one article by article number (or a page URL)
./doc-loader.sh extract all "<parent page URL>"    # every article under the migration page
./doc-loader.sh extract all "<parent page URL>" --overwrite   # re-fetch ones already saved
./doc-loader.sh extract search "text"              # find pages by title or text
```
