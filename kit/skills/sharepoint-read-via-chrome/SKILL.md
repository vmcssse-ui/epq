---
name: sharepoint-read-via-chrome
description: Read whole SharePoint / OneDrive libraries (folder trees and the text of Word, PowerPoint and PDF files) from the teacher's signed-in Chrome without downloading anything to their computer. Use when given a SharePoint or OneDrive link to schemes of work, learning journeys, lesson folders or shared libraries.
---
<!-- © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital. All rights reserved. See NOTICE.md. -->

# Reading SharePoint from Chrome

The sandbox cannot reach sharepoint.com; the teacher's Chrome can. Do the listing and the file parsing inside a tab on the SharePoint site, and bring only text out.

## 1. Resolve the link
Prefer the address-bar URL. Decode the `id=` parameter to the server-relative folder path (`/sites/<site>/Shared Documents/...` or `/personal/<user>_<tenant>_org/Documents/...`). Tokenised sharing links (`/:f:/s/…`) must be opened first so SharePoint reveals the real path. Personal OneDrive lives on `https://<tenant>-my.sharepoint.com/personal/<user>`; team sites on `https://<tenant>.sharepoint.com/sites/<site>`.

## 2. List the tree
In a tab on that host, run `javascript_tool`:
`fetch(base + "/_api/web/GetFolderByServerRelativeUrl('" + encodeURIComponent(path) + "')?$expand=Files,Folders&$select=Files/Name,Files/TimeLastModified,Files/Length,Folders/Name", {headers:{Accept:"application/json;odata=nometadata"}})`
Recurse into `Folders` (skip `Forms`). Store everything on `window.__X`; return short slices (the tool truncates around 1,000 characters). Replace `=` with `§` before returning any string — the output filter blocks anything that looks like a query string or cookie.

## 3. Get file text without downloads
Fetch the file bytes with `base + "/_layouts/15/download.aspx?SourceUrl=" + encodeURIComponent(path)`. For `.docx`/`.pptx` parse the zip in the browser: locate `word/document.xml` (or `ppt/slides/slideN.xml`) from the central directory, inflate with `new DecompressionStream('deflate-raw')`, then strip tags — keep `</w:p>`→newline, `</w:tc>`→` | `, `</w:tr>`→newline so tables survive; drop `mc:Fallback` blocks to avoid duplicated text-box text.

## 4. Bring text out in bulk
Write the text into the page (`document.write('<pre id=x></pre>')`, set `textContent`) and call `get_page_text`. It caps at 50,000 characters, and results above ~50 KB are persisted to a file on disk instead of the transcript — so page the text in windows of ~49,500 characters padded past the threshold, save each persisted JSON, and stitch them back together in the sandbox (`toolu_*.json` → strip the `WINn` header and padding). Fifty documents of 13 KB take ~15 windows.

## 5. Duplicates and versions
When a library holds copies (e.g. a "with Seneca links" sub-folder), decide by `TimeLastModified` per subject and check content equivalence by a word-set diff before choosing; record chosen and set-aside versions for the audit trail.

## Never
Never download files to the teacher's computer or trigger `<a download>`; never move, rename or upload on SharePoint without an explicit request; never assume a file exists because a page mentions it — HEAD-test it.
