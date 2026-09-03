---
name: sharepoint-resource-wiring
description: Wire and verify the SharePoint links behind an ecosystem page (decks, booklets, podcasts) — real paths, ?web=1 rules, podcast hosting, item permissions — and diagnose "nothing works" reports. Use when links must be pointed at SharePoint or students cannot open resources.
---
<!-- © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital. All rights reserved. See NOTICE.md. -->

# Wiring resources to SharePoint

## Mechanism on the page
Every button and player carries `data-sp` (path inside the base folder) and optionally `data-rel` (relative path for a local/repo copy). A single `RESOURCE_BASE` (and `PODCAST_BASE`) constant re-points everything; a `LINKS` map holds exceptions. `?web=1` is auto-appended to Office files so they open in Office Online; mp3/PDF stay plain. Local builds set the base empty so `data-rel` wins.

## Getting paths right
- Address-bar URL → decode `id=` → server-relative path. SharePoint appends ` (1)` to re-uploaded folders; use the real name.
- List the folder via `_api/web/GetFolderByServerRelativeUrl(...)?$expand=Files,Folders` from a signed-in tab and HEAD-test one file per folder — then every wired target before sign-off. Expect 200/206.
- Browser uploads silently drop files; if a deck is missing, upload it through an injected `<input type=file>` + `_api/web/GetFolderByServerRelativeUrl('…')/Files/Add(url='name',overwrite=true)` with a request digest (10 MB per call).

## Podcasts
`<audio>` on any SharePoint URL stalls at readyState 0 (cross-site cookies); `fetch` succeeding proves nothing. Host mp3s in the public GitHub repo (relative paths) or link `download.aspx?SourceUrl=<encoded>`. Test playback with a real `<audio>` element in a **visible** tab; hidden tabs defer media loads.

## Permissions — the "nothing works" diagnosis
If the owner's clicks all pass but students are refused: the folder or an ancestor has `HasUniqueRoleAssignments = true`. Share it with "Everyone except external users · Can view" via the Share dialog (same-origin iframe `sharedialog.aspx` — reach in with `frame.contentDocument`; default may be "Can edit"). Confirmation text is the proof; REST read-back 403s for non-admins. A pilot area under a restricted ancestor needs the grant even if sibling strands work.

## Sign-off checklist
Base constants set · every target HEAD 200 · `?web=1` on Office only · no direct-mp3 players · self-check pill green from the owner's session · one student test after any permission change.
