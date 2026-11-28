"""Turn the UN's bulk voting data into the tables for the UN votes stories.

    python analysis/un-votes/prepare.py RAW_DIR

RAW_DIR is a checkout of the `raw-un-votes` branch (see fetch_raw.py). It holds
the Dag Hammarskjöld Library's General Assembly votes (one row per country per
recorded vote), General Assembly outcomes (every resolution, with how it was
adopted) and Security Council votes.

Definitions:

- A session runs from September to September; session 80 is Sep 2025 to Sep
  2026. Only regular sessions are counted in the per-session tables;
  emergency and special sessions are left out, so sessions compare like for like.
- "Recorded vote": every country's vote is on the record. The alternatives are
  "without a vote" (adopted by consensus) and a non-recorded vote (show of hands).
- Agreement between two countries: the share of recorded votes, among those both
  took part in (yes, no or abstain), where they voted the same way. Absences
  ("non-voting") are left out.
- A forced vote: a resolution in session 80 that went to a recorded vote while
  every earlier resolution with the same title had passed without a vote.
- A lone no: a recorded vote where exactly one country voted no.
"""

from __future__ import annotations

import csv
import gzip
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORY_A = ROOT / "stories" / "the-year-the-un-stopped-agreeing" / "data"
STORY_B = ROOT / "stories" / "alone-against-the-world" / "data"
FIRST_SESSION = 45  # 1990, after the Cold War
LAST_SESSION = 80
# Countries to follow in the agreement-with-the-US trend.
FOLLOW = ["FSM", "MHL", "PLW", "ISR", "ARG", "HUN", "GBR", "NLD"]
SHORT = {
    "FSM": "Micronesia",
    "MHL": "Marshall Islands",
    "PLW": "Palau",
    "ISR": "Israel",
    "ARG": "Argentina",
    "HUN": "Hungary",
    "GBR": "United Kingdom",
    "NLD": "Netherlands",
    "PRY": "Paraguay",
    "USA": "United States",
}
VOTED = {"Y", "N", "A"}


def norm_title(title: str) -> str:
    """Resolution title without the ': resolution / adopted by ...' tail."""
    title = re.sub(r"\s*:\s*resolution\s*/.*$", "", title.strip(), flags=re.I)
    return re.sub(r"\s+", " ", title).strip().rstrip(".").lower()


def nice_name(name: str) -> str:
    fixes = {
        "MICRONESIA (FEDERATED STATES OF)": "Micronesia",
        "IRAN (ISLAMIC REPUBLIC OF)": "Iran",
        "DEMOCRATIC PEOPLE'S REPUBLIC OF KOREA": "North Korea",
        "RUSSIAN FEDERATION": "Russia",
        "SYRIAN ARAB REPUBLIC": "Syria",
        "UNITED STATES": "United States",
        "UNITED KINGDOM": "United Kingdom",
        "TÜRKİYE": "Türkiye",
        "TURKEY": "Türkiye",
        "NAOERO": "Nauru",
        "NETHERLANDS (KINGDOM OF THE)": "Netherlands",
    }
    if name in fixes:
        return fixes[name]
    return name.title().replace(" And ", " and ").replace(" Of ", " of ").replace(" The ", " the ")


def session_of(value: str) -> int | None:
    return int(value) if value.isdigit() else None


def load(raw: Path):
    dl = raw / "dl"
    outcomes_path = sorted(dl.glob("*_outcomes_ga.csv.gz"))[-1]
    votes_path = sorted(dl.glob("*_votes_ga.csv.gz"))[-1]
    sc_path = sorted(dl.glob("*_sc_votes.csv.gz"))[-1]
    with gzip.open(outcomes_path, "rt", encoding="utf-8") as fh:
        outcomes = list(csv.DictReader(fh))
    votes: dict[str, dict[str, str]] = defaultdict(dict)
    meta: dict[str, dict] = {}
    names: dict[str, str] = {}
    with gzip.open(votes_path, "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            votes[r["undl_id"]][r["ms_code"]] = r["ms_vote"]
            names[r["ms_code"]] = r["ms_name"]  # latest name wins (file runs oldest first)
            if r["undl_id"] not in meta:
                meta[r["undl_id"]] = {
                    "date": r["date"],
                    "session": session_of(r["session"]),
                    "resolution": r["resolution"],
                    "title": norm_title(r["title"]),
                }
    with gzip.open(sc_path, "rt", encoding="utf-8") as fh:
        sc = list(csv.DictReader(fh))
    print(
        f"{outcomes_path.name}: {len(outcomes)} outcomes; "
        f"{votes_path.name}: {len(votes)} recorded votes; "
        f"{sc_path.name}: {len(sc)} rows"
    )
    return outcomes, votes, meta, names, sc


def agreement(votes, ids, a: str, b: str) -> tuple[float | None, int]:
    same = n = 0
    for i in ids:
        va, vb = votes[i].get(a), votes[i].get(b)
        if va in VOTED and vb in VOTED:
            n += 1
            same += va == vb
    return (round(100 * same / n, 1) if n else None), n


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path.relative_to(ROOT)} ({len(rows)} rows)")


def story_a(outcomes, votes, meta, names) -> None:
    print("The year the UN stopped agreeing")
    by_session = defaultdict(list)
    for i, m in meta.items():
        if m["session"]:
            by_session[m["session"]].append(i)

    # 1. How each session's resolutions were adopted.
    count = defaultdict(Counter)
    for r in outcomes:
        s = session_of(r["session"])
        if s:
            count[s][r["modality"]] += 1
    rows = []
    for s in range(FIRST_SESSION, LAST_SESSION + 1):
        c = count[s]
        total = sum(c.values())
        us = Counter(votes[i].get("USA") for i in by_session[s])
        rows.append(
            {
                "session": s,
                "start_year": 1945 + s,
                "label": f"{1945 + s}–{str(1946 + s)[2:]}",
                "resolutions": total,
                "recorded": c["Vote, recorded"],
                "without_vote": c["Without a vote"],
                "non_recorded": c["Vote, non-recorded"],
                "recorded_share": round(100 * c["Vote, recorded"] / total, 1),
                "us_no": us["N"],
                "us_yes": us["Y"],
                "us_abstain": us["A"],
            }
        )
    write(STORY_A / "sessions.csv", rows)
    last, before = rows[-1], rows[-2]
    print(
        f"  session 80: {last['recorded']} of {last['resolutions']} recorded "
        f"({last['recorded_share']}%), "
        f"US no {last['us_no']}; session 79: {before['recorded']} ({before['recorded_share']}%)"
    )

    # 2. Forced votes: session 80 recorded votes on titles that had only ever passed without a vote.
    history = defaultdict(set)
    for r in outcomes:
        s = session_of(r["session"])
        if s and s < LAST_SESSION:
            history[norm_title(r["title"])].add(r["modality"])
    by_res = {m["resolution"]: i for i, m in meta.items()}
    forced = []
    for r in outcomes:
        if session_of(r["session"]) != LAST_SESSION or r["modality"] != "Vote, recorded":
            continue
        title = norm_title(r["title"])
        if history.get(title) != {"Without a vote"}:
            continue
        i = by_res.get(r["resolution"])
        no = sorted(nice_name(names[c]) for c, v in votes[i].items() if v == "N") if i else []
        forced.append(
            {
                "date": r["date"],
                "resolution": r["resolution"],
                "title": title[:1].upper() + title[1:],
                "earlier_without_vote": sum(
                    1
                    for o in outcomes
                    if norm_title(o["title"]) == title
                    and session_of(o["session"])
                    and session_of(o["session"]) < LAST_SESSION
                ),
                "yes": int(float(r["total_yes"] or 0)),
                "no": int(float(r["total_no"] or 0)),
                "abstain": int(float(r["total_abstentions"] or 0)),
                "voted_no": "; ".join(no),
            }
        )
    forced.sort(key=lambda d: (-d["yes"] + d["no"], d["date"]))
    write(STORY_A / "forced_votes.csv", forced)
    us_alone = sum(1 for f in forced if f["voted_no"] == "United States")
    with_us = sum(1 for f in forced if "United States" in f["voted_no"])
    print(f"  forced votes: {len(forced)}; US voted no on {with_us}, alone on {us_alone}")

    # 3. Agreement with the US, sessions 79 and 80, every member.
    s79, s80 = by_session[LAST_SESSION - 1], by_session[LAST_SESSION]
    shift = []
    for c in sorted({c for i in s80 for c in votes[i]} - {"USA"}):
        a79, n79 = agreement(votes, s79, "USA", c)
        a80, n80 = agreement(votes, s80, "USA", c)
        if a79 is None or a80 is None or n79 < 40 or n80 < 40:
            continue
        shift.append(
            {
                "code": c,
                "country": nice_name(names[c]),
                "agree_79": a79,
                "agree_80": a80,
                "votes_79": n79,
                "votes_80": n80,
                "change": round(a80 - a79, 1),
            }
        )
    shift.sort(key=lambda d: -d["agree_80"])
    write(STORY_A / "us_agreement_shift.csv", shift)
    median = lambda xs: sorted(xs)[len(xs) // 2]  # noqa: E731
    print(
        f"  median agreement with US: 79 {median([d['agree_79'] for d in shift])}, "
        f"80 {median([d['agree_80'] for d in shift])}"
    )
    print("  top 80:", [(d["country"], d["agree_80"]) for d in shift[:6]])

    # 4. Agreement with the US per session for the followed countries.
    trend = []
    for s in range(FIRST_SESSION + 25, LAST_SESSION + 1):  # 2015 on
        for c in FOLLOW:
            a, n = agreement(votes, by_session[s], "USA", c)
            if a is not None:
                trend.append(
                    {
                        "session": s,
                        "start_year": 1945 + s,
                        "code": c,
                        "country": SHORT[c],
                        "agree": a,
                        "votes": n,
                    }
                )
    write(STORY_A / "us_agreement_trend.csv", trend)

    # 5. Who voted no with the US in session 80.
    us_no = [i for i in s80 if votes[i].get("USA") == "N"]
    partners = Counter(c for i in us_no for c, v in votes[i].items() if v == "N" and c != "USA")
    alone = sum(1 for i in us_no if sum(v == "N" for v in votes[i].values()) == 1)
    rows = [
        {
            "code": c,
            "country": nice_name(names[c]),
            "no_with_us": n,
            "us_no": len(us_no),
            "share": round(100 * n / len(us_no), 1),
        }
        for c, n in partners.most_common(12)
    ]
    rows.append(
        {
            "code": "-",
            "country": "Nobody (the US alone)",
            "no_with_us": alone,
            "us_no": len(us_no),
            "share": round(100 * alone / len(us_no), 1),
        }
    )
    write(STORY_A / "no_with_us.csv", rows)
    print("  no with US:", [(r["country"], r["no_with_us"]) for r in rows[:5]], "alone", alone)


def story_b(votes, meta, names, sc) -> None:
    print("Alone against the world")
    lone = defaultdict(list)
    for i, vs in votes.items():
        no = [c for c, v in vs.items() if v == "N"]
        if len(no) == 1:
            lone[no[0]].append(i)

    # 1. Each country's lone no's and the resolution it most often stands alone against.
    rows = []
    for c, ids in lone.items():
        titles = Counter(meta[i]["title"] for i in ids)
        top, n_top = titles.most_common(1)[0]
        years = sorted(meta[i]["date"][:4] for i in ids)
        top_years = sorted(meta[i]["date"][:4] for i in ids if meta[i]["title"] == top)
        rows.append(
            {
                "code": c,
                "country": nice_name(names[c]),
                "lone_no": len(ids),
                "first": years[0],
                "last": years[-1],
                "top_title": top[:1].upper() + top[1:],
                "top_count": n_top,
                "top_first": top_years[0],
                "top_last": top_years[-1],
                "since_2000": sum(1 for y in years if y >= "2000"),
            }
        )
    rows.sort(key=lambda d: -d["lone_no"])
    write(STORY_B / "lone_no.csv", rows)
    print("  countries ever alone:", len(rows))
    for r in rows[:12]:
        print(
            f"   {r['country']:15} {r['lone_no']:4}  {r['top_count']:3}x {r['top_title'][:60]} "
            f"({r['top_first']}–{r['top_last']})"
        )

    # 2. Every recorded vote on three resolutions, with the lone country's vote.
    lonely = []

    def series(pattern: str, code: str, case: str) -> None:
        out = []
        for i, m in sorted(meta.items(), key=lambda kv: kv[1]["date"]):
            if not re.search(pattern, m["title"]):
                continue
            vs = votes[i]
            tally = Counter(vs.values())
            out.append(
                {
                    "case": case,
                    "country": nice_name(names[code]),
                    "date": m["date"],
                    "year": int(m["date"][:4]),
                    "resolution": m["resolution"],
                    "vote": {"Y": "yes", "N": "no", "A": "abstain", "X": "absent"}.get(
                        vs.get(code), ""
                    ),
                    "yes": tally["Y"],
                    "no": tally["N"],
                    "abstain": tally["A"],
                    "alone": int(vs.get(code) == "N" and tally["N"] == 1),
                }
            )
        lonely.extend(out)
        print(
            f"  {case}: {len(out)} votes, {code} no {sum(r['vote'] == 'no' for r in out)}, "
            f"alone {sum(r['alone'] for r in out)}, {out[0]['year']}–{out[-1]['year']}"
        )

    series(r"^(oceans and (the )?law of the sea|law of the sea)$", "TUR", "Law of the Sea")
    series(
        r"^conventional arms control at the regional and subregional levels$",
        "IND",
        "Regional arms control",
    )
    series(r"^question of the comorian island of mayotte$", "FRA", "Mayotte")
    write(STORY_B / "lonely_votes.csv", lonely)

    # 3. Security Council votes on India and Pakistan (Kashmir), by year.
    pat = re.compile(r"kashmir|jammu|india.pakistan|india and pakistan", re.I)
    seen = {}
    for r in sc:
        if pat.search(" ".join([r["description"], r["agenda"], r["subjects"]])):
            seen[r["resolution"]] = {
                "date": r["date"],
                "resolution": r["resolution"],
                "description": re.sub(
                    r"^Security Council resolution [^\[]*\[|\]$", "", r["description"]
                ),
            }
    kashmir = sorted(seen.values(), key=lambda d: d["date"])
    write(STORY_B / "kashmir_security_council.csv", kashmir)
    print(
        f"  Security Council on India-Pakistan: {len(kashmir)} resolutions, "
        f"last {kashmir[-1]['date']}"
    )


def main(raw: Path) -> None:
    outcomes, votes, meta, names, sc = load(raw)
    story_a(outcomes, votes, meta, names)
    story_b(votes, meta, names, sc)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "raw"))
