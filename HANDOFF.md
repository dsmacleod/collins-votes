# Collins Vote Tracker — How it works and how to finish it

A reader tool that lists Susan Collins' Senate votes and ranks them by importance —
where **the reader decides what "important" means** by moving four sliders.

## What you have

1. **`collins-votes-tool.html`** — the finished reader-facing tool. Open it in any
   browser. It's one self-contained file (no plugins, no server), so it drops into
   the CMS as-is. Right now it's loaded with a **demo sample** of 12 landmark votes.

2. **`scrape_collins_votes.py`** — the script that turns the demo into the real thing:
   it downloads *every* vote Collins has cast since 1997 from the Senate's official
   record and scores them.

3. **This doc.**

## The idea, in plain terms

"Importance" isn't something the government records — it's an editorial call. So
instead of us deciding for readers, the tool scores every vote on four factors and
lets the reader weight them:

- **How close the vote was** — a 51–49 vote outranks a 90–5 one. (From the tally.)
- **How decisive she was** — how few senators would've had to flip to change the
  result. (From the tally.)
- **Breaking with her party** — did she vote against most Senate Republicans? This is
  Collins' whole brand, and it's the factor that surfaces her most newsworthy moments.
  (Computed automatically.)
- **Topic salience** — a Supreme Court confirmation weighs more than a procedural
  motion. (This is the one human-judgment factor — see below.)

The scoring formula is simple and transparent (a weighted average), shown in the
footer so readers — and rival reporters — can see there's no black box.

## To populate the full career (the only step that needs a developer)

The script can't run in this chat (no open internet here), but it runs fine on any
machine with Python. Hand these three lines to whoever maintains the website:

```
pip install requests
python3 scrape_collins_votes.py
```

It writes **`collins_votes.json`** (and a `.csv` if you'd rather eyeball it in Excel).
Expect a few thousand votes; the run takes a while because it politely downloads one
file at a time and caches them, so a second run is instant.

Then **just drop `collins_votes.json` in the same folder as `collins-votes-tool.html`**
(and commit/push it). The page now loads that file automatically on open — no code edit
needed. If the file isn't there, the page falls back to the built-in demo votes, so it
never breaks. Future refreshes are simply: re-run the script, replace the JSON, push.

Two things the page does automatically once the real data is in:
- **Caps the visible list to the top 200** by importance so 9,000 rows stay fast. A
  "Show all rows" checkbox lifts the cap; the count line tells readers what's hidden.
- **Hides procedural votes** (cloture, motions to proceed/table, etc.) by default, since
  they're most of the record by count but rarely the real decision. A "Hide procedural
  votes" checkbox toggles them. The scraper tags each vote with this flag.

## The one editorial decision to make

**Topic salience** is the only number a human sets. In the script, near the top,
there's a plain list called `TOPIC_RULES` — keywords mapped to a topic name and a
0–100 weight (e.g. "supreme court" → 100, "appropriation" → 70). Tune those numbers
to match how the newsroom weighs issues. Everything else is computed from the record.

This is also the honest caveat to put in the published piece: closeness, decisiveness
and party breaks are facts from the tally; topic weighting is our editorial judgment,
which is exactly why readers can dial it up or down (or to zero).

## Accuracy notes

- The three votes marked **✓ verified** in the demo were pulled live from senate.gov
  during the build (Kavanaugh 50–48, ACA "skinny repeal" 49–51, Laken Riley cloture
  84–9). The other demo rows are illustrative — **verify before publishing**, or just
  run the scraper, which pulls everything authoritatively.
- Source of record: U.S. Senate roll-call votes, senate.gov.
- The scraper skips votes Collins missed or voted "present," and counts a "party break"
  as voting opposite the Republican majority on that vote.

## Story angles this tool sets up

- Her most pivotal votes (max the "decisive" slider).
- Every time she broke with the GOP, by topic and by year.
- How her independence has changed over a 25-year career (sort by date).
- A reader-interactive sidebar to any Collins profile or election piece.
