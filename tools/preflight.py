"""Preflight: lay the sheets over each other and list every unfilled cell and every unresolved reference.

usage: python3 -I tools/preflight.py <original-files-dir>
<original-files-dir> holds the original's packages unpacked, one folder per component id (main/, minecraft/).
Exits 1 when anything is listed.
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "sheets", name + ".json")) as f:
        return json.load(f)


def main(orig):
    files, recipe = load("files"), load("recipe")
    problems = []

    # every cell filled
    for sheet in (files, recipe):
        for i, row in enumerate(sheet["rows"]):
            for col in sheet["columns"]:
                if col not in row or row[col] is None or row[col] == "":
                    problems.append(f"{sheet['sheet']} row {i} ({row.get('path') or row.get('key')}): {col} is empty")

    r = {row["key"]: row["remix"] for row in recipe["rows"]}
    for key in ("schemaVersion", "mode", "games", "components", "requirements", "mappings", "launch"):
        if key not in r:
            problems.append(f"recipe: required key {key} has no row")
    comp_ids = {c["id"] for c in r.get("components", [])}

    # files -> components, original bytes, licenses
    for row in files["rows"]:
        if row["component"] not in comp_ids:
            problems.append(f"files {row['path']}: component {row['component']} is not in recipe.components")
        src = os.path.join(orig, row["component"], row["path"])
        if not os.path.isfile(src):
            problems.append(f"files {row['path']}: not in the original files ({src})")
            continue
        data = open(src, "rb").read()
        if len(data) != row["size"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            problems.append(f"files {row['path']}: size or sha256 differs from the original")
        if row["changed"] and not os.path.isfile(os.path.join(ROOT, row["path"])):
            problems.append(f"files {row['path']}: changed=true but the remix's own copy is missing")

    # every kept file is installed by a mapping (first match wins), every mapping installs something
    kept = [row for row in files["rows"] if row["keep"]]
    used = set()
    for row in kept:
        hit = None
        for n, m in enumerate(r.get("mappings", [])):
            if m["component"] != row["component"]:
                continue
            if m["from"] == "" or m["from"] == row["path"] or (m["from"].endswith("/") and row["path"].startswith(m["from"])):
                hit = n
                break
        if hit is None:
            problems.append(f"files {row['path']}: no mapping installs it")
        else:
            used.add(hit)
    for n, m in enumerate(r.get("mappings", [])):
        if n not in used:
            problems.append(f"recipe mapping {n} ({m['component']}:{m['from']}): installs no kept file")

    # recipe references to files: setup/together launch paths, setup.done under a mapped folder
    targets = {}
    for row in kept:
        for m in r["mappings"]:
            if m["component"] == row["component"] and (m["from"] == "" or row["path"].startswith(m["from"])):
                targets[m["to"].rstrip("/") + "/" + row["path"][len(m["from"]):]] = row
                break
    launches = [r.get("setup", {}).get("launch")] + [t["launch"] for t in r.get("together", [])] + [r["launch"]]
    for la in launches:
        if la and la.get("kind") == "exe" and la["path"] not in targets:
            problems.append(f"recipe launch {la['path']}: no kept file lands there")

    # the dropped loader must be replaced by the loader requirement
    dropped = {row["path"] for row in files["rows"] if not row["keep"]}
    if "gta/dinput8.dll" in dropped and {"kind": "loader", "id": "ultimate-asi-loader"} not in r["requirements"]:
        problems.append("dinput8.dll is dropped but ultimate-asi-loader is not required")
    if "gta/args.txt" in dropped and "-nobattleye" not in r["launch"].get("args", []):
        problems.append("args.txt is dropped but launch.args don't carry -nobattleye")

    # credits: every non-MIT license named in the shipped credits
    credits = open(os.path.join(ROOT, "credits", "CREDITS.txt")).read()
    for name in ("Script Hook V", "ReShade", "Prism Launcher", "Fabric API", "universal-modder", "Melty"):
        if name not in credits:
            problems.append(f"credits: {name} is not credited")

    for p in problems:
        print("PREFLIGHT:", p)
    print(f"preflight: {len(files['rows'])} file rows x {len(files['columns'])} columns, "
          f"{len(recipe['rows'])} recipe rows x {len(recipe['columns'])} columns, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
