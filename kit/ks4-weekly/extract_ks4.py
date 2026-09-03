#!/usr/bin/env python3
# © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework, Weekly Page Kit (KS4 edition). All rights reserved. Harlington School deployment licensed for internal use. Not for reproduction or redistribution without written permission.
"""
extract_ks4.py <page.html> <out.json>

Reads one hand-built "Year 11 RS · Week by Week" page and writes a
ks4-weekly/1 manifest that build_ks4.py turns back into the same page.

The page is machine-shaped, so extraction is regex-driven over the raw
source rather than a DOM walk: that lets the hand-written blocks (hero,
section leads, exam map, footer) keep their original HTML entities verbatim,
while the generated week cards are unescaped into plain text — build_ks4.py
re-escapes them with html.escape(), which is what produced them originally.

Field conventions are in schema.md.  Nothing in here is course-specific:
every string that names a course, a folder, a paper or a tier ends up in the
manifest, not in the template.
"""
import html
import json
import re
import sys
from datetime import date

SCHEMA = "ks4-weekly/1"

# ----------------------------------------------------------------- helpers
T = html.unescape  # a generated-text field: entities -> plain text


def one(pattern, s, flags=re.S, group=1, required=True):
    m = re.search(pattern, s, flags)
    if not m:
        if required:
            raise SystemExit("extract: pattern not found: " + pattern[:80])
        return None
    return m.group(group)


def between(s, start, end):
    i = s.index(start) + len(start)
    j = s.index(end, i)
    return s[i:j]


# ----------------------------------------------------------- resource button
RES_BTN = re.compile(
    r'<a (?P<attrs>[^>]*class="res-btn(?P<cls>[^"]*)"[^>]*)>'
    r'<span class="ic">(?P<icon>[^<]*)</span>'
    r'<span class="lb">(?P<label>[^<]*)(?:<em>(?P<sub>[^<]*)</em>)?</span>'
    r'<span class="go">&#8599;</span></a>'
)


def attr(attrs, name):
    m = re.search(r'\b' + re.escape(name) + r'="([^"]*)"', attrs)
    return m.group(1) if m else None


def parse_btn(m):
    a = m.group("attrs")
    d = {"key": attr(a, "data-key"), "rel": attr(a, "data-rel")}
    if attr(a, "href") is not None:
        d["href"] = attr(a, "href")
    if attr(a, "data-sp") is not None:
        d["sp"] = attr(a, "data-sp")
    if attr(a, "data-localonly") == "1":
        d["localonly"] = True
    d["icon"] = m.group("icon")
    d["label"] = T(m.group("label"))
    if m.group("sub") is not None:
        d["sub"] = T(m.group("sub"))
    return d


def parse_btns(fragment):
    return [parse_btn(m) for m in RES_BTN.finditer(fragment)]


# ------------------------------------------------------------------ lessons
LES = re.compile(
    r'<div class="les">\n'
    r'      <div class="les-h"><span class="lnum">(?P<lnum>[^<]*)</span><h4>(?P<title>[^<]*)</h4></div>\n'
    r'      <p class="bq"><span>(?P<bql>[^<]*)</span> (?P<bq>.*?)</p>\n'
    r'      <div class="sum"><span class="sum-l">(?P<suml>[^<]*)</span>(?P<sum>(?:<p>.*?</p>)+)</div>\n'
    r'      (?P<deck><a [^>]*class="res-btn slim"[^>]*>.*?</a>)\n'
    r'      <div class="kws"><span class="kws-l">(?P<kwl>[^<]*)</span>(?P<kws>(?:<span class="kw">[^<]*</span>)*)</div>\n'
    r'      <div class="quo"><span class="quo-l">(?P<quol>[^<]*)</span><q>(?P<q>[^<]*)</q>(?:<cite>(?P<cite>[^<]*)</cite>)?</div>\n'
    r'    </div>',
    re.S,
)
FOCUS = re.compile(
    r'<div class="les les-rev"><div class="les-h"><span class="lnum">(?P<lnum>[^<]*)</span><h4>(?P<title>[^<]*)</h4></div>'
    r'<div class="sum"><span class="sum-l">(?P<suml>[^<]*)</span>(?P<sum>(?:<p>.*?</p>)+)</div></div>',
    re.S,
)
SPEC = re.compile(r'^(?P<q>.*?) <span class="spec" style="opacity:\.55;font-size:\.85em;white-space:nowrap">(?P<pre>[^<]*?)(?P<spec>\d[^<]*)</span>$', re.S)
POD = re.compile(
    r'<div class="pod" (?P<attrs>[^>]*)><div class="pod-h"><span class="pcode pc-(?P<series>[a-z])">(?P<code>[^<]*)</span>'
    r'<span class="pname">(?P<name>[^<]*)</span><span class="pkind">(?P<kind>[^<]*)</span></div>'
    r'<audio controls preload="none" src="(?P<src>[^"]*)"></audio></div>'
)
PCHIP = re.compile(r'<a class="pchip" (?P<attrs>[^>]*)>(?P<text>[^<]*)</a>')
TICK = re.compile(r'<label class="tk"><input type="checkbox" data-t="w(?P<n>\d+)_(?P<id>[a-z]+)"><span>(?P<label>[^<]*)</span></label>')

PHASES = {"ph-teach": "teach", "ph-rev": "rev", "ph-mock": "mock", "ph-fb": "fb", "ph-ret": "ret", "ph-ex": "ex"}


def paragraphs(frag):
    return [T(p) for p in re.findall(r'<p>(.*?)</p>', frag, re.S)]


def num_pattern(text, n):
    """'Lesson 1' with n=1 -> 'Lesson %N%'."""
    if text.endswith(" " + str(n)):
        return text[: -len(str(n))] + "%N%"
    raise SystemExit("extract: unexpected numbered label " + text)


def parse_week(article, labels):
    head = one(r'<article class="wk (ph-[a-z]+)" id="w(\d+)" data-iso="([^"]+)">', article, group=0)
    m = re.match(r'<article class="wk (ph-[a-z]+)" id="w(\d+)" data-iso="([^"]+)">', head)
    ph, n, iso = m.group(1), int(m.group(2)), m.group(3)
    wk = {"n": n, "type": PHASES[ph]}
    phase_label = one(r'<span class="phase ' + ph + r'">([^<]*)</span>', article)
    labels["phases"].setdefault(wk["type"], phase_label)
    wno = one(r'<span class="wno">([^<]*)</span>', article)
    labels.setdefault("week", wno[: -2] + "%NN%") if wno.endswith("%02d" % n) else None
    labels.setdefault("copyTitle", one(r'<button class="wlink" data-w="\d+" title="([^"]*)">', article))
    labels.setdefault("copyLink", T(one(r'<button class="wlink"[^>]*>&#128279; ([^<]*)</button>', article)))
    body = between(article, "</button>\n    </div>", "</article>")

    chip = re.match(r'<span class="chip (p\d)">([^<]*)</span>', body)
    if chip:
        wk["paper"] = chip.group(1)
        labels["papers"].setdefault(chip.group(1), T(chip.group(2)))
        body = body[chip.end():]
    wk["title"] = T(one(r'^<h3 class="wk-t">([^<]*)</h3>', body))
    wk["say"] = T(one(r'<p class="say">([^<]*)</p>', body))

    # lessons / focuses
    lessons = []
    for lm in LES.finditer(body):
        les = {"title": T(lm.group("title"))}
        labels.setdefault("lesson", num_pattern(lm.group("lnum"), len(lessons) + 1))
        labels.setdefault("bigQuestion", T(lm.group("bql")))
        labels.setdefault("summary", T(lm.group("suml")))
        labels.setdefault("keyWords", T(lm.group("kwl")))
        labels.setdefault("quote", T(lm.group("quol")))
        bq = lm.group("bq")
        sm = SPEC.match(bq)
        if sm:
            les["bq"] = T(sm.group("q"))
            les["spec"] = T(sm.group("spec"))
            labels.setdefault("specPrefix", T(sm.group("pre")))
        else:
            les["bq"] = T(bq)
        les["sum"] = paragraphs(lm.group("sum"))
        deck = parse_btns(lm.group("deck"))[0]
        les["deck"] = deck
        les["kws"] = [T(k) for k in re.findall(r'<span class="kw">([^<]*)</span>', lm.group("kws"))]
        les["quote"] = {"q": T(lm.group("q"))}
        if lm.group("cite") is not None:
            les["quote"]["cite"] = T(lm.group("cite"))
        lessons.append(les)
    if lessons:
        wk["lessons"] = lessons
    focuses = []
    for fm in FOCUS.finditer(body):
        labels.setdefault("focus", num_pattern(fm.group("lnum"), len(focuses) + 1))
        labels.setdefault("summary", T(fm.group("suml")))
        focuses.append({"title": T(fm.group("title")), "sum": paragraphs(fm.group("sum"))})
    if focuses:
        wk["focuses"] = focuses

    # checklist / activities
    chk = re.search(r'<ul class="chklist">(.*?)</ul>', body, re.S)
    if chk:
        wk["checklist"] = [T(x) for x in re.findall(r'<li>([^<]*)</li>', chk.group(1))]
    acts = re.search(r'<div class="acts">(.*?)</div></div>(?=<div class="shelf">|<div class="ticks">)', body, re.S)
    if acts:
        wk["activities"] = [{"title": T(h), "body": T(p)} for h, p in
                            re.findall(r'<div class="act"><h5>([^<]*)</h5><p>([^<]*)</p></div>', acts.group(1) + "</div>")]

    # podcasts
    pw = re.search(r'<div class="podwrap"><span class="blk-l">([^<]*)</span><div class="pods">(.*?)</div></div>(?=<div class="podset">|<div class="shelf">|<p class="podnote">|<div class="ticks">)', body, re.S)
    if pw:
        labels.setdefault("podcast", T(pw.group(1)))
        pods = []
        for pm in POD.finditer(pw.group(2)):
            a = pm.group("attrs")
            p = {"key": attr(a, "data-key"), "rel": attr(a, "data-rel")}
            if attr(a, "data-sp") is not None:
                p["sp"] = attr(a, "data-sp")
            if pm.group("src") != p["rel"]:
                p["src"] = pm.group("src")
            p.update(series=pm.group("series"), code=T(pm.group("code")), name=T(pm.group("name")), kind=T(pm.group("kind")))
            pods.append(p)
        wk["podcasts"] = pods
    pn = re.search(r'<p class="podnote">([^<]*)</p>', body)
    if pn:
        wk["podnote"] = T(pn.group(1))
    ps = re.search(r'<div class="podset"><span class="blk-l">([^<]*)</span><div class="pchips">(.*?)</div></div>', body, re.S)
    if ps:
        eps = []
        for cm in PCHIP.finditer(ps.group(2)):
            a = cm.group("attrs")
            e = {"key": attr(a, "data-key"), "rel": attr(a, "data-rel")}
            if attr(a, "data-sp") is not None:
                e["sp"] = attr(a, "data-sp")
            e["text"] = T(cm.group("text"))
            eps.append(e)
        lbl = T(ps.group(1))
        cnt = str(len(eps))
        if cnt in lbl:
            labels.setdefault("relisten", lbl.replace(cnt, "%N%", 1))
        wk["episodes"] = eps

    # shelf
    sh = re.search(r'<div class="shelf"><span class="blk-l">([^<]*)</span><div class="shelf-g">(.*?)</div></div><div class="ticks">', body, re.S)
    if sh:
        labels.setdefault("shelf", T(sh.group(1)))
        wk["reads"] = parse_btns(sh.group(2))

    # ticks
    tk = re.search(r'<div class="ticks"><span class="tl">([^<]*)</span>(.*?)</div>$', body, re.S)
    labels.setdefault("ticks", T(tk.group(1)))
    ticks = []
    for tm in TICK.finditer(tk.group(2)):
        assert int(tm.group("n")) == n, "tick id week mismatch in w%d" % n
        ticks.append([tm.group("id"), T(tm.group("label"))])
    wk["ticks"] = ticks
    return wk, iso


def name_tick_sets(weeks, labels):
    """Replace repeated tick lists with named sets in labels.tickSets."""
    names = {"listen": "listen", "revised,sat,timing": "exam", "marks": "feedback", "revised,sat,done": "final"}
    sets = {}
    for wk in weeks:
        key = ",".join(t[0] for t in wk["ticks"])
        name = names.get(key) or names.get(key.split(",")[0]) or "ticks_w%d" % wk["n"]
        if name in sets and sets[name] != wk["ticks"]:
            name = "ticks_w%d" % wk["n"]
        sets.setdefault(name, wk["ticks"])
        wk["ticks"] = name
    labels["tickSets"] = sets


# ------------------------------------------------------------------- page
def js_str_lit(src, pattern):
    """Find a JS string literal following `pattern`; return its text with \\ escapes undone."""
    m = re.search(pattern + r'"((?:[^"\\]|\\.)*)"', src, re.S)
    if not m:
        raise SystemExit("extract: JS literal not found: " + pattern)
    return m.group(1).replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def concat_pattern(expr, subs):
    """'"Week "+btn.dataset.w+" link copied"' -> 'Week %W% link copied'."""
    out = ""
    for piece in re.findall(r'"((?:[^"\\]|\\.)*)"|([A-Za-z_.]+)', expr):
        if piece[0] or piece[1] == "":
            out += piece[0].replace('\\"', '"')
        else:
            out += subs[piece[1]]
    return out


def extract(src):
    labels = {"phases": {}, "papers": {}}
    man = {"schema": SCHEMA}

    # ---- meta
    meta = {}
    meta["title"] = T(one(r'<title>([^<]*)</title>', src))
    meta["description"] = T(one(r'<meta name="description" content="([^"]*)">', src, required=False) or "")
    meta["noindex"] = bool(re.search(r'<meta name="robots" content="noindex', src))
    meta["homeLink"] = {"href": one(r'<a class="cnav-home" href="([^"]*)">', src),
                        "html": one(r'<a class="cnav-home" href="[^"]*">(.*?)</a>', src)}
    labels["homeNavAria"] = one(r'<nav class="cnav" aria-label="([^"]*)">', src)
    who = one(r'<div class="who">(.*?)</div>', src)
    e1, e2 = re.match(r'(.*?)<b>(.*?)</b>$', who, re.S).groups()
    meta["eyebrow"] = [e1, e2]
    meta["pill"] = one(r'<span class="pill">(.*?)</span>', src)
    meta["h1"] = one(r'<h1>(.*?)</h1>', src)
    meta["tagline"] = one(r'<div class="tagline">(.*?)</div>', src)
    meta["sub"] = one(r'<p class="sub">(.*?)</p>', src)
    meta["facts"] = [list(x) for x in re.findall(r'      <div><b>(.*?)</b><span>(.*?)</span></div>\n', between(src, '<div class="heroband">', "</div>\n  </div>\n</header>"))]
    foot = between(src, "<footer>\n  <div class=\"wrap\">\n", "\n  </div>\n</footer>")
    meta["footer"] = re.findall(r'<span(?: class="amber")?>(.*?)</span>', foot)
    meta["siteUrl"] = ""
    site = re.search(r'var url=("(?:[^"\\]|\\.)*")\+"#w"', src)
    if site:
        meta["siteUrl"] = json.loads(site.group(1))
    meta["id"] = js_str_lit(src, r'store\.get\(')[: -len("_ticks")]
    meta["tripwirePath"] = js_str_lit(src, r'p:')
    meta["tripwireEndpoint"] = js_str_lit(src, r'var EP=')
    meta["canonicalHost"] = js_str_lit(src, r'location\.hostname!==')
    meta["tier"] = re.sub(r'\s*(·|-).*$', "", T(meta["pill"])).replace(" edition", "").strip()
    man["meta"] = meta

    # ---- theme
    theme = {}
    tm = re.search(r'\n  :root\{([^}]*)\}\n</style>', src)
    if tm and "--ink:" not in tm.group(1):
        for kv in tm.group(1).split(";"):
            if ":" in kv:
                k, v = kv.split(":", 1)
                theme[k.strip().lstrip("-")] = v.strip()
    man["theme"] = theme

    # ---- files
    files = {}
    files["resourceBase"] = js_str_lit(src, r'const RESOURCE_BASE = ')
    files["podcastBase"] = js_str_lit(src, r'const PODCAST_BASE  = ')
    files["podcastFolder"] = js_str_lit(src, r'var i=sp\.indexOf\(').rstrip("/")
    files["setupNote"] = between(src, "<script>\n/* =====================================================================\n",
                                 "\n   ===================================================================== */\nconst RESOURCE_BASE").split("\n")
    files["podcastNote"] = between(src, '\n\n/* ', ' */\nconst PODCAST_BASE').split("\n   ")
    files["folderName"] = one(r'RESOURCE_BASE \+ its path inside the (.*?) folder', src)
    files["selfCheck"] = "fetch" if 'fetch(first.getAttribute("src"),{method:"HEAD"})' in src else "audio"
    links = re.search(r'const LINKS = \{(.*?)\n\};', src, re.S).group(1)
    files["links"] = {k: v for k, v in re.findall(r'\n  ([A-Za-z0-9_]+): "([^"]*)"', links) if v}
    man["files"] = files

    # ---- how
    how = {}
    hs = between(src, '<section id="how"><div class="wrap">\n', "\n</div></section>")
    how["num"] = one(r'<span class="num">([^<]*)</span>', hs)
    how["title"] = one(r'<h2>(.*?)</h2>', hs)
    how["lead"] = one(r'<p class="sec-lead">(.*?)</p>', hs)
    how["steps"] = [{"title": t, "body": b, "note": n} for t, b, n in
                    re.findall(r'<div class="h3c"><span class="hn">\d+</span><h4>(.*?)</h4><p>(.*?)</p><em>(.*?)</em></div>', hs, re.S)]
    man["how"] = how

    # ---- weeks section
    ws = between(src, '<section id="weeks"><div class="wrap">\n', '\n  <div class="weeks">\n')
    wsec = {"num": one(r'<span class="num">([^<]*)</span>', ws), "title": one(r'<h2>(.*?)</h2>', ws),
            "lead": one(r'<p class="sec-lead">(.*?)</p>', ws)}
    labels["goToWeek"] = T(one(r'<span class="nav-l">([^<]*)</span>', src))
    body = between(src, '  <div class="weeks">\n', '\n  </div>\n</div></section>\n\n<section id="shelf">')
    terms, holidays, weeks, isos = [], [], [], []
    labels.setdefault("holidayGlyph", "&#9670;")
    for line in re.split(r'\n(?=<div class="term-band">|<div class="hol">|<article )', body):
        if line.startswith('<div class="term-band">'):
            terms.append({"label": T(one(r'<span>([^<]*)</span>', line)), "from": len(weeks) + 1})
        elif line.startswith('<div class="hol">'):
            holidays.append({"before": len(weeks) + 1, "label": T(one(r'<div class="hol">&#9670; ([^<]*)</div>', line))})
        else:
            wk, iso = parse_week(line, labels)
            weeks.append(wk)
            isos.append(iso)
    name_tick_sets(weeks, labels)
    man["calendar"] = {"weeks": isos, "terms": terms, "holidays": holidays, "exams": []}
    man["weeksSection"] = wsec
    man["weeks"] = weeks

    # ---- shelf
    sh = between(src, '<section id="shelf"><div class="wrap">\n', "\n</div></section>\n\n<section id=\"map\">")
    shelf = {"num": one(r'<span class="num">([^<]*)</span>', sh), "title": one(r'<h2>(.*?)</h2>', sh),
             "lead": one(r'<p class="sec-lead">(.*?)</p>', sh),
             "note": one(r'<div class="res-note" id="resNote">(.*?)</div>\n  <div class="res-grid">', sh)}
    cols = []
    for cls, eyebrow, title, btns in re.findall(
            r'<div class="res-col (g\d)"><div class="rc-head"><span class="rc-n">(.*?)</span><h3>(.*?)</h3></div>(.*?)</div>(?=<div class="res-col|\n)', sh, re.S):
        cols.append({"cls": cls, "eyebrow": eyebrow, "title": title, "items": parse_btns(btns)})
    shelf["columns"] = cols
    shelf["wide"] = parse_btns(sh[sh.index('<div class="res-wide">'):])
    man["shelf"] = shelf

    # ---- map
    mp = between(src, '<section id="map"><div class="wrap">\n', "\n</div></section>\n\n<footer>")
    mapsec = {"num": one(r'<span class="num">([^<]*)</span>', mp), "title": one(r'<h2>(.*?)</h2>', mp),
              "lead": one(r'<p class="sec-lead">(.*?)</p>', mp), "cards": []}
    exams = []
    for cls, head, eb in re.findall(r'<div class="ecard (e\d)"><div class="eh">(.*?)</div><div class="eb">\n(.*?)</div></div>', mp, re.S):
        lines = re.findall(r'      <p(?: class="exday")?>(.*?)</p>', eb)
        exday = re.search(r'<p class="exday">(.*?)</p>', eb)
        card = {"cls": cls, "head": head, "lines": [l for l in lines if not exday or l != exday.group(1)]}
        if exday:
            card["examDay"] = exday.group(1)
            dm = re.search(r'(\d{1,2}) ([A-Z][a-z]+) (\d{4})', T(exday.group(1)))
            if dm:
                try:
                    d = date(int(dm.group(3)), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(dm.group(2)[:3]) + 1, int(dm.group(1)))
                    exams.append({"label": T(head), "date": d.isoformat()})
                except ValueError:
                    pass
        mapsec["cards"].append(card)
    man["calendar"]["exams"] = exams
    man["map"] = mapsec

    # ---- labels held in the JS
    labels["thisWeek"] = js_str_lit(src, r's\.textContent=')
    labels["copied"] = js_str_lit(src, r'btn\.textContent=')
    labels["copyPrompt"] = js_str_lit(src, r'prompt\(')
    labels["toastCopied"] = concat_pattern(one(r'toast\(((?:"[^"]*"|btn\.dataset\.w|\+)+)\);', src), {"btn.dataset.w": "%W%"})
    labels["toastPlaying"] = concat_pattern(one(r'toast\(((?:"[^"]*"|c\.textContent|\+)+)\);', src), {"c.textContent": "%E%"})
    labels["progress"] = concat_pattern(one(r'txt\.textContent=(.*?);', src), {"done": "%D%", "boxes.length": "%N%"})
    labels["checkOk"] = js_str_lit(src, r'el\.innerHTML = ok\n        \? ')[:-len("</b><span>")].replace("<b>", "", 1)
    labels["checkOkOnline"] = js_str_lit(src, r'\(ONLINE\?')
    labels["checkOkLocal"] = js_str_lit(src, r'\(ONLINE\?"[^"]*":')
    labels["checkBad"] = js_str_lit(src, r'</span>"\n        : ')[:-len("</b><span>")].replace("<b>", "", 1)
    labels["checkBadOnline"] = js_str_lit(src, r'\(ONLINE\n            \? ')
    labels["checkBadNoBase"] = js_str_lit(src, r'location\.protocol\)\n               \? ')
    labels["checkBadLocal"] = js_str_lit(src, r'location\.protocol\)\n               \? "[^"]*"\n               : ')
    man["labels"] = labels
    return man


ORDER = ["schema", "meta", "theme", "files", "calendar", "how", "weeksSection", "weeks", "shelf", "map", "labels"]


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src = open(sys.argv[1], encoding="utf-8").read()
    man = extract(src)
    man = {k: man[k] for k in ORDER}
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("wrote %s: %d weeks" % (sys.argv[2], len(man["weeks"])))


if __name__ == "__main__":
    main()
