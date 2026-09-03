<!-- © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework, Weekly Page Kit. All rights reserved. See NOTICE.md. -->
# Edu.Ai Weekly Page Kit

One folder that can reproduce, and replicate for any other course, the two kinds of
week-by-week page the Edu.Ai Ecosystem runs at Harlington:

| edition | worked example | live page | what it is |
|---|---|---|---|
| `weekly/` | EPQ 2026–27 (3 tracks, 38 weeks) | https://vmcssse-ui.github.io/epq/ | a **task** page — sessions, tasks, log book, session links, video/podcast per week; several groups on different clocks as tabs |
| `ks4-weekly/` | Year 11 RS, three tiers (33 weeks each) | https://vmcssse-ui.github.io/summit/year11-{supported,summit,sumhclass}.html | a **course** page — two lessons a week with Big Question, key words, quote and summary; podcasts; revision episode sets; Listen/Read/Practise ticks; resource shelf; unit-page map |

Both editions follow the same rule: **the design lives in one template, every word,
date, link and colour lives in a JSON manifest, and a generator joins them.** A new page
for another subject is a new manifest, not new code. Both are proven by round-trip: the
live pages were extracted into manifests, rebuilt, and compared — identical.

```
(root of kit/)  the EPQ-style weekly edition (template.weekly.html, build_weekly.py, browser builder, schema, manifests) — referred to below as `weekly/`
ks4-weekly/    the KS4-style kit (template, build_ks4.py, extract_ks4.py, roundtrip.py, smoke test, schema, manifests)
.claude/agents/   four Claude Code sub-agents that do the work (extract content · build · wire links · publish)
skills/           three skills: the replication procedure, SharePoint reading, SharePoint wiring
NOTICE.md         the intellectual-property notice — read it before sharing anything in this folder
```

## The quickest path to a new page

1. Decide the edition. Groups on different clocks with weekly *tasks* → `weekly/`.
   One class on one clock with *lessons* to learn from → `ks4-weekly/`.
2. Copy the skeleton: `weekly/manifests/_skeletons/blank-course.json` or
   `ks4-weekly/manifests/_skeletons/blank-course.json`.
3. Set the calendar first — weeks are a literal list of Mondays, one per teaching week,
   with the holidays left out. (The EPQ builder's Calendar panel generates this from
   term dates.)
4. Fill the weeks. For a KS4 page the lesson fields come out of the lesson decks — the
   `weekly-page-extractor` agent reads a folder of `.pptx` and returns them as manifest
   entries so the page cannot drift from the decks.
5. Build and check:
   `python3 ks4-weekly/build_ks4.py my.json out/my.html` (validation refuses a broken
   manifest) then `python3 ks4-weekly/smoke_ks4.py out` — or, for the other edition,
   `python3 weekly/build_weekly.py my.json out/index.html`.
6. Wire the resources: set `files.resourceBase` / `files.podcastBase` (KS4) or
   `files.base` (weekly) to the SharePoint folder, and let the `weekly-page-wirer`
   agent test every link from a signed-in browser.
7. Publish to GitHub Pages with the `weekly-page-publisher` agent, then seal the group:
   a class group gets its own master page and never a link to other groups' pages.

## Things that have gone wrong before, so the kit guards against them

- A week counter (`start + 7 × n`) silently mis-dates every week after the first
  holiday. Weeks are stored as explicit Mondays.
- Deep links into long pages land in the wrong place until web fonts have loaded.
  The templates re-anchor after `document.fonts.ready`.
- Never call `scrollIntoView` from a scroll handler — the week nav would drag the page
  back to week 1. The KS4 template sets `scrollLeft` on the nav instead.
- SharePoint will not stream audio into a page (`<audio>` stalls at readyState 0 even
  when `fetch` succeeds). Podcasts are hosted in the public repo, or offered as
  `download.aspx?SourceUrl=` links — never as direct SharePoint mp3 players.
- `?web=1` goes on Office files only; mp3 and PDF links stay plain.
- `meta.id` (KS4) / `meta.id` (weekly) is the localStorage prefix for students' ticks.
  Change it and everyone's ticks reset — and two pages sharing an id share ticks.
- "Nothing works" from a student while every owner-session test passes means item
  permissions on SharePoint (`HasUniqueRoleAssignments`), not the page.
- A YouTube id that is wrong renders an empty player, not an error. Verify every id
  through `youtube.com/oembed` before shipping.
