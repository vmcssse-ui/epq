#!/usr/bin/env python3
# © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework, Weekly Page Kit (KS4 edition). All rights reserved. Harlington School deployment licensed for internal use. Not for reproduction or redistribution without written permission.
"""
roundtrip.py [page.html ...]

For each source page: extract -> build -> compare with the original.

Two comparisons are made and both are reported:
  * byte  : sha256 of the rebuilt file against the source (nice to have)
  * DOM   : same tag tree, same attributes (order ignored), same text after
            whitespace normalisation, comments ignored (the requirement)

Exit status is non-zero if any page fails the DOM comparison.  Run this after
every edit to template.ks4weekly.html, extract_ks4.py or build_ks4.py.

With no arguments the three Year 11 pages in sources/ (copies of the live pages) are checked and the
manifests in manifests/ are refreshed from them.
"""
import hashlib
import json
import os
import re
import sys

from bs4 import BeautifulSoup, Comment, NavigableString

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ks4  # noqa: E402
import extract_ks4  # noqa: E402

DEFAULT = [os.path.join(HERE, "sources", "year11-%s.html" % t) for t in ("supported", "summit", "sumhclass")]
SCRATCH = os.environ.get("KS4_SCRATCH", os.path.join(HERE, "_roundtrip"))


def norm_text(s):
    return re.sub(r"\s+", " ", s).strip()


def flatten(node, path, out):
    """Depth-first list of (path, kind, payload) tuples for comparison."""
    if isinstance(node, Comment):
        return
    if isinstance(node, NavigableString):
        t = norm_text(str(node))
        if t:
            out.append((path, "text", t))
        return
    attrs = {}
    for k, v in node.attrs.items():
        if isinstance(v, list):
            v = " ".join(v)
        attrs[k] = norm_text(v) if k != "class" else " ".join(sorted(v.split()))
    out.append((path, "tag", (node.name, tuple(sorted(attrs.items())))))
    if node.name in ("script", "style"):
        out.append((path + "/#", "text", norm_text(node.get_text())))
        return
    i = 0
    for child in node.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            if norm_text(str(child)):
                flatten(child, path + "/text()", out)
            continue
        i += 1
        flatten(child, "%s/%s[%d]" % (path, child.name, i), out)


def dom_diff(a_html, b_html, limit=20):
    fa, fb = [], []
    flatten(BeautifulSoup(a_html, "lxml").html, "/html", fa)
    flatten(BeautifulSoup(b_html, "lxml").html, "/html", fb)
    diffs = []
    for i in range(max(len(fa), len(fb))):
        x = fa[i] if i < len(fa) else None
        y = fb[i] if i < len(fb) else None
        if x != y:
            diffs.append((x, y))
            if len(diffs) >= limit:
                break
    return diffs, len(fa), len(fb)


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def counts(m):
    c = {"weeks": len(m["weeks"]),
         "lessons": sum(len(w.get("lessons", [])) for w in m["weeks"]),
         "focuses": sum(len(w.get("focuses", [])) for w in m["weeks"]),
         "podcasts": sum(len(w.get("podcasts", [])) for w in m["weeks"]),
         "episodeChips": sum(len(w.get("episodes", [])) for w in m["weeks"]),
         "ticks": sum(len(w["ticks"] if isinstance(w["ticks"], list) else m["labels"]["tickSets"][w["ticks"]]) for w in m["weeks"]),
         "LINKS": len(build_ks4.link_keys(m)),
         "resourceButtons": sum(len(w.get("reads", [])) + sum(1 for l in w.get("lessons", []) if l.get("deck")) for w in m["weeks"])
         + sum(len(c["items"]) for c in m["shelf"]["columns"]) + len(m["shelf"]["wide"])}
    return c


def count_html(page):
    soup = BeautifulSoup(page, "lxml")
    return {"weeks": len(soup.select("article.wk")),
            "lessons": len(soup.select("div.les:not(.les-rev)")),
            "focuses": len(soup.select("div.les.les-rev")),
            "podcasts": len(soup.select("div.pod")),
            "episodeChips": len(soup.select("a.pchip")),
            "ticks": len(soup.select("input[data-t]")),
            "navChips": len(soup.select("a.nch")),
            "dataSp": len(soup.select("[data-sp]")),
            "resourceButtons": len(soup.select("a.res-btn")),
            "LINKS": len(re.findall(r'\n  [A-Za-z0-9_]+: "', page))}


def run(pages, write_manifests=True):
    os.makedirs(SCRATCH, exist_ok=True)
    ok_all = True
    report = []
    for src_path in pages:
        name = os.path.splitext(os.path.basename(src_path))[0]
        src = open(src_path, encoding="utf-8").read()
        man = extract_ks4.extract(src)
        man = {k: man[k] for k in extract_ks4.ORDER}
        if write_manifests:
            mp = os.path.join(HERE, "manifests", name.replace("year11-", "y11-") + ".json")
            with open(mp, "w", encoding="utf-8") as f:
                json.dump(man, f, ensure_ascii=False, indent=2)
                f.write("\n")
        page = build_ks4.build(man)
        out_path = os.path.join(SCRATCH, os.path.basename(src_path))
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(page)
        byte_ok = sha(src) == sha(page)
        diffs, na, nb = dom_diff(src, page)
        dom_ok = not diffs
        ok_all = ok_all and dom_ok
        ch_src, ch_out = count_html(src), count_html(page)
        line = "%s  %s   byte:%s  DOM:%s (%d nodes)" % (
            "PASS" if dom_ok else "FAIL", name, "identical" if byte_ok else "differs", "identical" if dom_ok else "%d diffs" % len(diffs), na)
        print(line)
        for x, y in diffs:
            print("   source :", x)
            print("   rebuilt:", y)
        report.append({"page": name, "byte": byte_ok, "dom": dom_ok, "nodes": na, "manifestCounts": counts(man),
                       "sourceCounts": ch_src, "rebuiltCounts": ch_out, "sha256": sha(page)})
    with open(os.path.join(SCRATCH, "roundtrip.json"), "w") as f:
        json.dump(report, f, indent=2)
    return ok_all


if __name__ == "__main__":
    pages = sys.argv[1:] or DEFAULT
    sys.exit(0 if run(pages, write_manifests=not sys.argv[1:]) else 1)
