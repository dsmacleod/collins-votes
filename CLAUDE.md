# Project: Susan Collins Vote Tracker

An interactive newsroom tool (Bangor Daily News) that ranks Sen. Susan Collins'
Senate votes by importance. Readers control what "important" means via four weighted
factors: vote closeness, how decisive she was, breaking with her party, and topic salience.

## Files
- `collins-votes-tool.html` — self-contained reader tool. Scoring engine + sliders are
  inline near the bottom in `<script>`. Seeded with 12 demo votes in `const VOTES = [...]`.
- `scrape_collins_votes.py` — pulls Collins' full roll-call record (1997–present) from
  senate.gov, scores it, writes `collins_votes.json` + `collins_votes.csv`.
- `HANDOFF.md` — plain-English overview (the owner, Dan, is a journalist, not a coder).

## Current state / likely next steps
1. Run the scraper (`pip install requests && python3 scrape_collins_votes.py`) to
   generate the real dataset, then replace the demo `VOTES` array in the HTML with the
   JSON — or wire the HTML to `fetch('collins_votes.json')` so refreshes are one re-run.
2. Verify the 9 unverified demo tallies if they're kept (3 are marked ✓ verified).
3. Tune `TOPIC_RULES` salience weights in the scraper to match newsroom editorial judgment.
4. Optional: match BDN site styling; add CSV export; build a companion story.

## Notes
- `lis_member_id` for Collins is `S252`. Data source of record: senate.gov roll-call XML.
- "Importance" is an editorial score, not an official metric — keep that transparent.
- Git repo is already initialized with an initial commit. No remote set yet.
