# Minecraft x GTA V: Clean Install

A remix of [Minecraft x GTA V](https://melty.gg/m/minecraft-x-gta-v) by Melty (v0.1.5), built from
[rehan-remade/universal-modder](https://github.com/rehan-remade/universal-modder/tree/main/examples/minecraft-gta5-passthrough).
The game is unchanged; only how it installs changed (see `credits/CREDITS.txt`). GTA V story mode only.

- `sheets/files.json`: every file of the original's packages, kept or dropped and why.
- `sheets/recipe.json`: the Melty install recipe, original next to remix.
- `tools/preflight.py <orig>`: lists empty cells and unresolved references; build only when it reports 0 problems.
- `tools/build.py <orig> <out>`: builds the two packages and `recipe.json` from the sheets.

`<orig>` is the original's two packages unpacked as `main/` and `minecraft/` (from Melty's `remix_mashup`).
No game files or third-party binaries are kept in this repository.
