<!-- © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework, Weekly Page Kit (KS4 edition). All rights reserved. Harlington School deployment licensed for internal use. Not for reproduction or redistribution without written permission. -->
# KS4 weekly page manifest — schema

`schema: "ks4-weekly/1"`

One manifest describes one page — one tier of one course, one year. The
template supplies the design and the behaviour; the manifest supplies every
word, date, link, label and colour. Nothing about a particular course is
hard-coded in `template.ks4weekly.html`: if you find yourself editing the
template to change wording, the wording belongs in `labels` instead.

```
python3 build_ks4.py manifests/y11-summit.json site/year11-summit.html
```

Rendering is server-side (Python). The three Year 11 pages rebuild from their
manifests **byte-for-byte**, which is the guarantee `roundtrip.py` checks.

---

## Top level

| key | required | what it is |
|---|---|---|
| `schema` | ● | `"ks4-weekly/1"` |
| `meta` | ● | identity, masthead, footer, deployment |
| `theme` | ● | CSS custom-property overrides (may be `{}`) |
| `files` | ● | where the files live: bases, LINKS overrides, self-check probe |
| `calendar` | ● | the week spine: Mondays, terms, holidays, exam days |
| `how` | ● | the three-step routine section |
| `weeksSection` | ● | the heading and lead of the weeks section |
| `weeks` | ● | one entry per week |
| `shelf` | ● | the resource grid at the foot |
| `map` | ● | the exam-shape cards |
| `labels` | ● | every fixed string on the page, HTML and JS |

Any key that starts with `_` anywhere in the file is a comment and is
ignored — the skeleton uses them to explain itself.

### Text or HTML?

Two conventions, and it matters which a field follows:

* **text** — plain text. The builder escapes it (`'` → `&#x27;`, `&` → `&amp;`).
  Never put tags in a text field; they will show up as tags.
* **html** — inserted verbatim. Tags (`<b>`, `<code>`) and named entities
  (`&#183;`, `&#8211;`) are allowed and pass straight through. Write `&amp;`
  for an ampersand.

Everything inside `weeks[]`, and every `label`/`sub` on a resource button,
is **text**. The hand-written blocks (hero, section leads, shelf note, exam
map, footer, the four JS self-check messages) are **html**. Each field below
says which.

---

## meta

```jsonc
"meta": {
  "id": "y11_supported",           // localStorage prefix: ticks are saved under id + "_ticks".
                                   // Choose it once. Changing it resets every student's ticks.
  "title": "Year 11 RS · Week by Week · Supported",   // text — <title>
  "tier": "Supported",             // informational; the tier name
  "description": "",               // text — <meta name=description>; empty = no tag
  "noindex": false,                // true adds <meta name=robots content=noindex>
  "homeLink": { "href": "index.html#year11",
                "html": "◂ <b>Harlington RE</b> · all course pages" },   // html — the home strip
  "eyebrow": ["Exam board line", "School &#183; Year 11 &#183; 2026&#8211;27"],  // html, two lines by the crest
  "pill": "Supported edition",     // html — the amber pill
  "h1": "Your year, week by week", // html
  "tagline": "listen &#183; read &#183; practise",  // html
  "sub": "One paragraph under the title.",          // html
  "facts": [["13 May", "Paper 1 &#183; Christianity"], …],   // html — the four hero tiles, [big, small]
  "footer": ["left line", "right line (amber)"],    // html
  "siteUrl": "",                   // final public address; see below
  "tripwirePath": "summit/year11-supported.html",   // identifies this page in the re-host beacon
  "tripwireEndpoint": "https://…/e",                // beacon endpoint, framework-issued; keep as extracted
  "canonicalHost": "vmcssse-ui.github.io"           // the host the page is meant to live on
}
```

**`siteUrl`.** Every *Copy week link* button builds its URL from it. Empty
means the page uses `location.href` — correct once the page sits at its
final address, wrong the moment it is embedded, proxied or moved. Set it
before anyone shares a link.

**`id` is shared across the three Year 11 tiers as shipped** (`y11_supported`
on all three). That is how the source pages were built, and the manifests
reproduce it faithfully; it means a student who opens two tiers in one
browser sees the same ticks on both. For a new course give each tier its own
id.

---

## theme

Optional overrides of the template's CSS custom properties. Keys are token
names without the `--`. `{}` keeps the template palette.

```jsonc
"theme": { "amber": "#C9A227", "p1": "#3E1163" }
```

Rendered as one extra `:root{…}` rule at the end of the stylesheet, so it
wins over the defaults without the stylesheet changing. Tokens available:
`ink ink-2 mint mint-2 amber amber-soft p1 p2 red slate teal paper line lead
muted sans or-soft or-line or-rule or-ink or-body or-mid or-mid-line or-deep
or-hover`.

---

## files

```jsonc
"files": {
  "resourceBase": "https://hs365.sharepoint.com/sites/…/Year%2011",   // RESOURCE_BASE
  "podcastBase":  "https://hs365.sharepoint.com/sites/…/Podcast_Audio", // PODCAST_BASE ("" = under resourceBase)
  "podcastFolder": "Podcast_Audio",   // the folder name the JS looks for inside data-sp
  "folderName": "Year 11",            // named in the JS comment only
  "setupNote":   ["   ONE LINE TO PUT THIS PAGE ONLINE", "   ----", …],   // the comment block above RESOURCE_BASE, verbatim lines
  "podcastNote": ["line", "line"],    // the comment above PODCAST_BASE
  "selfCheck": "audio",               // "audio" | "fetch" — see below
  "links": {}                         // one-off URL overrides by key: {"deck_MLD_L01": "https://…"}
}
```

**How a button finds its file.** Every button and player carries three
things: a `key`, a `rel` (path relative to the page, used on the classroom
machine) and an `sp` (path inside the uploaded folder, used online). At load
the page resolves each in this order:

1. a URL in `LINKS[key]` — a one-off override, from `files.links`;
2. `resourceBase + "/" + sp` — the whole page at once; anything under
   `podcastFolder/` is re-pointed to `podcastBase` instead;
3. `rel` — the copy next to the page.

**The `?web=1` rule.** In step 2, and only there, a path ending
`.pptx .docx .xlsx .ppt .doc .xls` gets `?web=1` appended so SharePoint opens
it in the browser rather than downloading it. Nothing else gets it: not
podcasts, not HTML pages, not overrides from `links`, not local `rel` paths.
Do not put `?web=1` in a manifest path yourself.

**`LINKS` is generated.** The `const LINKS = {…}` object in the page lists
every resource button that has no fixed `href`, plus every podcast player,
sorted, each `""` unless `files.links` gives it a value. Episode chips are not
listed (they follow the same resolve order but were never overridable in the
source and are not now).

**`selfCheck`.** The page probes the first podcast to show the green/red pill.
`"audio"` loads it through an `<audio>` element — right when the podcasts are
on SharePoint. `"fetch"` sends a HEAD request — right when the podcasts sit
next to the page on a plain web server (the SumHclass page), because a
background-tab `<audio>` probe is throttled and used to show a false red
pill. This is the only JS that differs between the three source pages, and it
is selected by this one field.

---

## calendar

```jsonc
"calendar": {
  "weeks": ["2026-08-31", "2026-09-07", …],        // 33 literal Mondays, holidays ALREADY REMOVED
  "terms":    [{ "label": "Autumn 1", "from": 1 }, { "label": "Autumn 2", "from": 9 }],
  "holidays": [{ "before": 9,  "label": "Half term · 26–30 October 2026" },
               { "before": 34, "label": "Half term · 31 May – 4 June 2027" }],
  "exams":    [{ "label": "Paper 1 · Religion and Ethics — Christianity", "date": "2027-05-13" }]
}
```

**`weeks` is a literal list of Mondays, not a start date plus a counter.**
This is the single most important thing in the schema. Week 9 is 2 November
because week 8 is 19 October and half term is in between; a page that
computed `firstMonday + 7×(n−1)` would date every week after the first
holiday wrongly and look perfectly fine. `data-iso` on each card, the printed
date, and the THIS WEEK badge all come from this list. `validate()` warns on
any date that is not a Monday.

`terms[].from` is the week number a term band is printed before. `holidays[]
.before` is the week number a holiday divider is printed before; the
divider goes *after* the term band when both fall on the same week, and
`before: weeks+1` puts a divider after the last card. Labels are **text**;
the ◆ glyph is added by the template (`labels.holidayGlyph`).

`exams` is informational: nothing renders from it, but `validate()` warns if
an exam date does not fall inside a week of type `ex`. The extractor fills it
from the exam map's `examDay` lines.

---

## how · weeksSection · shelf · map — the section frames

Each has `num` (the "01" tag), `title` and `lead` — all **html**.

```jsonc
"how": { "num": "01", "title": "Three things, every week", "lead": "…",
         "steps": [{ "title": "Listen", "body": "…", "note": "…" }, …] }   // html; numbered 1..n

"weeksSection": { "num": "02", "title": "The thirty-three weeks", "lead": "… <b>Copy week link</b> …" }

"shelf": { "num": "03", "title": "…", "lead": "…",
           "note": "<b>Teacher setup:</b> … re-points all %MEDIA% buttons and players. …",   // html; %MEDIA% = live count
           "columns": [{ "cls": "g1", "eyebrow": "Your shelf", "title": "Workbooks — Supported edition",
                         "items": [ resource, … ] }],       // cls g1|g2|g3 picks the header gradient
           "wide":    [ resource, … ] }                     // the full-width buttons under the grid

"map": { "num": "04", "title": "…", "lead": "…",
         "cards": [{ "cls": "e1", "head": "Paper 1 &#183; …",                 // html; cls e1|e2 picks the colour
                     "lines": ["Q1 … &#183; Q4 …", "Every question: …", "1 hour 45 minutes …"],
                     "examDay": "Thursday 13 May 2027 &#183; morning" }] }  // red line; omit for none
```

The extracted manifests carry the literal "156" in `shelf.note` because the
source pages do; write `%MEDIA%` in a new manifest and the builder keeps the
count right (buttons + players + episode chips).

---

## resource

The one shape used everywhere a file is linked — lesson decks, per-week
reads, shelf columns, wide buttons:

```jsonc
{ "key": "deck_MLD_L01",                          // unique; the LINKS key and the override handle
  "rel": "../1%20-%20Mock%20Exam%20Lessons/MLD_L01_Origins_of_the_universe.pptx",  // path next to the page
  "sp":  "Year%2011/1%20-%20Mock%20Exam%20Lessons/MLD_L01_Origins_of_the_universe.pptx", // path inside the uploaded folder; omit = never online
  "href": "SH_MOLD_Ecosystem.html",               // optional fixed link; a button with href is left out of LINKS
  "localonly": true,                              // optional; hidden once RESOURCE_BASE is set (SharePoint will not run a page)
  "icon": "&#9635;",                              // html; the glyph in the square
  "label": "Open the lesson",                     // text
  "sub": "MLD_L01_Origins_of_the_universe.pptx" } // text, small line; omit for none
```

Paths are written exactly as they should appear in the attribute — already
percent-encoded, no `?web=1`. Glyphs in use: `&#9635;` ▣ deck · `&#9632;` ■
workbook · `&#9670;` ◆ companion · `&#9679;` ● kit / sheet · `&#9654;` ▶
audio · `&#9968;` ⛰ another page.

---

## weeks

One entry per calendar week, `n` running 1…N without gaps. The card's body is
assembled from whichever optional blocks are present, always in this order:
lessons/focuses → checklist → activities → podcasts → podnote → episodes →
reads → ticks. The `type` sets the phase colour and label; it does not
restrict which blocks you may use.

| `type` | colour | label (from `labels.phases`) | typical blocks |
|---|---|---|---|
| `teach` | purple | Lessons | lessons, podcasts, reads |
| `rev` | amber | Revision | focuses, podcasts, episodes, reads |
| `mock` | red | Mock exam | checklist |
| `fb` | slate | Feedback | checklist |
| `ret` | teal | Practice | activities, reads |
| `ex` | ink | The real exam | checklist |

```jsonc
{
  "n": 1,
  "type": "teach",
  "paper": "p1",                    // chip; key into labels.papers. Omit for no chip.
  "title": "Matters of Life and Death",     // text
  "say":   "One or two sentences to the student.",   // text
  "lessons": [{
      "title": "Origins of the universe",
      "bq": "Where did everything come from?",       // the Big question
      "spec": "1.4.1",                 // optional; shown faintly after bq as "· spec 1.4.1"
      "sum": ["Paragraph one.", "Paragraph two."],   // the orange summary box
      "deck": resource,                // the slim orange button; validated to have a path
      "kws": ["Big Bang", "creation", "commodity", "stewardship"],
      "quote": { "q": "Be fruitful and increase in number…", "cite": "Genesis 1:28" }   // cite optional
  }],
  "focuses": [{ "title": "Christian Beliefs", "sum": ["…", "…"] }],   // revision weeks; "Focus n" blocks
  "checklist": ["Christian Beliefs", "Marriage and the Family"],       // <ul class=chklist>
  "activities": [{ "title": "Retrieval roulette", "body": "…" }],      // practice weeks
  "podcasts": [{ "key": "pod_E01_w1", "rel": "Podcast_Audio/Mock_Countdown/E01_Wk1_Origins.mp3",
                 "sp": "Year%2011/3%20-%20Mock%20Exam%20Companion/Podcast_Audio/Mock_Countdown/E01_Wk1_Origins.mp3",
                 "series": "e",       // e | c | i → the code's colour (amber / purple / green)
                 "code": "E01", "name": "Wk1 Origins", "kind": "Countdown episode" }],
  "podnote": "Re-listen to your two weakest episodes — you choose which.",   // italic line instead of players
  "episodes": [{ "key": "pset_C01_w7", "rel": "Podcast_Audio/Christianity/C01_The_Trinity.mp3",
                 "sp": "…", "text": "C01" }],    // inline-playing chips; label counts them
  "reads": [ resource, … ],          // "What you read and bring"
  "ticks": "listen"                  // a set name from labels.tickSets, or [["listen","1. Listen"], …]
}
```

A week with exactly one lesson or focus gets the single-column layout
(`lessons-one`) automatically.

A podcast player's `<audio src>` is its `rel`; add `"src"` only if the two
must differ. A player with an empty `rel` is refused by `validate()` — a
player with nothing to play is the one failure that looks fine until a
student presses it.

Tick ids become `data-t="w<n>_<id>"`, which is the localStorage key. Keep
ids stable across rebuilds or students lose their ticks.

---

## labels

Every fixed string. `%N%`, `%NN%` (zero-padded), `%D%`, `%W%`, `%E%` are
substituted where shown.

| key | where | notes |
|---|---|---|
| `phases` | `{teach, rev, mock, fb, ret, ex}` | the phase badge on each card and chip colour class |
| `papers` | `{p1, p2}` | the paper chip text, keyed by `weeks[].paper` |
| `homeNavAria` | `<nav class=cnav aria-label>` | |
| `goToWeek` | left of the chip strip | |
| `holidayGlyph` | html; before each holiday label | `&#9670;` |
| `week` | `Week %NN%` | |
| `copyTitle`, `copyLink` | the copy button's tooltip and text | the 🔗 is added by the template, in HTML as `&#128279;` and in JS as the character |
| `lesson`, `focus` | `Lesson %N%`, `Focus %N%` | |
| `bigQuestion`, `summary`, `keyWords`, `quote` | the small caps labels inside a lesson | |
| `specPrefix` | `· spec ` | before `lessons[].spec` |
| `podcast`, `shelf`, `ticks` | block labels | |
| `relisten` | `Re-listen this week — %N% episodes` | |
| `tickSets` | `{name: [[id, label], …]}` | named tick lists; the source uses `listen`, `exam`, `feedback`, `final` |
| `thisWeek` | the red badge JS inserts on the current week | |
| `copied`, `copyPrompt`, `toastCopied` (`%W%` = week no.), `toastPlaying` (`%E%` = chip text) | copy-link and chip feedback | JS strings |
| `progress` | `%D% of %N% ticked` | initial HTML and the JS update |
| `checkOk`, `checkOkOnline`, `checkOkLocal`, `checkBad`, `checkBadOnline`, `checkBadNoBase`, `checkBadLocal` | the self-check pill | html (they go through `innerHTML`); may name folders, so they are labels not template |

---

## Traps

**Weeks are literal Mondays.** See `calendar` above. Never generate the list
in your head; copy the school calendar out week by week with the holidays
removed, and let `validate()` tell you about a Tuesday.

**Do not "fix" the scrollspy with `scrollIntoView`.** The chip strip is
scrolled sideways by setting `scrollLeft` on purpose. An earlier version
called `chip.scrollIntoView()`, which also scrolls the *page* — every time
the observer fired, the document jumped back to fight the reader's
scrolling. The template carries the comment; keep the behaviour if you fork
the JS. Related: `scroll-padding-top` on `html` (88px) and `scroll-margin-top`
on `.wk` (92px) are additive, so a targeted card lands ~180px from the top —
below the sticky nav, not flush against it. That is intended.

**SharePoint media never streams in-page.** With `resourceBase` set, a
podcast's `src` becomes a SharePoint URL, and SharePoint answers `<audio>`
requests with a sign-in redirect or a download, not a byte-range stream —
the player shows a spinner forever and the self-check pill goes red. The
Year 11 pages solved this by giving the podcasts their own folder
(`podcastBase`) served plainly, and the SumHclass page keeps them next to the
page and probes with `fetch` (`selfCheck: "fetch"`). Office files are fine on
SharePoint (that is what `?web=1` is for); audio is not.

**`meta.id` is the localStorage prefix.** Ticks live under `<id>_ticks` in
the student's browser. Renaming it, or changing tick ids, silently resets
everyone. Decide once.

**`?web=1` on Office files only.** It is appended by the JS at resolve time
for `.pptx .docx .xlsx .ppt .doc .xls` under `resourceBase`. Put it in a
manifest path and it will be doubled online and break the local copy.

**Text fields are escaped, html fields are not.** A `<b>` in `weeks[].say`
will print as `<b>`; an unescaped `&` in `meta.sub` is a stray ampersand.
The extracted manifests are the reference for which is which.

---

## Validation

`build_ks4.py` (and therefore `build_all.py`) refuses to write a page when
any of these hold:

- a missing top-level key, or the wrong `schema`
- `calendar.weeks` empty, not a list, or a date not in `YYYY-MM-DD`
- the number of `weeks` entries differs from the number of calendar dates
- a duplicate week number, or numbers that do not run 1…N
- a week `type` outside `teach rev mock fb ret ex`
- a `paper` with no entry in `labels.papers`; a named tick set that is not in `labels.tickSets`
- a lesson `deck`, a per-week `read`, a shelf item, a podcast or an episode chip with no path
- a term or holiday placed outside the calendar

and warns (build continues) on a calendar date that is not a Monday, an exam
date that is not inside an `ex` week, or a numbered label missing its `%N%`.

The empty-path check is the one that earns its keep: a podcast with nothing
to play renders as a perfectly normal player until a student presses it.
