"""Build the remix's packages and recipe from the sheets.

usage: python3 -I tools/build.py <original-files-dir> <out-dir>
Copies every kept row of sheets/files.json byte for byte from the original (or the remix's own copy when
changed=true) into the zip of its component, and writes recipe.json from sheets/recipe.json.
"""
import hashlib
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = (2026, 10, 8, 0, 0, 0)  # fixed timestamps, so the same sheets build the same bytes


def main(orig, out):
    files = json.load(open(os.path.join(ROOT, "sheets", "files.json")))
    recipe_sheet = json.load(open(os.path.join(ROOT, "sheets", "recipe.json")))
    recipe = {row["key"]: row["remix"] for row in recipe_sheet["rows"]}
    os.makedirs(out, exist_ok=True)
    for comp in recipe["components"]:
        path = os.path.join(out, comp["fileName"])
        rows = sorted((r for r in files["rows"] if r["component"] == comp["id"] and r["keep"]), key=lambda r: r["path"])
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for row in rows:
                src = os.path.join(ROOT, row["path"]) if row["changed"] else os.path.join(orig, comp["id"], row["path"])
                data = open(src, "rb").read()
                if not row["changed"]:
                    assert hashlib.sha256(data).hexdigest() == row["sha256"], row["path"]
                info = zipfile.ZipInfo(row["path"], STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, data, compresslevel=9)
        print(f"{comp['fileName']}: {len(rows)} files, {os.path.getsize(path)} bytes")
    with open(os.path.join(out, "recipe.json"), "w") as f:
        json.dump(recipe, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
