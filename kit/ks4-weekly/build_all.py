#!/usr/bin/env python3
# © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework, Weekly Page Kit (KS4 edition). All rights reserved. Harlington School deployment licensed for internal use. Not for reproduction or redistribution without written permission.
"""
build_all.py <manifests-folder> <site-folder>

Every *.json under the manifests folder becomes <site-folder>/<name>.html.
Sub-folders are walked; any folder whose name starts with "_" is skipped
(that is where _skeletons lives).  Exit status is the number of failed
builds, so it works as a CI step.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ks4  # noqa: E402


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    src, dst = argv
    failed, built = 0, 0
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if not d.startswith("_"))
        for fn in sorted(files):
            if not fn.endswith(".json") or fn.startswith("_"):
                continue
            path = os.path.join(root, fn)
            out = os.path.join(dst, os.path.relpath(root, src), fn[:-5] + ".html")
            out = os.path.normpath(out)
            try:
                m = json.load(open(path, encoding="utf-8"))
                page = build_ks4.build(m)
            except (build_ks4.ManifestError, ValueError, KeyError, TypeError) as e:
                print("FAIL  %s\n      %s" % (path, str(e).replace("\n", "\n      ")))
                failed += 1
                continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w", encoding="utf-8", newline="\n") as f:
                f.write(page)
            print("ok    %s -> %s (%d weeks)" % (path, out, len(m["weeks"])))
            built += 1
    print("%d built, %d failed" % (built, failed))
    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
