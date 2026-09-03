<!-- © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework, Weekly Page Kit (KS4 edition). All rights reserved. Harlington School deployment licensed for internal use. Not for reproduction or redistribution without written permission. -->
# Weekly Page Kit — KS4 edition

The "Year 11 RS · Week by Week" page — thirty-three cards, one per Monday,
each carrying the week's two lessons, the podcast to press play on, the
Companion page to read, the key words and quote to learn, and three tick-boxes
— reduced to a **manifest** plus a **generator**. Change the JSON, rebuild,
publish. The design lives in one template and is never edited to change a
word.

Built from the three Year 11 tiers (Supported, Summit · Grade 9, SumHclass
grade) and generalised: any KS4 course on a weekly clock can use it. The KS4
twin of the EPQ weekly kit.

---

## The five-minute version

```
python3 build_ks4.py manifests/y11-summit.json site/year11-summit.html
open site/year11-summit.html
```

To rebuild every tier at once:

```
python3 build_all.py manifests site
```

To prove nothing has drifted (do this after any edit to the template or the
Python):

```
python3 roundtrip.py
```

which extracts each of the three source pages to a manifest, builds it back,
and prints `PASS`/`FAIL` per page — `byte:identical` is what you should see.

---

## What is in here

| file | what it does |
|---|---|
| `template.ks4weekly.html` | the master page: the source pages' CSS and JS, unchanged, with `%%TOKENS%%` where content goes; no course content |
| `build_ks4.py` | one manifest → one page, with `validate()` — refuses to write a broken page |
| `build_all.py` | a folder of manifests → a folder of pages; skips `_`-prefixed folders; non-zero exit on failure, so it works in CI |
| `extract_ks4.py` | one existing page → one manifest (how the three manifests below were made) |
| `roundtrip.py` | extract → build → compare, byte and DOM, for the three source pages |
| `smoke_ks4.py` | serves a built folder and drives one page in headless Chromium: cards, chips, ticks, deep link |
| `schema.md` | the manifest, field by field, with the traps called out |
| `manifests/y11-supported.json` | the Supported tier, 33 weeks, 81 buttons, 39 players, 36 chips |
| `manifests/y11-summit.json` | the Summit · Grade 9 tier |
| `manifests/y11-sumhclass.json` | the SumHclass grade tier |
| `manifests/_skeletons/blank-course.json` | empty but correctly shaped — one tier, three weeks (a teaching week with two lessons, a revision week, an exam week), one podcast wired. Copy this to start. |
| `sources/` | the three live Year 11 pages the kit was proven against — `roundtrip.py` reads them |
| `qa_report.md` | what was verified, and how |

### Two rules that keep the kit honest

1. **Weeks are literal Mondays.** `calendar.weeks` is an explicit list of
   dates with the holidays already taken out — never a first Monday plus a
   counter. Every date on the page, and the THIS WEEK badge, comes from that
   list. `validate()` warns if a date is not a Monday.
2. **Run `roundtrip.py` after any template edit.** The template is the three
   source pages' CSS and JS verbatim. If the round-trip stops reporting
   `byte:identical` you have changed the design for every page that will ever
   be built from it — which is either exactly what you meant, or a mistake
   you would otherwise find in a classroom.

---

## What the page does

- **Thirty-three cards, six phases.** Teaching, revision, mock, feedback,
  practice and exam weeks each get a colour, a badge and a chip in the sticky
  nav strip. The strip highlights the card you are looking at and scrolls
  itself sideways to keep up — sideways only, never the page.
- **Three things a week.** Listen, read, practise. Each card carries the
  podcast players, the Companion page and workbook buttons, and three
  tick-boxes; a progress bar in the nav counts them.
- **One address puts it online.** Every button and player carries a local
  path and a SharePoint path. `files.resourceBase` re-points all of them at
  once; `files.links` overrides one. Office files get `?web=1` so they open
  in the browser; a pill in the corner confirms the files can be reached.
- **Deep links.** `#w7` opens the page at week 7 and flashes it. Every card
  has a copy-link button.
- **Tick-boxes** persist per browser via `localStorage`, keyed on `meta.id`.

---

## Starting a new course

1. Copy `manifests/_skeletons/blank-course.json` to `manifests/<course>-<tier>.json`.
2. Fill in `meta`, then `calendar.weeks` from the school calendar — one
   Monday per teaching week, holidays removed — then `terms` and `holidays`.
3. Write the weeks. A teaching week is `lessons[]`; a revision week is
   `focuses[]` (+ `episodes[]`); a mock, feedback or exam week is a
   `checklist`; a practice week is `activities[]`. The card assembles itself.
4. `python3 build_ks4.py manifests/<course>-<tier>.json site/<page>.html`,
   read the warnings, open the page.
5. Set `meta.siteUrl` to where the page will actually live *before* anyone
   shares a link, and give each tier its own `meta.id`.

---

## Publishing

The output is one self-contained HTML file: no fonts to fetch, no
dependencies, no server requirement. The only external requests are whatever
`resourceBase` / `podcastBase` point at and the re-host beacon. Drop it on
GitHub Pages next to `Podcast_Audio/`, or on a school web server.

Rebuilding the three Year 11 pages in place (the manifests are named
`y11-*`, the live pages `year11-*`, so name the outputs explicitly):

```
python3 build_ks4.py manifests/y11-supported.json ../summit/year11-supported.html
python3 build_ks4.py manifests/y11-summit.json    ../summit/year11-summit.html
python3 build_ks4.py manifests/y11-sumhclass.json ../summit/year11-sumhclass.html
```

Today those three commands reproduce the live files byte-for-byte.
