# Weekly Page Kit

A weekly task page — the kind where each week of the year is a card carrying
what happens in the room, what students do before the next session, what gets
recorded, and the files each session opens — reduced to a **manifest** plus a
**generator**. Change the JSON, rebuild, publish. The design lives in one
template and is never edited to change a word.

Built for the Harlington EPQ page and generalised: any course on a weekly clock
can use it. The KS5/KS4 twin of the Design Summit kit, for weekly rather than
unit pages.

---

## The five-minute version

```
python3 build_weekly.py manifests/epq/epq-2026-27.json site/index.html
open site/index.html
```

To author without touching JSON by hand, open **`builder.html`** in a browser:
load a manifest, edit it in forms, watch the live preview, download the manifest
or the finished page. No Python, no server, no install.

---

## What is in here

| file | what it does |
|---|---|
| `template.weekly.html` | the master page: design and behaviour, five `%%TOKENS%%`, no course content |
| `build_weekly.py` | one manifest → one page, with validation |
| `build_all.py` | a folder of manifests → a whole site; non-zero exit on failure, so it works in CI |
| `builder.html` / `builder.js` | the browser authoring tool |
| `template.js` | the template packaged for the browser — **generated** |
| `sync_template.py` | regenerates `template.js`; run it after every template edit |
| `schema.md` | the manifest, field by field, with the traps called out |
| `manifests/epq/epq-2026-27.json` | the worked example: the real EPQ year, 3 tracks, 38 weeks, 74 week entries, 36 files |
| `manifests/_skeletons/blank-course.json` | empty but correctly shaped — copy this to start |

### Two rules that keep the kit honest

1. **`build()` in `build_weekly.py` and `buildWeekly()` in `builder.js` are twin
   ports**, as are the two `validate()` functions. Change one, change the other.
   They are short and deliberately boring so that staying in step is easy.
2. **Run `sync_template.py` after editing the template.** Otherwise the browser
   builder quietly keeps generating pages from the previous design — the badge
   in its header shows which template hash it loaded, which is how you catch it.

---

## What the page does

- **Tracks.** One tab per group. Use several when groups share a page but run on
  different clocks — the EPQ page carries three, whose deadlines are months
  apart. A single-group course has one track and nothing looks different.
- **Two views.** A student view and a second view (teacher, supervisor, whatever
  `labels.viewB` says) that adds a delivery note and checkpoint chips per week.
- **Per-session file buttons.** Each session box links straight to the deck or
  document that session runs on. Leftover resources fall through to a filtered
  "also this week" row, so nothing appears twice on a card.
- **Optional video and podcast per week.** Both independent, both optional.
  Nothing loads until pressed — 38 weeks of video does not mean 38 iframes — and
  opening one closes the other. YouTube links become `youtube-nocookie` embeds
  automatically.
- **Deep links.** `#<track>-w<n>` opens a specific week on a specific track,
  scrolls to it and flashes it. Every card has a copy-link button.
- **Tick-boxes** persist per browser via `localStorage`, keyed on `meta.id`.
- **Light and dark**, both designed, following the reader's system setting.

---

## Two traps worth knowing before you author a year

**Weeks are a list of dates, not a start plus a counter.** `calendar.weeks` is
an explicit list of teaching Mondays with holidays already removed. The first
version of the EPQ page computed `firstMonday + 7×(n−1)` and every week after
the first holiday was silently wrong — week 20 showed 18 January instead of 22
February, and the page looked perfectly fine. The builder's Calendar panel takes
one first and last Monday per term and generates the list, the term indices and
the breaks between them. Use it.

**Deep links need re-anchoring after web fonts load.** The template already
handles this. If you fork the scroll logic, keep it: the first jump lands before
Newsreader and Source Sans arrive, the swap reflows the page, and the target
slides out of view — which reads as "the deep link is broken" when it fired
correctly.

---

## Starting a new course

1. Copy `manifests/_skeletons/blank-course.json` to `manifests/<course>/<id>.json`.
2. Open `builder.html`, load it, and work down the panels: **Page** → **Calendar**
   → **Tracks** → **Resources** → **Weeks**.
3. Set `meta.siteUrl` to where the page will actually live *before* anyone shares
   a link — every copy-link button is built from it.
4. `python3 build_all.py manifests/<course> site` and publish `site/`.

`meta.id` is the `localStorage` prefix for tick-boxes. Changing it after students
have started resets their ticks, so choose it once.

---

## Publishing

The output is one self-contained HTML file with no build step, no dependencies
and no server requirement — the only external requests are the Google Fonts
stylesheet and whatever your resource links point at. Drop it on GitHub Pages,
a school web server, or anywhere that serves a file.

The EPQ page runs from `vmcssse-ui/epq` on GitHub Pages: `index.html` at the
repo root, this kit in `kit/`. Rebuilding it is one command:

```
python3 build_weekly.py manifests/epq/epq-2026-27.json ../index.html
```
