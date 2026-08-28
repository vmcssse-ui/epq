#!/usr/bin/env python3
"""
build_weekly.py — manifest JSON -> one self-contained weekly page.

    python3 build_weekly.py manifests/epq/epq-2026-27.json site/index.html

The template carries the design and the behaviour; the manifest carries every
word, date, link and colour. Four tokens are replaced:

    %%TITLE%%        meta.title
    %%DESCRIPTION%%  meta.description
    %%FONTS%%        meta.fonts  (a Google Fonts css2 URL)
    %%NOINDEX%%      a robots meta tag when meta.noindex is true
    %%MANIFEST%%     the whole manifest, inlined as a JS object literal

NOTE: build() here and buildWeekly() in builder.js are twin ports.
Change one, change the other, then run sync_template.py.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.weekly.html")

REQUIRED = ["meta", "calendar", "tracks", "weeks"]


def validate(m):
    """Fail loudly and specifically rather than shipping a broken page."""
    problems = []
    for k in REQUIRED:
        if k not in m:
            problems.append("missing top-level key: %s" % k)
    if problems:
        return problems

    weeks = m["calendar"].get("weeks") or []
    if not weeks:
        problems.append("calendar.weeks is empty — a page needs at least one week")
    for i, d in enumerate(weeks, 1):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(d)):
            problems.append("calendar.weeks[%d] is not YYYY-MM-DD: %r" % (i, d))

    n = len(weeks)
    for t in m["calendar"].get("terms") or []:
        if not (1 <= t.get("from", 0) <= t.get("to", 0) <= n):
            problems.append("term %r spans outside 1..%d" % (t.get("t"), n))

    keys = [t.get("key") for t in m["tracks"]]
    if len(set(keys)) != len(keys):
        problems.append("duplicate track keys: %r" % keys)
    for k in keys:
        if not re.match(r"^[a-z0-9]+$", str(k)):
            problems.append("track key %r must be lowercase letters/digits (it goes in the URL hash)" % k)
        if k not in m["weeks"]:
            problems.append("track %r has no entry in weeks" % k)

    res = m.get("resources") or {}
    for track, wk in m["weeks"].items():
        for num, d in wk.items():
            where = "%s week %s" % (track, num)
            if int(num) > n:
                problems.append("%s is beyond calendar.weeks (%d)" % (where, n))
            for field in ("wl", "cl", "r"):
                for rid in d.get(field) or []:
                    if rid not in res:
                        problems.append("%s: %s references unknown resource %r" % (where, field, rid))
            for slot in ("video", "podcast"):
                o = d.get(slot)
                if o and not o.get("url"):
                    problems.append("%s: %s has no url" % (where, slot))

    for shelf in (m.get("library") or {}).get("shelves") or []:
        for rid in shelf[1]:
            if rid not in res:
                problems.append("library shelf %r references unknown resource %r" % (shelf[0], rid))
    return problems


def build(manifest, template):
    """Manifest dict + template string -> finished HTML string."""
    meta = manifest["meta"]
    noindex = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""

    # json.dumps is safe to inline as long as nothing can close the script
    # element early or start an HTML comment inside it.
    blob = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))
    blob = blob.replace("</", "<\\/").replace("<!--", "<\\!--")

    out = template
    for token, value in (
        ("%%TITLE%%", meta.get("title", "Weekly page")),
        ("%%DESCRIPTION%%", meta.get("description", "")),
        ("%%FONTS%%", meta.get("fonts", "")),
        ("%%NOINDEX%%", noindex),
        ("%%MANIFEST%%", blob),
    ):
        out = out.replace(token, value)

    left = re.findall(r"%%[A-Z_]+%%", out)
    if left:
        raise SystemExit("unfilled tokens remain: %s" % ", ".join(sorted(set(left))))
    return out


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__.strip())
    src = argv[1]
    dest = argv[2] if len(argv) > 2 else os.path.join(HERE, "site", "index.html")

    with open(src, encoding="utf-8") as fh:
        manifest = json.load(fh)
    problems = validate(manifest)
    if problems:
        for p in problems:
            sys.stderr.write("  ! %s\n" % p)
        raise SystemExit("%d problem(s) in %s — nothing written" % (len(problems), src))

    with open(TEMPLATE, encoding="utf-8") as fh:
        template = fh.read()

    html = build(manifest, template)
    os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(html)

    weeks = sum(len(w) for w in manifest["weeks"].values())
    print("built %s  (%d tracks, %d week entries, %d resources, %.0f KB)" % (
        dest, len(manifest["tracks"]), weeks,
        len(manifest.get("resources") or {}), len(html) / 1024.0))


if __name__ == "__main__":
    main(sys.argv)
