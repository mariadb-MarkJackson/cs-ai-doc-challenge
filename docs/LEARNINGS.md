# Learnings log

Running notes for the "what you learned" part of the demo (worth 28%). Be specific: real prompts, real outcomes. Add entries as we go, not at the end.

## Entry template

### YYYY-MM-DD, who, what we were doing
- **Prompt / approach:**
- **What Claude gave us:**
- **Accepted / rewritten / rejected, and why:**
- **How we checked quality:**
- **Where AI sped us up:**
- **Where it got in the way:**
- **What we'd do differently:**

## Entries

### 2026-10-08, planning
- **Prompt / approach:** Gave Claude the challenge PDF and asked for a plan before any code (plan mode).
- **What Claude gave us:** A plan with Python, a Confluence REST source, and a single module list.
- **Accepted / rewritten / rejected, and why:** Rewrote the structure into three stages (extract, transform, load) that save output to disk, and one folder per module. Rejected the first folder layout (`src/` grouping).
- **How we checked quality:** Reviewed the plan against the PDF's article format requirements.
- **Where AI sped us up:** Read the PDF and surveyed the Zendesk API and Confluence spaces quickly.
- **Where it got in the way:** It submitted the plan for approval before explaining it to us.
- **What we'd do differently:** Talk through the design before asking Claude to write it up.
