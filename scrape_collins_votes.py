#!/usr/bin/env python3
"""
scrape_collins_votes.py
-----------------------
Pulls EVERY Senate roll-call vote Susan Collins has cast (1997-present) straight
from the U.S. Senate's official record (senate.gov), scores each vote on four
transparent factors, and writes a JSON file that drops directly into
collins-votes-tool.html.

Susan Collins' Senate ID (lis_member_id) is S252.
She took office in the 105th Congress (1997).

USAGE
  pip install requests
  python3 scrape_collins_votes.py

OUTPUT
  collins_votes.json   (full dataset)
  collins_votes.csv    (same data, spreadsheet-friendly)

Then open collins-votes-tool.html, find the line  `const VOTES = [ ... ];`
and replace the seed array with the contents of collins_votes.json.
(Or wire the HTML to fetch the JSON file — see the handoff doc.)

Be polite: this hits senate.gov a few thousand times. The script sleeps between
requests and caches everything locally so you only download each file once.
"""

import csv
import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

COLLINS_ID = "S252"
FIRST_CONGRESS = 105          # 1997 — Collins' first
LAST_CONGRESS = 119           # update as needed
CACHE_DIR = "senate_cache"
SLEEP = 0.4                   # seconds between requests; be a good citizen
HEADERS = {"User-Agent": "BDN newsroom research (contact: newsroom@bangordailynews.com)"}

# Keyword -> topic + salience (0-100). This is the one judgment-based factor.
# Edit these to match how your newsroom weights issues.
TOPIC_RULES = [
    (("supreme court", "associate justice", "chief justice"), "Supreme Court", 100),
    (("impeach",), "Impeachment", 100),
    (("affordable care", "health care", "obamacare", "medicaid", "medicare"), "Health care", 95),
    (("abortion", "reproductive", "contraception", "planned parenthood"), "Reproductive rights", 95),
    (("tax",), "Taxes", 85),
    (("immigration", "border", "alien", "asylum"), "Immigration", 80),
    (("climate", "emission", "energy", "environmental"), "Climate / Energy", 80),
    (("marriage", "civil rights", "voting rights", "discrimination"), "Civil rights", 85),
    (("gun", "firearm", "second amendment"), "Guns", 85),
    (("circuit", "district judge", "nomination"), "Nominations", 60),
    (("appropriation", "budget", "debt limit", "shutdown", "spending"), "Budget / Spending", 70),
    (("defense", "military", "ukraine", "israel", "war", "ndaa"), "Defense / Foreign policy", 75),
]
DEFAULT_TOPIC = ("Other", 40)


def topic_for(text):
    t = (text or "").lower()
    for keys, name, sal in TOPIC_RULES:
        if any(k in t for k in keys):
            return name, sal
    return DEFAULT_TOPIC


def fetch(url, cache_name):
    """Download with on-disk caching so re-runs are instant and polite."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, cache_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    r = requests.get(url, headers=HEADERS, timeout=30)
    time.sleep(SLEEP)
    if r.status_code != 200:
        return None
    with open(path, "w", encoding="utf-8") as f:
        f.write(r.text)
    return r.text


def vote_numbers(congress, session):
    """Read a session's vote menu to learn how many roll-call votes happened."""
    url = (f"https://www.senate.gov/legislative/LIS/roll_call_lists/"
           f"vote_menu_{congress}_{session}.xml")
    xml = fetch(url, f"menu_{congress}_{session}.xml")
    if not xml:
        return []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    nums = [int(v.findtext("vote_number")) for v in root.iter("vote") if v.findtext("vote_number")]
    return sorted(set(nums))


def parse_vote(congress, session, num):
    """Return a scored record for one vote, or None if Collins didn't participate."""
    url = (f"https://www.senate.gov/legislative/LIS/roll_call_votes/"
           f"vote{congress}{session}/vote_{congress}_{session}_{num:05d}.xml")
    xml = fetch(url, f"vote_{congress}_{session}_{num:05d}.xml")
    if not xml:
        return None
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None

    yeas = int(root.findtext("count/yeas") or 0)
    nays = int(root.findtext("count/nays") or 0)
    question = root.findtext("vote_question_text") or ""
    title = root.findtext("vote_title") or root.findtext("vote_document_text") or question
    date_raw = (root.findtext("vote_date") or "").split(",")
    try:
        d = datetime.strptime(date_raw[0].strip() + " " + date_raw[1].strip(), "%B %d %Y")
        date = d.strftime("%Y-%m-%d")
    except (ValueError, IndexError):
        date = ""
    bill = root.findtext("document/document_name") or root.findtext("amendment/amendment_number") or ""

    collins_vote, r_yea, r_nay = None, 0, 0
    for m in root.iter("member"):
        cast = (m.findtext("vote_cast") or "").strip()
        party = (m.findtext("party") or "").strip()
        if m.findtext("lis_member_id") == COLLINS_ID:
            collins_vote = "Yea" if cast.startswith("Yea") else "Nay" if cast.startswith("Nay") else cast
        if party == "R":
            if cast.startswith("Yea"):
                r_yea += 1
            elif cast.startswith("Nay"):
                r_nay += 1

    if collins_vote not in ("Yea", "Nay"):
        return None  # skip votes she missed / "present"

    # party break: did she vote opposite the GOP majority?
    gop_majority = "Yea" if r_yea >= r_nay else "Nay"
    party_break = (collins_vote != gop_majority)

    topic, salience = topic_for(title + " " + question)

    return {
        "title": title.strip(),
        "meta": (bill + " — " if bill else "") + question.strip(),
        "topic": topic,
        "date": date,
        "yea": yeas,
        "nay": nays,
        "position": collins_vote,
        "partyBreak": party_break,
        "salience": salience,
        "verified": True,
        "congress": congress,
        "session": session,
        "vote_number": num,
    }


def main():
    records = []
    for congress in range(FIRST_CONGRESS, LAST_CONGRESS + 1):
        for session in (1, 2):
            nums = vote_numbers(congress, session)
            if not nums:
                continue
            print(f"Congress {congress}, session {session}: {len(nums)} votes")
            for n in nums:
                rec = parse_vote(congress, session, n)
                if rec:
                    records.append(rec)

    records.sort(key=lambda r: r["date"])
    print(f"\nTotal Collins votes captured: {len(records)}")

    with open("collins_votes.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    with open("collins_votes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        w.writeheader()
        w.writerows(records)

    print("Wrote collins_votes.json and collins_votes.csv")


if __name__ == "__main__":
    main()
