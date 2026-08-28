/* ------------------------------------------------------------------
   builder.js — author a weekly-page manifest in the browser, preview it
   live, and download either the manifest or the finished page.

   buildWeekly() and validate() here are TWIN PORTS of build() and
   validate() in build_weekly.py. Change one, change the other.
   ------------------------------------------------------------------ */
(function () {
"use strict";

var $ = function (id) { return document.getElementById(id); };
function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;"); }
function el(tag, attrs, html) {
  var n = document.createElement(tag);
  for (var k in (attrs || {})) n.setAttribute(k, attrs[k]);
  if (html != null) n.innerHTML = html;
  return n;
}

/* ============================ twin ports ============================ */

function buildWeekly(manifest, template) {
  var meta = manifest.meta || {};
  var blob = JSON.stringify(manifest).replace(/<\//g, "<\\/").replace(/<!--/g, "<\\!--");
  var out = template
    .split("%%TITLE%%").join(meta.title || "Weekly page")
    .split("%%DESCRIPTION%%").join(meta.description || "")
    .split("%%FONTS%%").join(meta.fonts || "")
    .split("%%NOINDEX%%").join(meta.noindex ? '<meta name="robots" content="noindex">' : "")
    .split("%%MANIFEST%%").join(blob);
  var left = out.match(/%%[A-Z_]+%%/g);
  if (left) throw new Error("unfilled tokens remain: " + left.join(", "));
  return out;
}

function validate(m) {
  var problems = [];
  ["meta", "calendar", "tracks", "weeks"].forEach(function (k) {
    if (!m[k]) problems.push("missing top-level key: " + k);
  });
  if (problems.length) return problems;

  var weeks = (m.calendar && m.calendar.weeks) || [];
  if (!weeks.length) problems.push("calendar.weeks is empty — a page needs at least one week");
  weeks.forEach(function (d, i) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(d))) problems.push("calendar.weeks[" + (i + 1) + "] is not YYYY-MM-DD: " + d);
  });

  var n = weeks.length;
  (m.calendar.terms || []).forEach(function (t) {
    if (!(t.from >= 1 && t.from <= t.to && t.to <= n)) problems.push('term "' + t.t + '" spans outside 1..' + n);
  });

  var keys = m.tracks.map(function (t) { return t.key; });
  keys.forEach(function (k, i) {
    if (keys.indexOf(k) !== i) problems.push("duplicate track key: " + k);
    if (!/^[a-z0-9]+$/.test(String(k))) problems.push("track key " + k + " must be lowercase letters/digits (it goes in the URL hash)");
    if (!m.weeks[k]) problems.push("track " + k + " has no entry in weeks");
  });

  var res = m.resources || {};
  Object.keys(m.weeks).forEach(function (track) {
    Object.keys(m.weeks[track]).forEach(function (num) {
      var d = m.weeks[track][num], where = track + " week " + num;
      if (parseInt(num, 10) > n) problems.push(where + " is beyond calendar.weeks (" + n + ")");
      ["wl", "cl", "r"].forEach(function (f) {
        (d[f] || []).forEach(function (rid) {
          if (!res[rid]) problems.push(where + ": " + f + " references unknown resource " + rid);
        });
      });
      ["video", "podcast"].forEach(function (s) {
        if (d[s] && !d[s].url) problems.push(where + ": " + s + " has no url");
      });
    });
  });

  (((m.library || {}).shelves) || []).forEach(function (sh) {
    (sh[1] || []).forEach(function (rid) {
      if (!res[rid]) problems.push('library shelf "' + sh[0] + '" references unknown resource ' + rid);
    });
  });
  return problems;
}

/* ============================ model ============================ */

var M = null;              // the manifest being edited
var page = "meta";
var wkTrack = null, wkNum = null;

function skeleton() {
  return {
    schema: "weekly-page/1",
    meta: {
      id: "new-course", title: "Course Week by Week",
      eyebrow: ["School name", "Course · Board"],
      standfirst: "One sentence on what this page is for.",
      hint: "Every week has its own address — use <b>Copy week link</b> on any card to send students straight to that week.",
      facts: [["Teaching weeks", "0"], ["Curriculum time", ""], ["Cohort", ""], ["Teacher", ""]],
      footer: ["School · Course"], siteUrl: "", description: "", noindex: true,
      labels: {
        weekWord: "Week", slotA: "Main lesson", slotB: "Second session",
        tasks: "Before the next session", logbook: "Record", also: "Also this week",
        supervisor: "Teacher notes", copyLink: "Copy week link", copied: "Link copied",
        copyManual: "Copy from the box", viewA: "Student", viewB: "Teacher",
        today: "This week", watch: "Watch", listen: "Listen",
        libraryTitle: "Where everything lives", libraryLede: "", gapsLabel: "Not available yet:",
        endcapTitle: "Weeks %A%–%B% · nothing scheduled",
        endcapBody: "This track finishes in week %L%. The remaining weeks belong to the other tracks — switch tabs above to see them.",
        endcapPoints: []
      },
      fonts: "https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Source+Sans+3:ital,wght@0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
    },
    theme: { light: {}, dark: {} },
    calendar: { weeks: [], terms: [], notes: {}, breaks: {}, shortWeeks: {} },
    files: { origin: "", prefix: "", base: "", officeParam: "?web=1", officeExt: ["pptx", "docx", "xlsx"], folderView: "", folderRoot: "" },
    resources: {},
    library: { shelves: [], folders: [], gaps: "" },
    tracks: [{
      key: "a", label: "Group A", count: "", name: "Group A", blurb: "Who this track is for and what its year looks like.",
      spine: [], accent: { ink: "#2F5E80", bg: "#E8F0F6", rule: "#BBD2E2", inkDark: "#84B6D8", bgDark: "#132534", ruleDark: "#25415A" }
    }],
    weeks: { a: {} }
  };
}

/* ---------- dates ---------- */
var MN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
var DAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
function iso(d) {
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
}
function parseISO(s) { var p = String(s).split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); }
function pretty(s) { var d = parseISO(s); return DAY[d.getDay()] + " " + d.getDate() + " " + MN[d.getMonth()]; }
function mondaysBetween(a, b) {
  var out = [], d = parseISO(a), end = parseISO(b);
  while (d.getDay() !== 1) d.setDate(d.getDate() + 1);      // snap forward to Monday
  while (d <= end) { out.push(iso(d)); d.setDate(d.getDate() + 7); }
  return out;
}

/* Term blocks are the authoring view of calendar.weeks: one row per term,
   first and last teaching Monday. Everything else is derived. */
function blocksFromManifest() {
  var w = M.calendar.weeks, t = M.calendar.terms || [];
  if (!w.length) return [{ t: "Term 1", first: "", last: "" }];
  if (!t.length) return [{ t: "Term 1", first: w[0], last: w[w.length - 1] }];
  return t.map(function (x) { return { t: x.t, first: w[x.from - 1], last: w[x.to - 1] }; });
}

function applyBlocks(blocks) {
  var weeks = [], terms = [], breaks = {}, prevLast = null, prevIdx = null;
  blocks.forEach(function (b) {
    if (!b.first || !b.last) return;
    var ms = mondaysBetween(b.first, b.last);
    if (!ms.length) return;
    if (prevLast) {
      // the gap between two term blocks is a break, hung off the last week before it
      var gapStart = parseISO(prevLast); gapStart.setDate(gapStart.getDate() + 7);
      var gapEnd = parseISO(ms[0]); gapEnd.setDate(gapEnd.getDate() - 3);   // preceding Friday
      var weeksOff = Math.round((parseISO(ms[0]) - gapStart) / 604800000);
      var old = M.calendar.breaks[prevIdx] || {};
      breaks[prevIdx] = {
        lbl: old.lbl || "Break",
        dt: pretty(iso(gapStart)) + " – " + pretty(iso(gapEnd)) + (weeksOff > 1 ? " · " + weeksOff + " weeks" : ""),
        msg: old.msg || "", warn: !!old.warn
      };
      if (!breaks[prevIdx].msg) delete breaks[prevIdx].msg;
      if (!breaks[prevIdx].warn) delete breaks[prevIdx].warn;
    }
    terms.push({ t: b.t || "Term", from: weeks.length + 1, to: weeks.length + ms.length });
    weeks = weeks.concat(ms);
    prevLast = ms[ms.length - 1];
    prevIdx = weeks.length;
  });
  M.calendar.weeks = weeks;
  M.calendar.terms = terms;
  M.calendar.breaks = breaks;
  var f = (M.meta.facts || []).find(function (x) { return /teaching weeks/i.test(x[0]); });
  if (f) f[1] = String(weeks.length);
}

/* ============================ panels ============================ */

function textField(label, value, oninput, help, tag) {
  var wrap = el("div", { "class": "field" });
  wrap.appendChild(el("label", null, esc(label)));
  var input = document.createElement(tag || "input");
  if (tag !== "textarea") input.type = "text";
  input.value = value == null ? "" : value;
  input.addEventListener("input", function () { oninput(input.value); touch(); });
  wrap.appendChild(input);
  if (help) wrap.appendChild(el("div", { "class": "help" }, help));
  return wrap;
}
function listField(label, arr, onchange, help) {
  return textField(label, (arr || []).join("\n"), function (v) {
    onchange(v.split("\n").map(function (x) { return x.trim(); }).filter(Boolean));
  }, help, "textarea");
}

var PANELS = {};

PANELS.meta = function (p) {
  var m = M.meta;
  p.appendChild(el("h2", null, "The page itself"));
  p.appendChild(el("div", { "class": "help" }, "Identity, the masthead, and every reusable label. Nothing here is course-specific in the code — it is all manifest."));

  p.appendChild(el("h3", null, "Identity"));
  p.appendChild(textField("Manifest id", m.id, function (v) { m.id = v; },
    "Used as the localStorage prefix for tick-boxes and as the output filename. Change it and everyone's ticks reset."));
  p.appendChild(textField("Page title", m.title, function (v) { m.title = v; }));
  p.appendChild(listField("Eyebrow (one line each)", m.eyebrow, function (v) { m.eyebrow = v; },
    "First line is bold. Sits above the headline."));
  p.appendChild(textField("Standfirst", m.standfirst, function (v) { m.standfirst = v; }, null, "textarea"));
  p.appendChild(textField("Hint under the facts", m.hint, function (v) { m.hint = v; },
    "HTML allowed. Leave empty to hide the line.", "textarea"));
  p.appendChild(textField("Canonical URL", m.siteUrl, function (v) { m.siteUrl = v; },
    "Where the page will be hosted. Every Copy-week-link button builds on this, so set it before sharing links."));
  p.appendChild(textField("Meta description", m.description, function (v) { m.description = v; }, null, "textarea"));

  var nx = el("div", { "class": "field" });
  var cb = el("input"); cb.type = "checkbox"; cb.checked = !!m.noindex;
  cb.addEventListener("change", function () { m.noindex = cb.checked; touch(); });
  var lb = el("label", { style: "display:flex;gap:8px;align-items:center;text-transform:none;font-size:14px;letter-spacing:0" });
  lb.appendChild(cb); lb.appendChild(document.createTextNode("Ask search engines not to index this page"));
  nx.appendChild(lb); p.appendChild(nx);

  p.appendChild(el("h3", null, "Facts strip"));
  p.appendChild(pairTable(m.facts, ["Label", "Value"], function () { touch(); }));

  p.appendChild(el("h3", null, "Footer"));
  p.appendChild(listField("Footer lines", m.footer, function (v) { m.footer = v; }));

  p.appendChild(el("h3", null, "Wording"));
  p.appendChild(el("div", { "class": "help" }, "Every fixed string on the page. %A% %B% %L% in the end-cap are the first empty week, the last week of the year, and the track's final week."));
  var L = m.labels, grid = el("div", { "class": "row two" });
  [["weekWord", "Week word"], ["slotA", "Session A heading"], ["slotB", "Session B heading"],
   ["tasks", "Tasks heading"], ["logbook", "Record line label"], ["also", "Spare resources heading"],
   ["supervisor", "Teacher panel heading"], ["viewA", "View A button"], ["viewB", "View B button"],
   ["today", "Jump button"], ["watch", "Video button"], ["listen", "Podcast button"],
   ["copyLink", "Copy link button"], ["copied", "Copied confirmation"],
   ["libraryTitle", "Library heading"], ["gapsLabel", "Gaps label"],
   ["endcapTitle", "End-cap title"], ["endcapBody", "End-cap body"]
  ].forEach(function (pair) {
    grid.appendChild(textField(pair[1], L[pair[0]], function (v) { L[pair[0]] = v; }));
  });
  p.appendChild(grid);
  p.appendChild(textField("Library intro (HTML allowed)", L.libraryLede, function (v) { L.libraryLede = v; }, null, "textarea"));
  p.appendChild(listField("End-cap bullet points", L.endcapPoints, function (v) { L.endcapPoints = v; }));
};

function pairTable(arr, heads, after) {
  var t = el("table");
  var thead = el("thead"), tr = el("tr");
  heads.concat([""]).forEach(function (h) { tr.appendChild(el("th", null, esc(h))); });
  thead.appendChild(tr); t.appendChild(thead);
  var tb = el("tbody"); t.appendChild(tb);
  function draw() {
    tb.innerHTML = "";
    arr.forEach(function (row, i) {
      var r = el("tr");
      row.slice(0, heads.length).forEach(function (cell, j) {
        var td = el("td"), inp = el("input");
        inp.type = "text"; inp.value = cell == null ? "" : cell;
        inp.addEventListener("input", function () { row[j] = inp.value; after(); });
        td.appendChild(inp); r.appendChild(td);
      });
      var td = el("td");
      var del = el("button", { "class": "small danger" }, "×");
      del.addEventListener("click", function () { arr.splice(i, 1); draw(); after(); });
      td.appendChild(del); r.appendChild(td); tb.appendChild(r);
    });
  }
  draw();
  var add = el("button", { "class": "small" }, "+ Add row");
  add.addEventListener("click", function () { arr.push(heads.map(function () { return ""; })); draw(); after(); });
  var box = el("div"); box.appendChild(t); box.appendChild(el("div", { style: "margin-top:8px" })).appendChild(add);
  return box;
}

PANELS.calendar = function (p) {
  p.appendChild(el("h2", null, "Calendar"));
  p.appendChild(el("div", { "class": "help" },
    "Give each term its first and last <b>teaching Monday</b>. Weeks are generated from those ranges, and the gaps between them become the breaks — so holidays are skipped rather than counted. This is the part that is easy to get wrong by hand."));

  var blocks = blocksFromManifest();
  var host = el("div");
  function drawBlocks() {
    host.innerHTML = "";
    blocks.forEach(function (b, i) {
      var c = el("div", { "class": "card" });
      var hd = el("div", { "class": "hd" });
      hd.appendChild(el("strong", null, "Term " + (i + 1)));
      hd.appendChild(el("span", { "class": "sp", style: "flex:1" }));
      var del = el("button", { "class": "small danger" }, "Remove");
      del.addEventListener("click", function () { blocks.splice(i, 1); drawBlocks(); });
      hd.appendChild(del); c.appendChild(hd);
      var row = el("div", { "class": "row three" });
      row.appendChild(textField("Term heading", b.t, function (v) { b.t = v; }));
      ["first", "last"].forEach(function (k) {
        var f = el("div", { "class": "field" });
        f.appendChild(el("label", null, k === "first" ? "First Monday" : "Last Monday"));
        var inp = el("input"); inp.type = "date"; inp.value = b[k] || "";
        inp.addEventListener("change", function () { b[k] = inp.value; drawBlocks(); });
        f.appendChild(inp);
        if (b[k]) f.appendChild(el("div", { "class": "help" }, pretty(b[k])));
        c.appendChild(row);
        row.appendChild(f);
      });
      var n = (b.first && b.last) ? mondaysBetween(b.first, b.last).length : 0;
      c.appendChild(el("div", { "class": "help" }, n + " teaching week" + (n === 1 ? "" : "s")));
      host.appendChild(c);
    });
  }
  drawBlocks();
  p.appendChild(host);

  var bar = el("div", { style: "display:flex;gap:8px;margin:4px 0 18px" });
  var add = el("button", { "class": "small" }, "+ Add term");
  add.addEventListener("click", function () { blocks.push({ t: "Term " + (blocks.length + 1), first: "", last: "" }); drawBlocks(); });
  var gen = el("button", { "class": "primary" }, "Generate weeks");
  gen.addEventListener("click", function () { applyBlocks(blocks); render(); touch(); });
  bar.appendChild(add); bar.appendChild(gen);
  p.appendChild(bar);

  var w = M.calendar.weeks;
  p.appendChild(el("h3", null, "Generated weeks (" + w.length + ")"));
  if (!w.length) {
    p.appendChild(el("div", { "class": "help" }, "None yet — fill the term dates above and press Generate weeks."));
    return;
  }
  var tbl = el("table", null,
    "<thead><tr><th>#</th><th>Week commencing</th><th>Note shown on the card</th><th>Ends</th></tr></thead>");
  var tb = el("tbody");
  w.forEach(function (d, i) {
    var n = i + 1, r = el("tr");
    r.appendChild(el("td", { "class": "mono" }, String(n)));
    r.appendChild(el("td", { "class": "mono" }, pretty(d) + " " + parseISO(d).getFullYear()));
    var td = el("td"), inp = el("input");
    inp.type = "text"; inp.value = M.calendar.notes[n] || "";
    inp.placeholder = "e.g. Term ends Thu 25 Mar";
    inp.addEventListener("input", function () {
      if (inp.value) M.calendar.notes[n] = inp.value; else delete M.calendar.notes[n];
      touch();
    });
    td.appendChild(inp); r.appendChild(td);
    var td2 = el("td"), sel = el("select");
    [["", "Fri"], ["3", "Thu"], ["2", "Wed"], ["1", "Tue"], ["0", "Mon"]].forEach(function (o) {
      var op = el("option"); op.value = o[0]; op.textContent = o[1];
      if (String(M.calendar.shortWeeks[n] == null ? "" : M.calendar.shortWeeks[n]) === o[0]) op.selected = true;
      sel.appendChild(op);
    });
    sel.addEventListener("change", function () {
      if (sel.value === "") delete M.calendar.shortWeeks[n]; else M.calendar.shortWeeks[n] = +sel.value;
      touch();
    });
    td2.appendChild(sel); r.appendChild(td2); tb.appendChild(r);

    if (M.calendar.breaks[n]) {
      var b = M.calendar.breaks[n], br = el("tr");
      var cell = el("td", { colspan: "4", style: "background:var(--surface-2)" });
      var g = el("div", { "class": "row three" });
      g.appendChild(textField("Break label", b.lbl, function (v) { b.lbl = v; }));
      g.appendChild(textField("Dates", b.dt, function (v) { b.dt = v; }));
      g.appendChild(textField("Warning note (optional)", b.msg, function (v) { b.msg = v || undefined; }));
      cell.appendChild(g);
      var wf = el("label", { style: "display:flex;gap:7px;align-items:center;text-transform:none;letter-spacing:0;font-size:13px" });
      var wc = el("input"); wc.type = "checkbox"; wc.checked = !!b.warn;
      wc.addEventListener("change", function () { b.warn = wc.checked || undefined; touch(); });
      wf.appendChild(wc); wf.appendChild(document.createTextNode("Show this break in the alert colour"));
      cell.appendChild(wf);
      br.appendChild(cell); tb.appendChild(br);
    }
  });
  tbl.appendChild(tb);
  p.appendChild(tbl);
};

PANELS.tracks = function (p) {
  p.appendChild(el("h2", null, "Tracks"));
  p.appendChild(el("div", { "class": "help" },
    "One tab per track. Use tracks when groups share a page but run on different clocks; a single-group course just has one. The key goes in the URL (<code>#key-w7</code>) so keep it short and lowercase."));
  M.tracks.forEach(function (t, i) {
    var c = el("div", { "class": "card" });
    var hd = el("div", { "class": "hd" });
    var sw = el("span", { "class": "swatch", style: "background:" + (t.accent.ink || "#ccc") });
    hd.appendChild(sw);
    hd.appendChild(el("strong", null, esc(t.label || t.key)));
    hd.appendChild(el("span", { "class": "pill" }, Object.keys(M.weeks[t.key] || {}).length + " weeks"));
    hd.appendChild(el("span", { style: "flex:1" }));
    if (M.tracks.length > 1) {
      var del = el("button", { "class": "small danger" }, "Remove");
      del.addEventListener("click", function () {
        if (!confirm("Remove track " + t.key + " and its " + Object.keys(M.weeks[t.key] || {}).length + " weeks?")) return;
        delete M.weeks[t.key]; M.tracks.splice(i, 1); render(); touch();
      });
      hd.appendChild(del);
    }
    c.appendChild(hd);
    var r1 = el("div", { "class": "row three" });
    r1.appendChild(textField("Key", t.key, function (v) {
      var old = t.key; v = v.toLowerCase().replace(/[^a-z0-9]/g, "");
      if (!v || v === old) return;
      M.weeks[v] = M.weeks[old] || {}; delete M.weeks[old]; t.key = v;
    }));
    r1.appendChild(textField("Tab label", t.label, function (v) { t.label = v; }));
    r1.appendChild(textField("Tab count badge", t.count, function (v) { t.count = v; }));
    c.appendChild(r1);
    c.appendChild(textField("Heading", t.name, function (v) { t.name = v; }));
    c.appendChild(textField("Blurb", t.blurb, function (v) { t.blurb = v; }, null, "textarea"));
    c.appendChild(el("label", null, "Key dates (shown right of the blurb)"));
    c.appendChild(pairTable(t.spine, ["What", "When"], touch));
    c.appendChild(el("label", { style: "margin-top:12px" }, "Accent colours"));
    var r2 = el("div", { "class": "row three" });
    [["ink", "Text / rules"], ["bg", "Background"], ["rule", "Border"]].forEach(function (k) {
      r2.appendChild(textField(k[1] + " (light)", t.accent[k[0]], function (v) { t.accent[k[0]] = v; sw.style.background = t.accent.ink; }));
    });
    c.appendChild(r2);
    var r3 = el("div", { "class": "row three" });
    [["inkDark", "Text / rules"], ["bgDark", "Background"], ["ruleDark", "Border"]].forEach(function (k) {
      r3.appendChild(textField(k[1] + " (dark)", t.accent[k[0]], function (v) { t.accent[k[0]] = v; }));
    });
    c.appendChild(r3);
    p.appendChild(c);
  });
  var add = el("button", null, "+ Add track");
  add.addEventListener("click", function () {
    var k = "t" + (M.tracks.length + 1);
    M.tracks.push({ key: k, label: "New track", count: "", name: "New track", blurb: "", spine: [],
      accent: { ink: "#2C6349", bg: "#E6F0EA", rule: "#B9D6C6", inkDark: "#7FC8A2", bgDark: "#132A20", ruleDark: "#204535" } });
    M.weeks[k] = {}; render(); touch();
  });
  p.appendChild(add);
};

PANELS.resources = function (p) {
  p.appendChild(el("h2", null, "Resources"));
  p.appendChild(el("div", { "class": "help" },
    "Every file the page can link to, once. Weeks then refer to them by id. <b>Path</b> is relative to the base below, or a full https:// URL."));

  var f = M.files;
  var g = el("div", { "class": "row two" });
  g.appendChild(textField("Origin", f.origin, function (v) { f.origin = v; }, "e.g. https://yourschool.sharepoint.com"));
  g.appendChild(textField("Site prefix", f.prefix, function (v) { f.prefix = v; }, "e.g. /sites/Subject/"));
  p.appendChild(g);
  p.appendChild(textField("Base folder", f.base, function (v) { f.base = v; }, "Prepended to every relative path."));
  var g2 = el("div", { "class": "row two" });
  g2.appendChild(textField("Office suffix", f.officeParam, function (v) { f.officeParam = v; }, "?web=1 opens Office files in the browser."));
  g2.appendChild(textField("Office extensions", (f.officeExt || []).join(", "), function (v) {
    f.officeExt = v.split(",").map(function (x) { return x.trim().toLowerCase(); }).filter(Boolean);
  }));
  p.appendChild(g2);

  p.appendChild(el("h3", null, "Files (" + Object.keys(M.resources).length + ")"));
  var tbl = el("table", null, "<thead><tr><th>id</th><th>Label</th><th>Path</th><th>Type</th><th>Button text</th><th></th></tr></thead>");
  var tb = el("tbody");
  function drawRows() {
    tb.innerHTML = "";
    Object.keys(M.resources).forEach(function (id) {
      var r = M.resources[id], tr = el("tr");
      function cell(val, set, w) {
        var td = el("td"), inp = el("input");
        inp.type = "text"; inp.value = val == null ? "" : val;
        if (w) inp.style.minWidth = w;
        inp.addEventListener("input", function () { set(inp.value); touch(); });
        td.appendChild(inp); return td;
      }
      tr.appendChild(cell(id, function (v) {
        if (!v || v === id || M.resources[v]) return;
        M.resources[v] = r; delete M.resources[id];
        Object.keys(M.weeks).forEach(function (t) {
          Object.keys(M.weeks[t]).forEach(function (n) {
            ["wl", "cl", "r"].forEach(function (fl) {
              var a = M.weeks[t][n][fl]; if (!a) return;
              for (var i = 0; i < a.length; i++) if (a[i] === id) a[i] = v;
            });
          });
        });
        (M.library.shelves || []).forEach(function (s) {
          for (var i = 0; i < s[1].length; i++) if (s[1][i] === id) s[1][i] = v;
        });
      }, "70px"));
      tr.appendChild(cell(r.label, function (v) { r.label = v; }, "150px"));
      tr.appendChild(cell(r.path, function (v) { r.path = v; }, "200px"));
      tr.appendChild(cell(r.type, function (v) { r.type = v.toUpperCase(); }, "55px"));
      tr.appendChild(cell(r.short, function (v) { r.short = v; }, "120px"));
      var td = el("td");
      var del = el("button", { "class": "small danger" }, "×");
      del.addEventListener("click", function () { delete M.resources[id]; drawRows(); touch(); });
      td.appendChild(del); tr.appendChild(td);
      tb.appendChild(tr);
    });
  }
  drawRows();
  tbl.appendChild(tb);
  p.appendChild(tbl);

  var add = el("button", { "class": "small", style: "margin-top:8px" }, "+ Add file");
  add.addEventListener("click", function () {
    var i = 1; while (M.resources["r" + i]) i++;
    M.resources["r" + i] = { label: "New file", path: "", type: "PPTX", short: "New file" };
    drawRows(); touch();
  });
  p.appendChild(add);

  p.appendChild(el("h3", null, "Bulk add"));
  p.appendChild(el("div", { "class": "help" }, "One file per line: <code>id | Label | path/to/file.pptx | Button text</code>. Type is taken from the extension."));
  var ta = el("textarea"); ta.placeholder = "u1 | Unit 1 · Managing the Project | Unit 1/EPQ_1_Managing_the_Project.pptx | Unit 1 deck";
  p.appendChild(ta);
  var bulk = el("button", { "class": "small", style: "margin-top:8px" }, "Add these");
  bulk.addEventListener("click", function () {
    ta.value.split("\n").forEach(function (line) {
      var c = line.split("|").map(function (x) { return x.trim(); });
      if (c.length < 3 || !c[0]) return;
      M.resources[c[0]] = {
        label: c[1], path: c[2],
        type: (c[2].split(".").pop() || "").toUpperCase().slice(0, 5),
        short: c[3] || c[1]
      };
    });
    ta.value = ""; render(); touch();
  });
  p.appendChild(bulk);
};

PANELS.weeks = function (p) {
  p.appendChild(el("h2", null, "Weeks"));
  if (!M.calendar.weeks.length) {
    p.appendChild(el("div", { "class": "help" }, "Set up the calendar first — there are no weeks to fill in yet."));
    return;
  }
  if (!wkTrack || !M.weeks[wkTrack]) wkTrack = M.tracks[0].key;

  var sel = el("select", { style: "max-width:280px;margin-bottom:12px" });
  M.tracks.forEach(function (t) {
    var o = el("option"); o.value = t.key; o.textContent = t.label + " (" + Object.keys(M.weeks[t.key] || {}).length + " weeks)";
    if (t.key === wkTrack) o.selected = true;
    sel.appendChild(o);
  });
  sel.addEventListener("change", function () { wkTrack = sel.value; wkNum = null; render(); });
  p.appendChild(sel);

  var nav = el("div", { "class": "wknav" });
  M.calendar.weeks.forEach(function (d, i) {
    var n = i + 1;
    var has = !!M.weeks[wkTrack][n];
    var b = el("button", { "class": has ? "has" : "" }, String(n));
    if (String(n) === String(wkNum)) b.setAttribute("aria-current", "true");
    b.title = pretty(d);
    b.addEventListener("click", function () { wkNum = n; render(); });
    nav.appendChild(b);
  });
  p.appendChild(nav);

  if (!wkNum) {
    p.appendChild(el("div", { "class": "help" }, "Pick a week above. Green outline = already written."));
    return;
  }

  var d = M.weeks[wkTrack][wkNum];
  if (!d) {
    var mk = el("button", { "class": "primary" }, "Add week " + wkNum + " to this track");
    mk.addEventListener("click", function () {
      M.weeks[wkTrack][wkNum] = { p: "", t: "", f: null, l: "", w: "", c: "", wl: [], cl: [], k: [], g: "", r: [], s: "", q: [], video: null, podcast: null };
      render(); touch();
    });
    p.appendChild(mk);
    return;
  }

  var hd = el("div", { "class": "card" });
  var h = el("div", { "class": "hd" });
  h.appendChild(el("strong", null, "Week " + wkNum + " · " + pretty(M.calendar.weeks[wkNum - 1])));
  h.appendChild(el("span", { style: "flex:1" }));
  var rm = el("button", { "class": "small danger" }, "Delete week");
  rm.addEventListener("click", function () { delete M.weeks[wkTrack][wkNum]; wkNum = null; render(); touch(); });
  h.appendChild(rm); hd.appendChild(h);

  var r1 = el("div", { "class": "row two" });
  r1.appendChild(textField("Phase chip", d.p, function (v) { d.p = v; }));
  r1.appendChild(textField("Deadline flag (blank = none)", d.f, function (v) { d.f = v || null; }));
  hd.appendChild(r1);
  hd.appendChild(textField("Week title", d.t, function (v) { d.t = v; }));
  hd.appendChild(textField("Lede", d.l, function (v) { d.l = v; }, null, "textarea"));
  p.appendChild(hd);

  var s1 = el("div", { "class": "card" });
  s1.appendChild(el("div", { "class": "hd" }, "<strong>" + esc(M.meta.labels.slotA || "Session A") + "</strong>"));
  s1.appendChild(textField("What happens", d.w, function (v) { d.w = v; }, null, "textarea"));
  s1.appendChild(idsField("Files opened in this session", d.wl, function (v) { d.wl = v; }));
  p.appendChild(s1);

  var s2 = el("div", { "class": "card" });
  s2.appendChild(el("div", { "class": "hd" }, "<strong>" + esc(M.meta.labels.slotB || "Session B") + "</strong>"));
  s2.appendChild(textField("What happens", d.c, function (v) { d.c = v; }, null, "textarea"));
  s2.appendChild(idsField("Files opened in this session", d.cl, function (v) { d.cl = v; }));
  p.appendChild(s2);

  var md = el("div", { "class": "card" });
  md.appendChild(el("div", { "class": "hd" }, "<strong>Video &amp; podcast</strong> <span class='pill'>optional</span>"));
  md.appendChild(el("div", { "class": "help" }, "Leave the URL blank and nothing shows. YouTube links are converted to privacy-mode embeds automatically; a podcast URL becomes an audio player."));
  ["video", "podcast"].forEach(function (kind) {
    var o = d[kind] || { url: "", label: "", mins: "" };
    var row = el("div", { "class": "row three" });
    row.appendChild(textField(kind + " URL", o.url, function (v) {
      o.url = v; d[kind] = v ? o : null;
    }));
    row.appendChild(textField("Button text", o.label, function (v) { o.label = v; if (d[kind]) d[kind] = o; }));
    row.appendChild(textField("Length", o.mins, function (v) { o.mins = v; if (d[kind]) d[kind] = o; }));
    md.appendChild(row);
  });
  p.appendChild(md);

  var tk = el("div", { "class": "card" });
  tk.appendChild(el("div", { "class": "hd" }, "<strong>" + esc(M.meta.labels.tasks || "Tasks") + "</strong>"));
  tk.appendChild(listField("One task per line", d.k, function (v) { d.k = v; }, "Each becomes a tick-box."));
  tk.appendChild(textField(M.meta.labels.logbook || "Record", d.g, function (v) { d.g = v; }, null, "textarea"));
  tk.appendChild(idsField("Other files worth having this week", d.r, function (v) { d.r = v; },
    "Anything already linked from a session box is filtered out automatically."));
  p.appendChild(tk);

  var sp = el("div", { "class": "card" });
  sp.appendChild(el("div", { "class": "hd" }, "<strong>" + esc(M.meta.labels.supervisor || "Teacher notes") + "</strong> <span class='pill'>second view only</span>"));
  sp.appendChild(textField("Note", d.s, function (v) { d.s = v; }, null, "textarea"));
  sp.appendChild(listField("Checkpoint chips (one per line)", d.q, function (v) { d.q = v; }));
  p.appendChild(sp);
};

function idsField(label, arr, set, help) {
  var wrap = el("div", { "class": "field" });
  wrap.appendChild(el("label", null, esc(label)));
  var box = el("div", { style: "display:flex;flex-wrap:wrap;gap:5px;margin-bottom:6px" });
  function draw() {
    box.innerHTML = "";
    (arr || []).forEach(function (id, i) {
      var r = M.resources[id];
      var b = el("button", { "class": "small", title: r ? r.label : "unknown resource" },
        esc(id) + " ×");
      if (!r) b.classList.add("danger");
      b.addEventListener("click", function () { arr.splice(i, 1); set(arr); draw(); touch(); });
      box.appendChild(b);
    });
  }
  draw();
  wrap.appendChild(box);
  var sel = el("select");
  sel.appendChild(el("option", { value: "" }, "add a file…"));
  Object.keys(M.resources).forEach(function (id) {
    sel.appendChild(el("option", { value: id }, esc(id + " — " + M.resources[id].label)));
  });
  sel.addEventListener("change", function () {
    if (!sel.value) return;
    arr.push(sel.value); set(arr); sel.value = ""; draw(); touch();
  });
  wrap.appendChild(sel);
  if (help) wrap.appendChild(el("div", { "class": "help" }, help));
  return wrap;
}

PANELS.library = function (p) {
  p.appendChild(el("h2", null, "Resource library"));
  p.appendChild(el("div", { "class": "help" }, "The shelves at the foot of the page. Leave everything empty and the whole section disappears."));
  var lib = M.library;
  lib.shelves.forEach(function (sh, i) {
    var c = el("div", { "class": "card" });
    var hd = el("div", { "class": "hd" });
    hd.appendChild(el("strong", null, esc(sh[0] || "Shelf")));
    hd.appendChild(el("span", { style: "flex:1" }));
    var del = el("button", { "class": "small danger" }, "Remove");
    del.addEventListener("click", function () { lib.shelves.splice(i, 1); render(); touch(); });
    hd.appendChild(del); c.appendChild(hd);
    c.appendChild(textField("Shelf heading", sh[0], function (v) { sh[0] = v; }));
    c.appendChild(idsField("Files on this shelf", sh[1], function (v) { sh[1] = v; }));
    p.appendChild(c);
  });
  var add = el("button", { "class": "small" }, "+ Add shelf");
  add.addEventListener("click", function () { lib.shelves.push(["New shelf", []]); render(); touch(); });
  p.appendChild(add);

  p.appendChild(el("h3", null, "Folder links"));
  p.appendChild(el("div", { "class": "help" }, "Label, subfolder (blank = root), badge text."));
  p.appendChild(pairTable(lib.folders, ["Label", "Subfolder", "Badge"], touch));
  p.appendChild(el("h3", null, "Gaps note"));
  p.appendChild(textField("What is missing", lib.gaps, function (v) { lib.gaps = v; },
    "Shown in a dashed box. Leave empty to hide.", "textarea"));
};

PANELS.json = function (p) {
  p.appendChild(el("h2", null, "Manifest JSON"));
  p.appendChild(el("div", { "class": "help" }, "The whole thing. Edit and press Apply, or copy it somewhere safe."));
  var ta = el("textarea"); ta.style.minHeight = "60vh"; ta.style.fontFamily = "ui-monospace,monospace";
  ta.style.fontSize = "12px";
  ta.value = JSON.stringify(M, null, 2);
  p.appendChild(ta);
  var bar = el("div", { style: "display:flex;gap:8px;margin-top:10px" });
  var apply = el("button", { "class": "primary" }, "Apply");
  apply.addEventListener("click", function () {
    try { M = JSON.parse(ta.value); render(); touch(); }
    catch (e) { alert("That is not valid JSON:\n\n" + e.message); }
  });
  bar.appendChild(apply);
  p.appendChild(bar);
};

/* ============================ shell ============================ */

function touch() {
  var problems = validate(M);
  var b = $("statBadge");
  b.className = "badge " + (problems.length ? "bad" : "ok");
  b.textContent = problems.length ? problems.length + " problem" + (problems.length > 1 ? "s" : "") : "valid";
  b.title = problems.join("\n");
  var weeks = Object.keys(M.weeks).reduce(function (a, k) { return a + Object.keys(M.weeks[k]).length; }, 0);
  $("prevBadge").textContent = M.tracks.length + " tracks · " + weeks + " weeks";
}

function render() {
  var p = $("panel");
  p.innerHTML = "";
  var problems = validate(M);
  if (problems.length) {
    var box = el("div", { "class": "problems" }, "<b>" + problems.length + " problem" + (problems.length > 1 ? "s" : "") + " — the page will still preview, but fix these before publishing:</b>");
    var ul = el("ul");
    problems.slice(0, 12).forEach(function (x) { ul.appendChild(el("li", null, esc(x))); });
    if (problems.length > 12) ul.appendChild(el("li", null, "…and " + (problems.length - 12) + " more"));
    box.appendChild(ul);
    p.appendChild(box);
  }
  PANELS[page](p);
  Array.prototype.forEach.call(document.querySelectorAll("#nav button"), function (b) {
    b.setAttribute("aria-current", b.getAttribute("data-p") === page ? "true" : "false");
  });
  touch();
}

function preview() {
  try {
    $("frame").srcdoc = buildWeekly(M, window.WEEKLY_TEMPLATE);
  } catch (e) {
    $("frame").srcdoc = "<pre style='padding:20px;font:13px monospace;color:#A62016'>" + esc(e.message) + "</pre>";
  }
}

function download(name, text, mime) {
  var blob = new Blob([text], { type: mime });
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a); a.click();
  setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

Array.prototype.forEach.call(document.querySelectorAll("#nav button"), function (b) {
  b.addEventListener("click", function () { page = b.getAttribute("data-p"); wkNum = wkNum; render(); });
});
$("btnPreview").addEventListener("click", preview);
$("btnSkeleton").addEventListener("click", function () {
  if (M && !confirm("Discard the manifest you are editing?")) return;
  M = skeleton(); page = "meta"; render(); preview();
});
$("loadFile").addEventListener("change", function (e) {
  var f = e.target.files[0]; if (!f) return;
  var fr = new FileReader();
  fr.onload = function () {
    try { M = JSON.parse(fr.result); page = "meta"; render(); preview(); }
    catch (err) { alert("Could not read that manifest:\n\n" + err.message); }
  };
  fr.readAsText(f);
  e.target.value = "";
});
$("btnManifest").addEventListener("click", function () {
  download((M.meta.id || "manifest") + ".json", JSON.stringify(M, null, 2), "application/json");
});
$("btnHtml").addEventListener("click", function () {
  var problems = validate(M);
  if (problems.length && !confirm(problems.length + " problem(s) remain:\n\n" + problems.slice(0, 8).join("\n") + "\n\nDownload anyway?")) return;
  download("index.html", buildWeekly(M, window.WEEKLY_TEMPLATE), "text/html");
});

if (!window.WEEKLY_TEMPLATE) {
  $("tplBadge").className = "badge bad";
  $("tplBadge").textContent = "template.js missing — run sync_template.py";
} else {
  $("tplBadge").textContent = "template " + (window.WEEKLY_TEMPLATE_HASH || "loaded");
}

M = skeleton();
render();
preview();
})();
