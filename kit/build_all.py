#!/usr/bin/env python3
"""
build_all.py — build every manifest in a folder into a site.

    python3 build_all.py manifests/epq site
    python3 build_all.py manifests            # every subfolder, each into site/<name>/

One manifest per page. The manifest whose meta.id ends in "-index", or the
only manifest in the folder, becomes index.html; the rest are named after
their meta.id.

Exits non-zero if any manifest fails validation, so it is safe in CI.
"""

import glob
import json
import os
import sys

from build_weekly import build, validate, TEMPLATE


def build_folder(src_dir, out_dir, template):
    manifests = sorted(glob.glob(os.path.join(src_dir, "*.json")))
    if not manifests:
        return 0, ["no .json manifests in %s" % src_dir]

    os.makedirs(out_dir, exist_ok=True)
    built, failures = 0, []

    for path in manifests:
        name = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as fh:
                manifest = json.load(fh)
        except ValueError as exc:
            failures.append("%s: not valid JSON — %s" % (name, exc))
            continue

        problems = validate(manifest)
        if problems:
            failures.append("%s:\n    %s" % (name, "\n    ".join(problems)))
            continue

        if len(manifests) == 1 or manifest["meta"].get("id", "").endswith("-index"):
            out_name = "index.html"
        else:
            out_name = "%s.html" % manifest["meta"].get("id", os.path.splitext(name)[0])

        dest = os.path.join(out_dir, out_name)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(build(manifest, template))
        weeks = sum(len(w) for w in manifest["weeks"].values())
        print("  %-34s -> %-22s %d tracks, %d weeks" % (
            name, out_name, len(manifest["tracks"]), weeks))
        built += 1

    return built, failures


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__.strip())
    src = argv[1].rstrip("/")
    out = argv[2] if len(argv) > 2 else "site"

    with open(TEMPLATE, encoding="utf-8") as fh:
        template = fh.read()

    total, failures = 0, []
    if glob.glob(os.path.join(src, "*.json")):
        print("%s:" % src)
        n, f = build_folder(src, out, template)
        total += n
        failures += f
    else:
        for sub in sorted(d for d in glob.glob(os.path.join(src, "*")) if os.path.isdir(d)):
            if os.path.basename(sub).startswith("_"):
                continue
            print("%s:" % sub)
            n, f = build_folder(sub, os.path.join(out, os.path.basename(sub)), template)
            total += n
            failures += f

    print("\n%d page(s) built into %s/" % (total, out))
    if failures:
        sys.stderr.write("\n%d manifest(s) failed:\n" % len(failures))
        for f in failures:
            sys.stderr.write("  ! %s\n" % f)
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv)
