<!-- © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework, Weekly Page Kit (KS4 edition). All rights reserved. Harlington School deployment licensed for internal use. Not for reproduction or redistribution without written permission. -->
# QA report — Weekly Page Kit, KS4 edition

Date: 2026-09-03. Inputs: the three `year11-*.html` pages in `/home/claude/weekly/summit`
(unmodified; md5 `9743b822…` supported, `e6740719…` summit, `9f5387b8…` sumhclass).
Tooling: python3, beautifulsoup4 + lxml, Playwright 1.56 with the bundled Chromium.

## 1. Are the three pages one design?

Diffed before designing anything.

- **CSS**: the `<style>` block is byte-identical across the three pages. The
  template carries it verbatim, with one `%%THEME%%` token on the line before
  `</style>` (renders to nothing when `theme` is `{}`).
- **JS, script 1**: identical except for the course constants
  (`RESOURCE_BASE`, `PODCAST_BASE`, the `LINKS` key list, the two comment
  blocks, the `"y11_supported_ticks"` storage key) and **one behavioural
  difference**: the SumHclass page probes the first podcast with
  `fetch(…, {method:"HEAD"})` instead of an `<audio>` element. Parameterised
  as `files.selfCheck: "audio" | "fetch"` via two `%%IF%%` variant blocks in
  the template; no third template.
- **JS, script 2** (tripwire beacon): identical except the page path
  (`p:"summit/year11-….html"`) → `meta.tripwirePath`; endpoint and canonical
  host also lifted into `meta` so nothing deployment-specific stays in the
  template.
- **Body**: same skeleton; every difference is content (tier names, workbook
  file names, lesson summaries, the Summit/SumHclass `spec` references and
  per-week unit-page buttons with a fixed `href`).

## 2. Round-trip results

`python3 roundtrip.py` — extract each page → build from the manifest → compare.

| page | byte-identical (sha256) | DOM-identical | DOM nodes compared |
|---|---|---|---|
| year11-supported | yes — `41b22c5b9b4e7ea2…` | yes, 0 differences | 3 848 |
| year11-summit | yes — `36467d177e84f61a…` | yes, 0 differences | 4 030 |
| year11-sumhclass | yes — `74960a380929b81c…` | yes, 0 differences | 4 030 |

The DOM comparison (bs4/lxml) walks both trees depth-first and compares tag
name, the attribute set (order-independent, `class` tokens sorted), and text
after whitespace normalisation; comments are ignored; `<script>`/`<style>`
are compared as whole normalised text. Sensitivity was checked by mutating
one attribute in a copy (`w7_read` → `w7_reed`): reported as exactly one
difference at `/html/body/section[5]/…/article[8]/div[9]/label[3]/input[1]`.
A whitespace-only mutation is correctly ignored.

Because the pages come back byte-for-byte, the stronger claim holds too:
`build_ks4.py manifests/y11-<tier>.json` reproduces the live file exactly.

## 3. Counts — extracted vs rebuilt

Counted in the manifest (by `roundtrip.py`) and in the rebuilt HTML (bs4
selectors); the rebuilt counts equal the source counts on all three pages.

| | supported | summit | sumhclass |
|---|---|---|---|
| week cards `article.wk` | 33 | 33 | 33 |
| nav chips `a.nch` | 33 | 33 | 33 |
| teaching lessons `.les` | 28 | 28 | 28 |
| revision focuses `.les-rev` | 7 | 7 | 7 |
| podcast players `.pod` | 39 | 39 | 39 |
| episode chips `.pchip` | 36 | 36 | 36 |
| tick-boxes `input[data-t]` | 99 | 99 | 99 |
| resource buttons `a.res-btn` | 81 | 95 | 95 |
| elements with `data-sp` | 156 | 156 | 80 |
| `LINKS` entries | 120 | 120 | 120 |

Notes on the numbers: the 14 extra buttons on Summit/SumHclass are the
per-teaching-week unit-page links (`g9page_w*`), which carry a fixed `href`
and are therefore not in `LINKS` — the builder reproduces that rule
(`link_keys()`: every `.res-btn` without `href`, plus every `.pod`). SumHclass
has only 80 `data-sp` because its 39 players, 36 chips and the START HERE
button are served next to the page and carry no SharePoint path; the
manifest simply omits `sp` for them.

## 4. validate() refusals

Exercised against a copy of the Supported manifest with one fault injected
at a time; each was refused with a named error and nothing written:

missing top-level key · empty `calendar.weeks` · malformed date
(`31/08/2026`) · week count mismatch (32 vs 33) · duplicate week number ·
unknown week type (`teaching`) · lesson deck with empty path · podcast with
no path · episode chip with no path · shelf item with no path · unknown tick
set. Warnings only (build continues): a non-Monday date; an exam date outside
an `ex` week. `build_all.py` on a folder with one broken and one good
manifest built the good one, reported `1 built, 1 failed`, exit status 1.

## 5. Skeleton

`manifests/_skeletons/blank-course.json` builds (3 weeks, 7 LINKS keys, no
warnings) and passes validation. Its `_`-prefixed comment keys are ignored
by the builder (checked: none of them leak into the CSS `:root` override or
the `LINKS` object).

## 6. Playwright smoke test of a rebuilt page

`python3 build_all.py manifests <site>`, `Podcast_Audio` linked in beside the
pages, served with `python3 -m http.server`, driven with `smoke_ks4.py` in
headless Chromium (`/opt/pw-browsers/chromium…/chrome`, 1280×900).

`y11-supported.html` — 14/14:

- page loads with the right title; **no JS exceptions; no console errors**
  (see caveat below on resource-load messages)
- 33 `article.wk` cards, 33 nav chips
- clicking chip 20 scrolls to `#w20` (card top 180px, sticky nav bottom
  49px) and the scrollspy marks chip 20 `.on`
- ticking `w20_read` updates the nav to `1 of 99 ticked`; after a reload
  the box is still ticked; `localStorage` holds `y11_supported_ticks`
- opening `…#w7` lands on week 7 (top 180px, below the nav) and the card
  carries the `target` flash class
- the copy-link button reacts (clipboard permission granted to the context)
- the self-check pill appears (red here: SharePoint unreachable from the sandbox)

`y11-sumhclass.html` (the `fetch` self-check variant) — 14/14, pill green,
since its podcasts are served next to the page.

**Why 180px and not flush under the nav:** `html{scroll-padding-top:88px}`
and `.wk{scroll-margin-top:92px}` are additive. This is the source pages'
behaviour, not a regression; the test asserts "below the sticky nav and in
view" rather than a pixel.

## 7. What I could not verify, and other caveats

- **Network.** The sandbox blocks `hs365.sharepoint.com` and the tripwire
  endpoint, so the console shows `Failed to load resource:
  net::ERR_TUNNEL_CONNECTION_FAILED` for the SharePoint podcast probe and
  the beacon. These are logged and excluded from the "no console errors"
  check; genuine JS errors (`pageerror`) were zero. Whether the SharePoint
  paths actually resolve, and whether `?web=1` opens the Office files as
  intended, cannot be checked from here.
- **Shared storage key.** All three source pages save ticks under
  `y11_supported_ticks`; the manifests reproduce that (`meta.id` is
  `y11_supported` on all three) because byte-identity was the target. It is
  almost certainly unintended for the Summit and SumHclass tiers — a student
  who opens two tiers in one browser shares ticks between them. Changing
  `meta.id` per tier is a one-word edit but resets existing ticks, so it is
  flagged rather than done.
- **The "156 buttons and players" sentence** in `shelf.note` is literal text
  in the extracted manifests (it matches: 81 + 39 + 36). New manifests can
  write `%MEDIA%` and the builder substitutes the live count.
- **`calendar.exams`** is derived by the extractor from the exam map's red
  `examDay` lines ("Thursday 13 May 2027"); it renders nothing and only feeds
  a validation warning. It is correct for these pages (13 May → week 31,
  21 May → week 32, both `ex`), but the parse is by pattern and should be
  eyeballed on a new course.
- **Escaping convention.** Week-card fields are plain text and re-escaped
  with `html.escape()` — the same function that produced the source, which is
  why `'` comes back as `&#x27;`. Hand-written blocks are HTML fragments
  inserted verbatim. If a future author types a `"` in a week-card field it
  renders as `&quot;`, which is correct HTML but not something the source
  pages ever contained, so it is untested by the round-trip.
- **Not a browser builder.** Unlike the EPQ kit there is no `builder.html`;
  rendering is Python-only (chosen for exact byte round-trip and because a
  single generator cannot drift from a twin). Authoring is by editing JSON.
- The kit's own copyright notice sits on line 1 of the template as an HTML
  comment; `build_ks4.py` strips that one line so built pages stay identical
  to the originals. The source pages' own authorship comment (lines 2–18)
  is part of the page and is kept.
