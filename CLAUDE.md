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
- Articles get the content tag **"KCS Content"**.
- Style: sentence case for the title and headings; `<code>` for literals and identifiers; `<em>` for placeholders; Resolution is a numbered list with destructive steps flagged in `<strong>`; "primary"/"replica" never "master"/"slave"; no "kill", "abort", "hang", "simply", "obviously", "basically", "easy".
- API: `POST /api/v2/help_center/sections/{section_id}/articles`. Needs title, locale, permission_group_id; body is HTML (unsafe tags are stripped). Attachments use the article attachments endpoint.

## Architecture
Three stages, each saving output to disk so it can be inspected and re-run on its own:

1. `src/extract/`: pull articles (and attachments) from the source into `data/raw/`.
2. `src/transform/`: convert each raw article into Zendesk article JSON in `data/out/`.
3. `src/load/`: read `data/out/` and POST to Zendesk as drafts.

Each module folder holds its own code. Extract sits behind a small source interface so it can read from the Confluence REST API or from the cloned article repo (GridGain or MariaDB); transform and load do not care where an article came from.

CLI intent: a demo mode (specific page IDs, `--dry-run` prints the payload) and an all mode (whole space or label, with a success/failure report, one failure not stopping the batch, and no duplicate posts on re-run).

## Credentials
Token-based so anyone can run the tool; no dependence on Claude or MCP access at runtime. Each user puts their own tokens in a local, gitignored `.env`. `.env.example` lists the variable names only. The tool must fail fast listing missing variables and must never log or print tokens.

## Status and open decisions
- Folder skeleton created; no code yet.
- Language: Python recommended (requests, beautifulsoup4/lxml, pytest); not yet confirmed.
- Source: Confluence (ggsystems.atlassian.net) vs the cloned article repo, and the clone's format, are undecided.
- Whether Claude's API assists with sorting content into the four sections, or this is rule-based only. If used, a validator must confirm no source text was changed.
- Still needed from Zendesk Dev: API token, subdomain, section_id, permission_group_id, "KCS Content" tag id (contact Caleb Terry or William Fong).

## Working notes
- Keep a `docs/LEARNINGS.md` log of prompts used, what was accepted vs rewritten, and where AI helped or got in the way; it feeds the reflection criterion.
- Both teammates should be able to explain the whole solution; review each other's changes.
