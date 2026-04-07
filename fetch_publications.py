#!/usr/bin/env python3
"""Fetch publications from ORCID and write publications content."""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError

ORCID_ID = "0000-0003-1623-1949"
API_BASE = f"https://pub.orcid.org/v3.0/{ORCID_ID}"
HEADERS = {"Accept": "application/json"}

# Content-only file (no frontmatter) — included in both index.qmd and publications.qmd
CONTENT_PATH = "_pubs_content.qmd"


def fetch_json(url: str) -> dict:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def get_works() -> list[dict]:
    data = fetch_json(f"{API_BASE}/works")
    summaries = []
    for group in data.get("group", []):
        work_summaries = group.get("work-summary", [])
        if not work_summaries:
            continue
        # Take the first (preferred) summary in the group
        w = work_summaries[0]
        title = (
            w.get("title", {}).get("title", {}).get("value", "Untitled")
        )
        year = (
            w.get("publication-date", {}) or {}
        ).get("year", {})
        year_value = (year or {}).get("value", "")
        journal = (
            w.get("journal-title", {}) or {}
        ).get("value", "")
        doi = None
        for eid in w.get("external-ids", {}).get("external-id", []):
            if eid.get("external-id-type") == "doi":
                doi = eid.get("external-id-value")
                break
        summaries.append(
            {"title": title, "year": year_value, "journal": journal, "doi": doi}
        )
    # Sort newest first
    summaries.sort(key=lambda x: x["year"] or "0", reverse=True)
    return summaries


def build_content(works: list[dict]) -> str:
    lines = ["<!-- publications start -->"]

    if not works:
        lines.append("\n*No publications found.*\n")
    else:
        for w in works:
            title = w["title"]
            year = w["year"]
            journal = w["journal"]
            doi = w["doi"]

            if doi:
                title_str = f"[{title}](https://doi.org/{doi})"
            else:
                title_str = title

            meta_parts = []
            if journal:
                meta_parts.append(f"*{journal}*")
            if year:
                meta_parts.append(year)
            meta_str = " · ".join(meta_parts)

            lines.append("::: {.pub-item}")
            lines.append(f"**{title_str}**")
            if meta_str:
                lines.append(f"<br>{meta_str}")
            lines.append(":::")
            lines.append("")

    lines.append("<!-- publications end -->")
    return "\n".join(lines) + "\n"


def main():
    print(f"Fetching publications for ORCID {ORCID_ID}…")
    try:
        works = get_works()
    except URLError as exc:
        print(f"Error fetching ORCID data: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(works)} works.")
    content = build_content(works)
    with open(CONTENT_PATH, "w") as f:
        f.write(content)
    print(f"Written {CONTENT_PATH}")


if __name__ == "__main__":
    main()
