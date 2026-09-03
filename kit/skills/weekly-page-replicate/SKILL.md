---
name: weekly-page-replicate
description: Replicate an Edu.Ai week-by-week page (EPQ-style task page or KS4-style course page) for a new subject, year group or tier using the Weekly Page Kit — manifest first, then build, wire, publish and seal. Use when asked for a "week by week" page, a weekly ecosystem page, or to replicate the Y11 RS / EPQ pages for another course.
---
<!-- © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework. All rights reserved. See NOTICE.md. -->

# Replicating a weekly page

The kit lives in the `EduAi_Weekly_Page_Kit` folder (also `kit/` in `vmcssse-ui/epq` for the weekly edition). Everything course-specific goes in a JSON manifest; the templates are never edited to change words. Four sub-agents in `.claude/agents/` do the heavy lifting: `weekly-page-extractor`, `weekly-page-builder`, `weekly-page-wirer`, `weekly-page-publisher`.

## 1. Choose the edition (ask if unclear)
- **`weekly/`** (EPQ-style): groups on different clocks as tabs; each week = phase, two session boxes with their own file buttons, tasks with tick-boxes, a record line, leftover resource chips, optional video/podcast; Student/Supervisor views. Schema `weekly-page/1`.
- **`ks4-weekly/`** (Year 11 RS-style): one class on one clock; each week = paper chip, title, "say" line, two lessons (Big Question, deck button, four key words, learn-this quote + source, two-paragraph summary) or revision focuses, podcasts, episode-set chips, Listen/Read/Practise ticks; resource shelf and unit-page map at the foot. Schema `ks4-weekly/1`.

## 2. Settle the identity before any content
Ask for, in this order: the course/tier name exactly as the teacher wants it branded (a clone branded as another strand reads as "not connected" whatever the nav does); the audience (staff preview vs students — students get a sealed group master page and never the staff index); the final URL (`meta.siteUrl`); a unique `meta.id` (localStorage prefix — two pages with the same id share ticks; changing it later resets ticks).

## 3. Calendar spine
Weeks are a literal list of Mondays. Take the term dates (or the teacher's timetable .xlsx) and list every teaching Monday, leaving holidays out; mark term ends on a Thursday; mark exam days. Never derive dates by adding seven days. Sixth form may start a week later than the school.

## 4. Content
- KS4: run `weekly-page-extractor` on the lesson-deck folder; it maps decks to weeks by topic and returns lessons/focuses/podcasts with provenance. Write summaries at the tier's reading level.
- Weekly: fill `tracks`/`weeks` from the scheme of work; session links (`wl`/`cl`) point at resource ids; verify every YouTube id via oEmbed.
- Copy `manifests/_skeletons/blank-course.json`; keep `meta.labels` for every fixed string.

## 5. Build and prove
`weekly-page-builder`: validation, counts, Playwright smoke test (zero console errors, cards, chips, ticks persist, deep link lands). For the KS4 kit, `roundtrip.py` must still pass after any template edit.

## 6. Wire
`weekly-page-wirer`: real SharePoint paths from the address bar, HEAD-test every target from the signed-in browser, `?web=1` on Office files only, podcasts hosted in the repo (SharePoint will not stream in-page), permissions checked (`HasUniqueRoleAssignments`).

## 7. Publish and seal
`weekly-page-publisher`, only with an explicit yes per commit: fetch fresh, upload, verify commit and served page with a cache-buster, seal the group (own master page, home links only to it), sync local masters.

## Done means
The teacher's whole click path works from a student's point of view: master → week → deck opens → podcast plays → ticks persist; the page is branded with the group's own name; nothing links out of the group; the manifest is saved beside the kit so next year is a data edit.
