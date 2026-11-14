# DeepLab product family: sources and build

| File | What |
|---|---|
| [`products.json`](products.json) | **The names table.** One row per product (id, public name, lowercase wordmark, role, motif) plus bundles |
| [`build.py`](build.py) | Builds every product mark, icon, lockup, the stacked master logo and the sheets below from the table |
| [`family-overview.svg`](family-overview.svg) / `.png` | All products with icons, lockups (light and dark) and the Watch bundle |
| [`family-system.svg`](family-system.svg) / `.png` | Construction: grid, live area, keylines, tile, colour roles, lockup spacing |
| [`template-mark.svg`](template-mark.svg) | Working template for drawing a new mark (guides in their own group) |

Rules live in [../BRAND.md](../BRAND.md#product-family).

## Rename a product
1. Edit `name` (text) and `wordmark` (lowercase lockup text) in `products.json`. Change `id` only if the folder should move too.
2. Run the build (below). All lockups, icons, READMEs and sheets are regenerated.
3. If the `id` changed, the script warns about the old `products/<old-id>/` folder. Delete it by hand (and keep a redirect note if anything hotlinks it).
4. Commit.

## New product
Draw the motif on `template-mark.svg`, add it as a new `motif()` branch in `build.py` (keep the grid, stroke and colour-role rules), add a row to `products.json`, then build.

## Build
No sudo needed:

```sh
python3 -m venv --without-pip .venv
curl -sSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python
.venv/bin/pip install fonttools brotli uharfbuzz cairosvg
.venv/bin/python family/build.py --font /path/to/Inter-variable.woff2   # or INTER_FONT=...
```

The font must be Inter 4.x, variable (`wght` axis) or static; weights 400 and 700 are used. Text is converted to outlines, so the output SVGs need no font. The files in this repo were built with Inter 4.001 (the latin subset the Strata portal ships).
