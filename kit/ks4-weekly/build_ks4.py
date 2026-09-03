#!/usr/bin/env python3
# © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework, Weekly Page Kit (KS4 edition). All rights reserved. Harlington School deployment licensed for internal use. Not for reproduction or redistribution without written permission.
"""
build_ks4.py <manifest.json> <out.html> [--template template.ks4weekly.html]

One ks4-weekly/1 manifest -> one finished page.  Rendering is server-side:
the template carries the design (CSS) and the behaviour (JS) with %%TOKENS%%
where course content goes, and this file fills every token from the manifest.

validate() runs first and refuses to write on any structural error — see the
list at the bottom of schema.md.  Warnings (things that are probably wrong
but not certainly) are printed and do not block the build.

Text conventions (schema.md, "text or HTML?"):
  * plain-text fields are escaped here with html.escape()   -> ' becomes &#x27;
  * HTML-fragment fields are inserted verbatim
"""
import html
import json
import os
import re
import sys
from datetime import date

SCHEMA = "ks4-weekly/1"
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.ks4weekly.html")
TOP_KEYS = ["schema", "meta", "theme", "files", "calendar", "how", "weeksSection", "weeks", "shelf", "map", "labels"]
TYPES = ["teach", "rev", "mock", "fb", "ret", "ex"]
KIT_NOTICE = "© 2026 Dr Vitor Merissi de Carvalho"

E = lambda s: html.escape(str(s), quote=True)  # plain text -> HTML


def js_str(s):
    """A JS double-quoted string literal. Non-ASCII stays as-is (the page is UTF-8)."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def js_concat(pattern, subs):
    """'Week %W% link copied' with {'%W%':'btn.dataset.w'} -> "Week "+btn.dataset.w+" link copied"."""
    parts = []
    for piece in re.split(r'(%[A-Z]+%)', pattern):
        if not piece:
            continue
        parts.append(subs[piece] if piece in subs else js_str(piece))
    return "+".join(parts)


# ------------------------------------------------------------------ validate
class ManifestError(Exception):
    pass


def validate(m):
    errs, warns = [], []
    for k in TOP_KEYS:
        if k not in m:
            errs.append("missing top-level key: %s" % k)
    if errs:
        return errs, warns
    if m["schema"] != SCHEMA:
        errs.append("schema is %r, expected %r" % (m["schema"], SCHEMA))
    cal = m["calendar"]
    weeks = cal.get("weeks")
    if not isinstance(weeks, list) or not weeks:
        errs.append("calendar.weeks is empty or not a list")
        weeks = []
    for i, d in enumerate(weeks):
        if not isinstance(d, str) or not re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            errs.append("calendar.weeks[%d] = %r is not YYYY-MM-DD" % (i, d))
            continue
        try:
            dd = date.fromisoformat(d)
            if dd.weekday() != 0:
                warns.append("calendar.weeks[%d] = %s is a %s, not a Monday" % (i, d, dd.strftime("%A")))
        except ValueError:
            errs.append("calendar.weeks[%d] = %r is not a real date" % (i, d))
    if len(m["weeks"]) != len(weeks):
        errs.append("week count mismatch: %d weeks, %d calendar dates" % (len(m["weeks"]), len(weeks)))
    seen = set()
    for wk in m["weeks"]:
        n = wk.get("n")
        if n in seen:
            errs.append("duplicate week number %r" % n)
        seen.add(n)
        if not isinstance(n, int) or n < 1 or n > max(len(weeks), 1):
            errs.append("week number %r is outside 1..%d" % (n, len(weeks)))
        if wk.get("type") not in TYPES:
            errs.append("week %r: unknown type %r (expected one of %s)" % (n, wk.get("type"), ", ".join(TYPES)))
        if wk.get("paper") and wk["paper"] not in m["labels"].get("papers", {}):
            errs.append("week %r: paper %r has no label in labels.papers" % (n, wk["paper"]))
        for i, les in enumerate(wk.get("lessons", [])):
            deck = les.get("deck")
            if deck is not None and not (deck.get("rel") or deck.get("href")):
                errs.append("week %r lesson %d: deck has no path (rel/href)" % (n, i + 1))
        for i, p in enumerate(wk.get("podcasts", [])):
            if not (p.get("rel") or p.get("src")):
                errs.append("week %r podcast %d: no path (rel/src)" % (n, i + 1))
        for i, e in enumerate(wk.get("episodes", [])):
            if not e.get("rel"):
                errs.append("week %r episode chip %d: no path (rel)" % (n, i + 1))
        for i, r in enumerate(wk.get("reads", [])):
            if not (r.get("rel") or r.get("href")):
                errs.append("week %r read %d: resource has no path (rel/href)" % (n, i + 1))
        t = wk.get("ticks")
        if isinstance(t, str):
            if t not in m["labels"].get("tickSets", {}):
                errs.append("week %r: tick set %r is not in labels.tickSets" % (n, t))
        elif not isinstance(t, list):
            errs.append("week %r: ticks must be a set name or a list of [id, label]" % n)
    if sorted(seen) != list(range(1, len(weeks) + 1)) and not errs:
        errs.append("week numbers must run 1..%d without gaps" % len(weeks))
    for t in cal.get("terms", []):
        if not (1 <= t.get("from", 0) <= len(weeks)):
            errs.append("term %r starts at week %r, outside the calendar" % (t.get("label"), t.get("from")))
    for h in cal.get("holidays", []):
        if not (1 <= h.get("before", 0) <= len(weeks) + 1):
            errs.append("holiday %r is placed before week %r, outside the calendar" % (h.get("label"), h.get("before")))
    for i, r in enumerate(m["shelf"].get("wide", []) + sum((c.get("items", []) for c in m["shelf"].get("columns", [])), [])):
        if not (r.get("rel") or r.get("href")):
            errs.append("shelf resource %d (%r) has no path" % (i, r.get("key")))
    if not errs:  # the calendar is sound, so the softer checks can index into it
        for ex in cal.get("exams", []):
            try:
                d = date.fromisoformat(ex["date"])
            except (KeyError, TypeError, ValueError):
                warns.append("calendar.exams entry %r has no valid date" % ex.get("label"))
                continue
            inside = [wk for wk in m["weeks"] if wk.get("type") == "ex"
                      and 0 <= (d - date.fromisoformat(weeks[wk["n"] - 1])).days < 7]
            if not inside:
                warns.append("exam %r on %s does not fall in a week of type 'ex'" % (ex.get("label"), ex["date"]))
    for k in ("week", "lesson", "focus", "relisten", "progress"):
        if k in m["labels"] and "%N" not in m["labels"][k] and "%D%" not in m["labels"][k]:
            warns.append("labels.%s has no %%N%% placeholder" % k)
    return errs, warns


# ------------------------------------------------------------------- render
def res_btn(r, cls=""):
    attrs = []
    if r.get("localonly"):
        attrs.append('data-localonly="1"')
    attrs.append('class="res-btn%s"' % ((" " + cls) if cls else ""))
    attrs.append('data-key="%s"' % r["key"])
    attrs.append('data-rel="%s"' % r.get("rel", ""))
    if "href" in r:
        attrs.append('href="%s"' % r["href"])
    if r.get("sp") is not None:
        attrs.append('data-sp="%s"' % r["sp"])
    lb = E(r["label"]) + ("<em>%s</em>" % E(r["sub"]) if r.get("sub") is not None else "")
    return '<a %s><span class="ic">%s</span><span class="lb">%s</span><span class="go">&#8599;</span></a>' % (
        " ".join(attrs), r.get("icon", "&#9679;"), lb)


def fmt_date(iso):
    d = date.fromisoformat(iso)
    return "%s %d %s %d" % (d.strftime("%a"), d.day, d.strftime("%b"), d.year)


def render_week(wk, iso, L):
    n = wk["n"]
    ph = "ph-" + wk["type"]
    out = ['<article class="wk %s" id="w%d" data-iso="%s"><div class="wk-h">\n' % (ph, n, iso)]
    out.append('      <span class="wno">%s</span>\n' % E(L["week"].replace("%NN%", "%02d" % n).replace("%N%", str(n))))
    out.append('      <span class="phase %s">%s</span>\n' % (ph, E(L["phases"][wk["type"]])))
    out.append('      <span class="wdate">%s</span>\n' % fmt_date(iso))
    out.append('      <button class="wlink" data-w="%d" title="%s">&#128279; %s</button>\n' % (n, E(L["copyTitle"]), E(L["copyLink"])))
    out.append('    </div>')
    if wk.get("paper"):
        out.append('<span class="chip %s">%s</span>' % (wk["paper"], E(L["papers"][wk["paper"]])))
    out.append('<h3 class="wk-t">%s</h3><p class="say">%s</p>' % (E(wk["title"]), E(wk["say"])))

    lessons, focuses = wk.get("lessons", []), wk.get("focuses", [])
    if lessons or focuses:
        one = len(lessons) + len(focuses) == 1
        out.append('<div class="lessons%s">' % (" lessons-one" if one else ""))
        for i, les in enumerate(lessons):
            bq = E(les["bq"])
            if les.get("spec"):
                bq += ' <span class="spec" style="opacity:.55;font-size:.85em;white-space:nowrap">%s%s</span>' % (
                    E(L.get("specPrefix", "· spec ")), E(les["spec"]))
            out.append('<div class="les">\n')
            out.append('      <div class="les-h"><span class="lnum">%s</span><h4>%s</h4></div>\n' % (E(L["lesson"].replace("%N%", str(i + 1))), E(les["title"])))
            out.append('      <p class="bq"><span>%s</span> %s</p>\n' % (E(L["bigQuestion"]), bq))
            out.append('      <div class="sum"><span class="sum-l">%s</span>%s</div>\n' % (E(L["summary"]), "".join("<p>%s</p>" % E(p) for p in les.get("sum", []))))
            if les.get("deck"):
                out.append('      %s\n' % res_btn(les["deck"], "slim"))
            out.append('      <div class="kws"><span class="kws-l">%s</span>%s</div>\n' % (E(L["keyWords"]), "".join('<span class="kw">%s</span>' % E(k) for k in les.get("kws", []))))
            q = les.get("quote") or {}
            out.append('      <div class="quo"><span class="quo-l">%s</span><q>%s</q>%s</div>\n' % (
                E(L["quote"]), E(q.get("q", "")), ("<cite>%s</cite>" % E(q["cite"])) if q.get("cite") is not None else ""))
            out.append('    </div>')
        for i, f in enumerate(focuses):
            out.append('<div class="les les-rev"><div class="les-h"><span class="lnum">%s</span><h4>%s</h4></div><div class="sum"><span class="sum-l">%s</span>%s</div></div>' % (
                E(L["focus"].replace("%N%", str(i + 1))), E(f["title"]), E(L["summary"]), "".join("<p>%s</p>" % E(p) for p in f.get("sum", []))))
        out.append('</div>')
    if wk.get("checklist"):
        out.append('<ul class="chklist">%s</ul>' % "".join("<li>%s</li>" % E(x) for x in wk["checklist"]))
    if wk.get("activities"):
        out.append('<div class="acts">%s</div>' % "".join('<div class="act"><h5>%s</h5><p>%s</p></div>' % (E(a["title"]), E(a["body"])) for a in wk["activities"]))
    if wk.get("podcasts"):
        pods = []
        for p in wk["podcasts"]:
            attrs = 'data-key="%s" data-rel="%s"' % (p["key"], p.get("rel", ""))
            if p.get("sp") is not None:
                attrs += ' data-sp="%s"' % p["sp"]
            pods.append('<div class="pod" %s><div class="pod-h"><span class="pcode pc-%s">%s</span><span class="pname">%s</span><span class="pkind">%s</span></div><audio controls preload="none" src="%s"></audio></div>' % (
                attrs, p.get("series", "e"), E(p["code"]), E(p["name"]), E(p.get("kind", "")), p.get("src", p.get("rel", ""))))
        out.append('<div class="podwrap"><span class="blk-l">%s</span><div class="pods">%s</div></div>' % (E(L["podcast"]), "".join(pods)))
    if wk.get("podnote"):
        out.append('<p class="podnote">%s</p>' % E(wk["podnote"]))
    if wk.get("episodes"):
        chips = []
        for e in wk["episodes"]:
            attrs = 'data-key="%s" data-rel="%s"' % (e["key"], e["rel"])
            if e.get("sp") is not None:
                attrs += ' data-sp="%s"' % e["sp"]
            chips.append('<a class="pchip" %s>%s</a>' % (attrs, E(e["text"])))
        out.append('<div class="podset"><span class="blk-l">%s</span><div class="pchips">%s</div></div>' % (
            E(L["relisten"].replace("%N%", str(len(chips)))), "".join(chips)))
    if wk.get("reads"):
        out.append('<div class="shelf"><span class="blk-l">%s</span><div class="shelf-g">%s</div></div>' % (E(L["shelf"]), "".join(res_btn(r) for r in wk["reads"])))
    ticks = wk.get("ticks", [])
    if isinstance(ticks, str):
        ticks = L["tickSets"][ticks]
    out.append('<div class="ticks"><span class="tl">%s</span>%s</div>' % (E(L["ticks"]), "".join(
        '<label class="tk"><input type="checkbox" data-t="w%d_%s"><span>%s</span></label>' % (n, tid, E(lbl)) for tid, lbl in ticks)))
    out.append('</article>')
    return "".join(out), len(ticks)


def render_weeks(m):
    cal, L = m["calendar"], m["labels"]
    weeks = sorted(m["weeks"], key=lambda w: w["n"])
    glyph = L.get("holidayGlyph", "&#9670;")
    lines, ticks = [], 0
    for wk in weeks:
        n = wk["n"]
        for t in cal.get("terms", []):
            if t["from"] == n:
                lines.append('<div class="term-band"><span>%s</span><i></i></div>' % E(t["label"]))
        for h in cal.get("holidays", []):
            if h["before"] == n:
                lines.append('<div class="hol">%s %s</div>' % (glyph, E(h["label"])))
        s, k = render_week(wk, cal["weeks"][n - 1], L)
        lines.append(s)
        ticks += k
    for h in cal.get("holidays", []):
        if h["before"] == len(weeks) + 1:
            lines.append('<div class="hol">%s %s</div>' % (glyph, E(h["label"])))
    chips = "".join('<a class="nch ph-%s" href="#w%d" data-w="%d">%d</a>' % (w["type"], w["n"], w["n"], w["n"]) for w in weeks)
    return "\n".join(lines), chips, ticks


def link_keys(m):
    """Every resource button without a fixed href, and every podcast player."""
    keys = set()

    def take(r):
        if r.get("key") and "href" not in r:
            keys.add(r["key"])

    for wk in m["weeks"]:
        for les in wk.get("lessons", []):
            if les.get("deck"):
                take(les["deck"])
        for r in wk.get("reads", []):
            take(r)
        for p in wk.get("podcasts", []):
            if p.get("key"):
                keys.add(p["key"])
    for c in m["shelf"].get("columns", []):
        for r in c.get("items", []):
            take(r)
    for r in m["shelf"].get("wide", []):
        take(r)
    keys |= set(k for k in m["files"].get("links", {}) if not k.startswith("_"))
    return sorted(keys)


def media_count(m):
    n = 0
    for wk in m["weeks"]:
        n += sum(1 for les in wk.get("lessons", []) if les.get("deck"))
        n += len(wk.get("reads", [])) + len(wk.get("podcasts", [])) + len(wk.get("episodes", []))
    n += sum(len(c.get("items", [])) for c in m["shelf"].get("columns", [])) + len(m["shelf"].get("wide", []))
    return n


def apply_variants(t, cond):
    """%%IF key=value%% ... %%ELSE%% ... %%END%% blocks, each marker on its own line."""
    out, keep, stack = [], True, []
    for line in t.split("\n"):
        mm = re.match(r'^%%IF (\w+)=(\w+)%%$', line)
        if mm:
            stack.append(keep)
            keep = keep and cond.get(mm.group(1)) == mm.group(2)
            continue
        if line == "%%ELSE%%":
            keep = stack[-1] and not keep
            continue
        if line == "%%END%%":
            keep = stack.pop()
            continue
        if keep:
            out.append(line)
    return "\n".join(out)


def build(m, template=None):
    errs, warns = validate(m)
    for w in warns:
        print("warning:", w, file=sys.stderr)
    if errs:
        raise ManifestError("\n".join(errs))
    t = open(template or TEMPLATE, encoding="utf-8").read()
    if t.startswith("<!-- " + KIT_NOTICE):  # the kit's own notice line is not part of the page
        t = t.split("\n", 1)[1]
    meta, files, L = m["meta"], m["files"], m["labels"]
    weeks_html, chips, tick_total = render_weeks(m)

    tok = {}
    tok["TITLE"] = E(meta["title"])
    tok["DESCRIPTION"] = ('\n<meta name="description" content="%s">' % E(meta["description"])) if meta.get("description") else ""
    tok["NOINDEX"] = '\n<meta name="robots" content="noindex">' if meta.get("noindex") else ""
    theme = {k: v for k, v in (m.get("theme") or {}).items() if not k.startswith("_")}
    tok["THEME"] = ("  :root{%s}\n" % ";".join("--%s:%s" % (k, v) for k, v in theme.items())) if theme else ""
    tok["HOME_ARIA"] = L.get("homeNavAria", "")
    tok["HOME_HREF"] = meta["homeLink"]["href"]
    tok["HOME_HTML"] = meta["homeLink"]["html"]
    tok["EYEBROW_1"], tok["EYEBROW_2"] = meta["eyebrow"]
    tok["PILL"], tok["H1"], tok["TAGLINE"], tok["SUB"] = meta["pill"], meta["h1"], meta["tagline"], meta["sub"]
    tok["FACTS"] = "".join("      <div><b>%s</b><span>%s</span></div>\n" % (b, s) for b, s in meta.get("facts", []))
    tok["GO_TO_WEEK"] = E(L["goToWeek"])
    tok["NAV_CHIPS"] = chips
    tok["PROGRESS"] = E(L["progress"].replace("%D%", "0").replace("%N%", str(tick_total)))
    how = m["how"]
    tok["HOW_NUM"], tok["HOW_TITLE"], tok["HOW_LEAD"] = how["num"], how["title"], how["lead"]
    tok["HOW_STEPS"] = "".join('    <div class="h3c"><span class="hn">%d</span><h4>%s</h4><p>%s</p><em>%s</em></div>\n' % (
        i + 1, s["title"], s["body"], s["note"]) for i, s in enumerate(how["steps"]))
    ws = m["weeksSection"]
    tok["WEEKS_NUM"], tok["WEEKS_TITLE"], tok["WEEKS_LEAD"] = ws["num"], ws["title"], ws["lead"]
    tok["WEEKS"] = weeks_html
    sh = m["shelf"]
    tok["SHELF_NUM"], tok["SHELF_TITLE"], tok["SHELF_LEAD"] = sh["num"], sh["title"], sh["lead"]
    tok["SHELF_NOTE"] = sh.get("note", "").replace("%MEDIA%", str(media_count(m)))
    tok["SHELF_GRID"] = "".join('<div class="res-col %s"><div class="rc-head"><span class="rc-n">%s</span><h3>%s</h3></div>%s</div>' % (
        c["cls"], c["eyebrow"], c["title"], "".join(res_btn(r) for r in c["items"])) for c in sh.get("columns", []))
    tok["SHELF_WIDE"] = "".join(res_btn(r, "big") for r in sh.get("wide", []))
    mp = m["map"]
    tok["MAP_NUM"], tok["MAP_TITLE"], tok["MAP_LEAD"] = mp["num"], mp["title"], mp["lead"]
    cards = []
    for c in mp.get("cards", []):
        ps = "".join("      <p>%s</p>\n" % l for l in c.get("lines", []))
        if c.get("examDay"):
            ps += '      <p class="exday">%s</p>\n' % c["examDay"]
        cards.append('    <div class="ecard %s"><div class="eh">%s</div><div class="eb">\n%s</div></div>\n' % (c["cls"], c["head"], ps.rstrip("\n")))
    tok["MAP_CARDS"] = "".join(cards)
    tok["FOOTER_LEFT"], tok["FOOTER_RIGHT"] = meta["footer"]

    tok["SETUP_NOTE"] = "\n".join(files.get("setupNote", []))
    tok["RESOURCE_BASE"] = js_str(files.get("resourceBase", ""))
    tok["PODCAST_NOTE"] = "\n   ".join(files.get("podcastNote", []))
    tok["PODCAST_BASE"] = js_str(files.get("podcastBase", ""))
    tok["FOLDER_NAME"] = files.get("folderName", "resource")
    links = {k: v for k, v in files.get("links", {}).items() if not k.startswith("_")}
    tok["LINKS"] = ",\n".join("  %s: %s" % (k, js_str(links.get(k, ""))) for k in link_keys(m))
    tok["PODCAST_FOLDER_RAW"] = files.get("podcastFolder", "Podcast_Audio")
    tok["PODCAST_FOLDER"] = js_str(tok["PODCAST_FOLDER_RAW"] + "/")
    tok["STORAGE_KEY"] = js_str(meta["id"] + "_ticks")
    tok["PROGRESS_EXPR"] = js_concat(L["progress"], {"%D%": "done", "%N%": "boxes.length"})
    tok["SITE_URL_EXPR"] = js_str(meta["siteUrl"]) if meta.get("siteUrl") else 'location.href.split("#")[0]'
    tok["COPIED"] = js_str(L["copied"])
    tok["TOAST_COPIED_EXPR"] = js_concat(L["toastCopied"], {"%W%": "btn.dataset.w"})
    tok["COPY_LINK_JS"] = js_str("🔗 " + L["copyLink"])
    tok["COPY_PROMPT"] = js_str(L["copyPrompt"])
    tok["THIS_WEEK"] = js_str(L["thisWeek"])
    tok["TOAST_PLAYING_EXPR"] = js_concat(L["toastPlaying"], {"%E%": "c.textContent"})
    tok["CHECK_OK"] = js_str("<b>" + L["checkOk"] + "</b><span>")
    tok["CHECK_OK_ONLINE"], tok["CHECK_OK_LOCAL"] = js_str(L["checkOkOnline"]), js_str(L["checkOkLocal"])
    tok["CHECK_BAD"] = js_str("<b>" + L["checkBad"] + "</b><span>")
    tok["CHECK_BAD_ONLINE"], tok["CHECK_BAD_NOBASE"], tok["CHECK_BAD_LOCAL"] = js_str(L["checkBadOnline"]), js_str(L["checkBadNoBase"]), js_str(L["checkBadLocal"])
    tok["TRIPWIRE_EP"] = js_str(meta.get("tripwireEndpoint", ""))
    tok["TRIPWIRE_PATH"] = js_str(meta.get("tripwirePath", ""))
    tok["CANONICAL_HOST"] = js_str(meta.get("canonicalHost", ""))

    t = apply_variants(t, {"selfCheck": files.get("selfCheck", "audio")})
    missing = set()

    def sub(mm):
        k = mm.group(1)
        if k not in tok:
            missing.add(k)
            return mm.group(0)
        return tok[k]

    t = re.sub(r'%%([A-Z_0-9]+)%%', sub, t)
    if missing:
        raise ManifestError("template tokens with no value: " + ", ".join(sorted(missing)))
    return t


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    template = None
    for i, a in enumerate(argv):
        if a == "--template":
            template = argv[i + 1]
            args.remove(template) if template in args else None
    if len(args) != 2:
        raise SystemExit(__doc__)
    m = json.load(open(args[0], encoding="utf-8"))
    try:
        page = build(m, template)
    except ManifestError as e:
        print("build_ks4: refusing to write %s:\n  %s" % (args[1], str(e).replace("\n", "\n  ")), file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(args[1])), exist_ok=True)
    with open(args[1], "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print("wrote %s (%d bytes, %d weeks)" % (args[1], len(page.encode("utf-8")), len(m["weeks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
