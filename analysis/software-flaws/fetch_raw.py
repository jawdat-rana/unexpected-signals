"""Download the raw data for "Black October": flaws found vs flaws exploited.

Runs in GitHub Actions (see .github/workflows/flaws-fetch.yml), because most of
these hosts are not reachable from every environment. Writes compact CSVs to
OUT_DIR, which the workflow commits to the `raw-flaws` branch:

- cves.csv: one row per published CVE record in the CVE List (cvelistV5),
  with publish date, who assigned it, vendor, highest CVSS base score,
  first CWE, and whether its credits or description mention an AI tool.
- kev.csv: CISA's Known Exploited Vulnerabilities catalogue, as published.
- msrc.csv: one row per CVE in each of Microsoft's monthly security update
  guides (CVRF), with whether Microsoft marked it as exploited.
- ncsc_nl.csv: NCSC-NL security advisories (CSAF), best effort.
- manifest.csv: what was downloaded, when, and how many rows.

Usage: python analysis/software-flaws/fetch_raw.py OUT_DIR
Needs only the Python standard library, plus `gh` for the CVE List release.
"""

import csv
import io
import json
import re
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HEADERS = {
    "User-Agent": "unexpected-signals research script (github.com/jawdat-rana/unexpected-signals)",
    "Accept": "application/json",
}
KEV_URLS = [
    "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    # CISA's own mirror, used if the website refuses the runner.
    "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json",
]
MSRC = "https://api.msrc.microsoft.com/cvrf/v3.0"
NCSC_META = "https://advisories.ncsc.nl/.well-known/csaf/provider-metadata.json"

# Credits or descriptions that name an AI system as finder. Matched as words,
# case-insensitive. Kept narrow on purpose: "AI" alone matches too much.
AI_TERMS = re.compile(
    r"\b(big sleep|naptime|xbow|aardvark|codemender|claude|anthropic|openai|gpt-?\d|"
    r"gemini|deepmind|llm|large language model|ai[- ]assisted|ai[- ]powered|ai agent|"
    r"ai-driven|artificial intelligence|autonomous (?:agent|system|vulnerability)|"
    r"atlantis|buttercup|trail of bits'? crs|cyber reasoning system|zeropath|"
    r"depthfirst|aisle|vulnhuntr|code intelligence)\b",
    re.I,
)

manifest: list[dict] = []


def log(source: str, status: str, rows: int = 0, note: str = "") -> None:
    manifest.append(
        {
            "source": source,
            "status": status,
            "rows": rows,
            "note": note,
            "fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        }
    )
    print(f"[{source}] {status} rows={rows} {note}", flush=True)


def get(url: str, timeout: int = 120, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - retried, then raised
            if i == tries - 1:
                raise
            print(f"retry {url}: {exc}", flush=True)
            time.sleep(5 * (i + 1))
    raise RuntimeError("unreachable")


def write(path: Path, rows: list[dict], cols: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# --- CVE List -----------------------------------------------------------------

CVSS_KEYS = ("cvssV4_0", "cvssV3_1", "cvssV3_0", "cvssV2_0")


def best_score(container: dict) -> tuple[str, str]:
    """Highest-version CVSS base score in a container, as (score, version)."""
    for key in CVSS_KEYS:
        for m in container.get("metrics", []) or []:
            if key in m and "baseScore" in m[key]:
                return str(m[key]["baseScore"]), key.replace("cvssV", "").replace("_", ".")
    return "", ""


def cve_row(rec: dict) -> dict | None:
    meta = rec.get("cveMetadata", {})
    if meta.get("state") != "PUBLISHED":
        return None
    cna = rec.get("containers", {}).get("cna", {})
    adp = rec.get("containers", {}).get("adp", []) or []
    score, ver = best_score(cna)
    source = "cna" if score else ""
    if not score:
        for a in adp:
            score, ver = best_score(a)
            if score:
                source = a.get("providerMetadata", {}).get("shortName", "adp")
                break
    cwe = ""
    for pt in cna.get("problemTypes", []) or []:
        for d in pt.get("descriptions", []) or []:
            if d.get("cweId"):
                cwe = d["cweId"]
                break
        if cwe:
            break
    vendor = ""
    for a in cna.get("affected", []) or []:
        if a.get("vendor"):
            vendor = a["vendor"]
            break
    credits = " | ".join(c.get("value", "") for c in cna.get("credits", []) or [])
    desc = " ".join(d.get("value", "") for d in cna.get("descriptions", []) or [] if d.get("lang", "en").startswith("en"))
    hit = AI_TERMS.search(credits) or AI_TERMS.search(desc)
    return {
        "cve": meta.get("cveId", ""),
        "published": (meta.get("datePublished") or "")[:10],
        "reserved": (meta.get("dateReserved") or "")[:10],
        "assigner": meta.get("assignerShortName", ""),
        "vendor": vendor[:80],
        "score": score,
        "cvss_version": ver,
        "score_source": source,
        "cwe": cwe,
        "ai_term": hit.group(0).lower() if hit else "",
        "ai_in": ("credits" if AI_TERMS.search(credits) else "description") if hit else "",
        "credits": credits[:200] if hit else "",
    }


CVE_COLS = [
    "cve", "published", "reserved", "assigner", "vendor", "score", "cvss_version",
    "score_source", "cwe", "ai_term", "ai_in", "credits",
]


def fetch_cves(out: Path, tmp: Path) -> None:
    tmp.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["gh", "release", "download", "--repo", "CVEProject/cvelistV5",
         "--pattern", "*_all_CVEs_at_midnight.zip*", "--dir", str(tmp), "--clobber"],
        check=True,
    )
    outer = next(tmp.glob("*all_CVEs_at_midnight*"))
    zf = zipfile.ZipFile(outer)
    names = zf.namelist()
    # The release is a zip holding cves.zip (a zip of the JSON tree).
    if len(names) == 1 and names[0].endswith(".zip"):
        inner_path = tmp / "cves.zip"
        with zf.open(names[0]) as src, inner_path.open("wb") as dst:
            while chunk := src.read(1 << 20):
                dst.write(chunk)
        zf = zipfile.ZipFile(inner_path)
    rows = []
    for name in zf.namelist():
        if not re.search(r"CVE-\d{4}-\d+\.json$", name):
            continue
        try:
            row = cve_row(json.loads(zf.read(name)))
        except Exception as exc:  # noqa: BLE001 - a broken record should not stop the run
            print(f"skip {name}: {exc}")
            continue
        if row:
            rows.append(row)
    rows.sort(key=lambda r: (r["published"], r["cve"]))
    write(out / "cves.csv", rows, CVE_COLS)
    log("cvelistV5", "ok", len(rows), outer.name)


# --- CISA KEV -----------------------------------------------------------------


KEV_COLS = [
    "cveID", "vendorProject", "product", "vulnerabilityName", "dateAdded",
    "dueDate", "knownRansomwareCampaignUse", "cwes",
]


def fetch_kev(out: Path) -> None:
    errors = []
    for url in KEV_URLS:
        try:
            data = json.loads(get(url))
            break
        except Exception as exc:  # noqa: BLE001 - try the mirror
            errors.append(f"{url}: {exc}")
    else:
        raise RuntimeError("; ".join(errors))
    rows = data["vulnerabilities"]
    for r in rows:
        r["cwes"] = " ".join(r.get("cwes") or [])
    write(out / "kev.csv", rows, KEV_COLS)
    log("cisa-kev", "ok", len(rows), f"{url} (catalog {data.get('catalogVersion', '')})")


# --- Microsoft security update guide (CVRF) -----------------------------------

MSRC_COLS = ["doc", "release", "cve", "title", "cna", "exploited", "publicly_disclosed", "score", "tags"]


def msrc_rows(doc_id: str, doc: dict) -> list[dict]:
    rows = []
    release = (doc.get("DocumentTracking", {}).get("InitialReleaseDate") or "")[:10]
    for v in doc.get("Vulnerability", []) or []:
        exploited = disclosed = ""
        for t in v.get("Threats", []) or []:
            desc = (t.get("Description", {}) or {}).get("Value", "") or ""
            m = re.search(r"Exploited:(\w+)", desc)
            if m and not exploited:
                exploited = m.group(1)
            m = re.search(r"Publicly Disclosed:(\w+)", desc)
            if m and not disclosed:
                disclosed = m.group(1)
        scores = [s.get("BaseScore") for s in v.get("CVSSScoreSets", []) or [] if s.get("BaseScore") is not None]
        tags, cna = [], ""
        for n in v.get("Notes", []) or []:
            if n.get("Type") == 7 and n.get("Title") == "Tag":
                tags.append(n.get("Value", ""))
            if n.get("Title") in ("Assigning CNA", "CNA"):
                cna = n.get("Value", "")
        rows.append(
            {
                "doc": doc_id,
                "release": release,
                "cve": v.get("CVE", ""),
                "title": ((v.get("Title") or {}).get("Value") or "")[:150],
                "cna": cna,
                "exploited": exploited,
                "publicly_disclosed": disclosed,
                "score": max(scores) if scores else "",
                "tags": "; ".join(sorted(set(tags)))[:150],
            }
        )
    return rows


def fetch_msrc(out: Path) -> None:
    index = json.loads(get(f"{MSRC}/updates"))
    docs = sorted({u["ID"] for u in index.get("value", [])})
    rows, failed = [], []
    for doc_id in docs:
        try:
            rows += msrc_rows(doc_id, json.loads(get(f"{MSRC}/cvrf/{doc_id}", timeout=300)))
        except Exception as exc:  # noqa: BLE001
            failed.append(doc_id)
            print(f"msrc {doc_id}: {exc}")
    write(out / "msrc.csv", rows, MSRC_COLS)
    log("msrc-cvrf", "ok" if not failed else "partial", len(rows),
        f"{len(docs)} monthly guides" + (f"; failed {','.join(failed)}" if failed else ""))


# --- NCSC-NL advisories (CSAF) ------------------------------------------------

NCSC_COLS = ["id", "released", "title", "probability", "damage", "cves"]


def fetch_ncsc(out: Path) -> None:
    meta = json.loads(get(NCSC_META))
    base = None
    for d in meta.get("distributions", []) or []:
        base = d.get("directory_url") or base
    if not base:
        raise RuntimeError("no directory_url in provider metadata")
    base = base.rstrip("/")
    changes = get(f"{base}/changes.csv").decode("utf-8")
    paths = sorted({row[0] for row in csv.reader(io.StringIO(changes)) if row})
    rows = []
    for p in paths:
        try:
            doc = json.loads(get(f"{base}/{p}", timeout=60, tries=2))
        except Exception as exc:  # noqa: BLE001
            print(f"ncsc {p}: {exc}")
            continue
        d = doc.get("document", {})
        tr = d.get("tracking", {})
        notes = " ".join(n.get("text", "") for n in d.get("notes", []) or [])
        prob = re.search(r"(?:Kans|Probability)[^\n:]*:\s*(\w+)", notes, re.I)
        dmg = re.search(r"(?:Schade|Damage)[^\n:]*:\s*(\w+)", notes, re.I)
        cves = sorted({v.get("cve") for v in doc.get("vulnerabilities", []) or [] if v.get("cve")})
        rows.append(
            {
                "id": tr.get("id", p),
                "released": (tr.get("initial_release_date") or "")[:10],
                "title": (d.get("title") or "")[:150],
                "probability": prob.group(1) if prob else "",
                "damage": dmg.group(1) if dmg else "",
                "cves": " ".join(cves)[:2000],
            }
        )
    write(out / "ncsc_nl.csv", rows, NCSC_COLS)
    log("ncsc-nl-csaf", "ok", len(rows), base)


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[2:])  # optional: run only some sources, e.g. "kev msrc"
    steps = [
        ("kev", lambda: fetch_kev(out)),
        ("msrc", lambda: fetch_msrc(out)),
        ("ncsc", lambda: fetch_ncsc(out)),
        ("cves", lambda: fetch_cves(out, out / "_tmp")),
    ]
    for name, fn in steps:
        if only and name not in only:
            continue
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - keep other sources
            log(name, "failed", 0, str(exc)[:200])
    path = out / "manifest.csv"
    write(path, manifest, ["source", "status", "rows", "note", "fetched_utc"])


if __name__ == "__main__":
    main()
