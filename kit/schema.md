# Weekly page manifest — schema

`schema: "weekly-page/1"`

One manifest describes one page. The template supplies the design and the
behaviour; the manifest supplies every word, date, link and colour. Nothing
about a particular course is hard-coded in the template — if you find yourself
editing `template.weekly.html` to change wording, the wording belongs in
`meta.labels` instead.

Build it with either generator — they are twin ports and produce the same file:

```
python3 build_weekly.py manifests/epq/epq-2026-27.json site/index.html
```

or open `builder.html`, load the manifest, and press **Download page**.

---

## Top level

| key | required | what it is |
|---|---|---|
| `schema` | – | `"weekly-page/1"` |
| `meta` | ● | identity, masthead, and every fixed string |
| `theme` | – | optional CSS token overrides, `{light:{}, dark:{}}` |
| `calendar` | ● | the week spine, terms, breaks, notes |
| `files` | – | how relative resource paths become URLs |
| `resources` | – | every linkable file, by id |
| `library` | – | the shelves at the foot of the page |
| `tracks` | ● | one per tab |
| `weeks` | ● | `{trackKey: {weekNumber: week}}` |

---

## meta

```jsonc
"meta": {
  "id": "epq-2026-27",            // localStorage prefix for tick-boxes AND the output filename.
                                  // Changing it resets everyone's ticks — treat it as permanent.
  "title": "EPQ Week by Week",
  "eyebrow": ["Harlington School", "AQA 7993 · Level 3 Extended Project"],
  "standfirst": "One sentence on what the page is for.",
  "hint": "HTML allowed. Omit to hide the line.",
  "facts": [["Teaching weeks","38"], ["Cohort","18 students"]],
  "footer": ["Left line", "Right line"],
  "siteUrl": "https://vmcssse-ui.github.io/epq/",   // see below — set this before sharing links
  "description": "…",             // <meta name=description>
  "noindex": true,                // adds <meta name=robots content=noindex>
  "fonts": "https://fonts.googleapis.com/css2?family=…",
  "labels": { … }
}
```

**`siteUrl` matters more than it looks.** Every *Copy week link* button builds
its URL from it. If it is wrong or empty the page falls back to guessing from
`location`, which is fine locally and wrong the moment the page is embedded or
moved. Set it to the final address before anyone shares a link.

### meta.labels

Every fixed string on the page. Defaults in brackets.

| key | where it appears |
|---|---|
| `weekWord` (`Week`) | above each week's date |
| `slotA` / `slotB` | the two session box headings |
| `tasks` | heading above the tick-boxes |
| `logbook` | bold label on the record line |
| `also` | heading above leftover resource chips |
| `supervisor` | heading of the second-view panel |
| `viewA` / `viewB` | the two view buttons |
| `today` | the jump-to-current-week button |
| `watch` / `listen` | video and podcast buttons |
| `copyLink` / `copied` / `copyManual` | the copy-link button's three states |
| `libraryTitle` / `libraryLede` / `gapsLabel` | the resource library |
| `endcapTitle` / `endcapBody` / `endcapPoints` | shown when a track ends before the year does |

In the end-cap strings, `%A%` is the first unscheduled week, `%B%` the last week
of the year, `%L%` the track's final week.

---

## calendar

```jsonc
"calendar": {
  "weeks": ["2026-09-07", "2026-09-14", …],   // teaching Mondays, holidays ALREADY REMOVED
  "terms": [{ "t": "Autumn 1 · September – October 2026", "from": 1, "to": 7 }],
  "notes": { "13": "Term ends Fri 18 Dec" },  // italic line on that week's card
  "breaks": { "7": { "lbl": "Autumn half term",
                     "dt": "Mon 26 Oct – Fri 6 Nov · two weeks",
                     "msg": "optional sentence",
                     "warn": true } },        // rendered after that week number
  "shortWeeks": { "24": 3 }                   // 3 = week ends Thursday (default 4 = Friday)
}
```

**`weeks` is a literal list of Mondays, not a start date plus a counter.** This
is the single most important thing in the schema. An earlier version of this
page computed each week as `firstMonday + 7×(n−1)`, which silently dated every
week after the first holiday wrongly — week 20 rendered as 18 January instead of
22 February, and nothing in the page looked broken. Holidays are absent from the
list; `terms` indexes into it; `breaks` are hung off the last week before each
gap. The builder's Calendar panel generates all of this from one first/last
Monday per term, which is the safe way to author it.

`from`/`to` are 1-based and inclusive. Keys in `notes`, `breaks` and
`shortWeeks` are week numbers as strings.

---

## tracks

One tab each. Use several when groups share a page but run on different clocks;
a single-group course has one track and the tab bar still works.

```jsonc
{
  "key": "jun",                    // lowercase a–z0–9 only — it goes in the URL as #jun-w19
  "label": "Y13 · June 2027",      // tab text
  "count": "6",                    // small badge on the tab
  "name": "Year 13 · June 2027 series",
  "blurb": "A paragraph on who this track is and what its year looks like.",
  "spine": [["Full draft","Fri 12 Feb"], ["Presentations","w/c 15 Mar"]],
  "accent": { "ink":"#2F5E80", "bg":"#E8F0F6", "rule":"#BBD2E2",
              "inkDark":"#84B6D8", "bgDark":"#132534", "ruleDark":"#25415A" }
}
```

Accents are injected as CSS custom properties at load, so tracks can be added
without touching the stylesheet. Give the dark values real thought rather than
darkening the light ones — `ink` needs to stay legible on a near-black ground.

A track whose weeks stop before the calendar does gets an end-cap panel instead
of a run of empty cards.

---

## resources and files

```jsonc
"files": {
  "origin": "https://hs365.sharepoint.com",
  "prefix": "/sites/HS_Subjects_RE/",
  "base": "Year 11/Philosophy/Edu AI - EPQ/",
  "officeParam": "?web=1",
  "officeExt": ["pptx","docx","xlsx"],
  "folderView": "/sites/HS_Subjects_RE/Year%2011/Forms/AllItems.aspx?id=",
  "folderRoot": "/sites/HS_Subjects_RE/Year 11/Philosophy/Edu AI - EPQ"
},
"resources": {
  "u1": { "label": "Unit 1 · Managing the Project",
          "path": "Unit 1/EPQ_1_Managing_the_Project.pptx",
          "type": "PPTX",
          "short": "Unit 1 deck" }
}
```

A URL is built as `origin + encodeURIComponent-per-segment(prefix + base + path)`,
plus `officeParam` when the extension is in `officeExt` — that suffix is what
makes Office files open in the browser instead of downloading. A `path` starting
`http://` or `https://` is used as-is, so external resources need no config.

`label` is the full name used in chips and the library; `short` is the button
text inside a session box, where the full name will not fit.

---

## weeks

`weeks[trackKey][weekNumber]`. Week numbers index `calendar.weeks`, so a track
can skip weeks freely — a track with weeks 1–8 simply ends after week 8.

```jsonc
{
  "p": "Gate week",                 // phase chip
  "t": "Baseline audit",            // week title
  "f": "HARD · Fri 16 Oct",         // deadline flag; null for none. Any value turns the card red.
  "l": "One or two sentences of context.",
  "w": "What happens in session A.",
  "c": "What happens in session B.",
  "wl": ["u1","s12"],               // files opened in session A
  "cl": ["lb13"],                   // files opened in session B
  "k": ["Task one.", "Task two."],  // tick-boxes
  "g": "What gets recorded.",       // the gold record line
  "r": ["nA1","trk"],               // other files; anything already in wl/cl is filtered out
  "s": "Note shown only in the second view.",
  "q": ["Log book check 1"],        // checkpoint chips, second view only
  "video":   { "url": "https://youtu.be/…", "label": "Watch", "mins": "6 min" },
  "podcast": { "url": "…/week5.mp3",        "label": "Listen", "mins": "12 min" }
}
```

**Video and podcast are optional and independent.** `null` or a missing key
shows nothing at all — no empty player, no placeholder — so media can be added
week by week as it is recorded rather than all at once. YouTube URLs in any of
the usual shapes (`youtu.be/ID`, `watch?v=ID`, `/embed/ID`, `/shorts/ID`) are
rewritten to `youtube-nocookie.com` embeds. Any other URL is used as-is in the
iframe. A podcast URL becomes an `<audio>` element; a relative path is resolved
through `files` like any other resource.

Nothing loads until the button is pressed — a page with 38 weeks of video does
not fetch 38 iframes — and opening one closes the other.

---

## library

```jsonc
"library": {
  "shelves": [["Unit decks", ["u1","u2","u3"]]],
  "folders": [["Edu AI – EPQ", "", "ROOT"], ["Docs", "Docs", "FOLDER"]],
  "gaps": "What is missing, shown in a dashed box."
}
```

Folder entries are `[label, subfolder, badge]` and are built from
`files.folderView` + `files.folderRoot`. If shelves, folders and gaps are all
empty the whole section is removed from the page.

---

## theme

Optional. Overrides the template's CSS custom properties without touching the
stylesheet:

```jsonc
"theme": {
  "light": { "bg": "#FBF7EE", "gold": "#C9A227" },
  "dark":  { "bg": "#0E1420" }
}
```

Keys are token names without the `--`. Track accents are separate — they live on
each track.

---

## Validation

Both generators refuse to write a page when any of these hold, and the builder
shows them live:

- a missing top-level key
- `calendar.weeks` empty, or a date not in `YYYY-MM-DD`
- a term spanning outside the week list
- a duplicate track key, a key that is not lowercase alphanumeric, or a track
  with no `weeks` entry
- a week number beyond the calendar
- `wl`, `cl`, `r` or a library shelf referencing a resource id that does not exist
- a `video` or `podcast` with no `url`

The unknown-resource check is the one that earns its keep: a mistyped id would
otherwise fail silently as a missing button on one card in one week of one track.
