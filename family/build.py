#!/usr/bin/env python3
"""Build the DeepLab product family assets from family/products.json.

Generates, for every product in the names table:
  products/<id>/<id>-mark(.svg|-dark.svg|-512.png|-dark-512.png)
  products/<id>/<id>-icon.svg, <id>-icon-16/32/180/512.png
  products/<id>/<id>-logo(-dark).svg/.png            horizontal lockup
  products/<id>/<id>-logo-stacked(-dark).svg/.png    stacked lockup
  products/<id>/README.md (unless the table says "readme": "hand")
plus bundle lockups (products/<bundle>/), the stacked master logo
(logo/deeplab-logo-stacked*), and the sheets in family/.

A rename is: edit products.json, rerun this script, commit.

Requirements (no sudo needed):
  python3 -m venv --without-pip .venv && curl -sSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python
  .venv/bin/pip install fonttools brotli uharfbuzz cairosvg
  .venv/bin/python family/build.py --font /path/to/InterVariable.ttf   (or Inter .woff2, variable)

All text is converted to outlines, so the SVGs need no font to display.
"""
import argparse
import io
import json
import math
import os
import sys

import cairosvg
import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- palette
INK = "#0F1729"
PAPER = "#F5F6F8"
SIGNAL = "#2F6FED"
SIGNAL_LIGHT = "#5B8DEF"
ACCENT = "#22C3EE"
MUTED = "#64748B"
BORDER = "#E2E5EA"

MODES = {
    # core colour, support opacity, wordmark colour, product-name colour
    "light": dict(core=SIGNAL, support=0.7, word=INK, name=SIGNAL),
    "dark": dict(core=SIGNAL_LIGHT, support=0.75, word=PAPER, name=SIGNAL_LIGHT),
}

# ---------------------------------------------------------------- grid rules
GRID = 64          # every mark is drawn on a 64 x 64 unit grid
LIVE = (6, 58)     # live area: nothing (including stroke) leaves 6..58
STROKE = 5.5       # the one stroke weight, round caps and joins
KEY = LIVE[0] + STROKE / 2  # 8.75: where stroke centres sit on the live edge
TILE_RX = 14       # app-icon tile corner radius (on the 64 grid)
TILE_GLYPH = 0.75  # glyph scale inside the tile (6..58 maps to 12.5..51.5)
TILE_GLYPH_16 = 0.875  # bigger glyph for the 16 px favicon only

# lockup typography (units of the 64 grid; matches logo/deeplab-logo.svg)
TEXT_SIZE = 38
TEXT_X = 76        # wordmark origin: 12 units after the 64-unit mark box
BASELINE = 44
NAME_GAP = 10.7    # one Inter Regular word space at 38: same as the space inside "ai guard"


def f(v):
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def stroke(color, opacity=1.0, width=STROKE):
    o = "" if opacity == 1 else ' stroke-opacity="%s"' % f(opacity)
    return ('fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
            'stroke-linejoin="round"%s' % (color, f(width), o))


def almond(hw, hh, cx=32, cy=32):
    """Eye outline: the shared Watch motif."""
    p = lambda x, y: "%s %s" % (f(x), f(y))
    return ("M%s C%s %s %s S%s %s C%s %s %s S%s %sZ" % (
        p(cx - hw, cy),
        p(cx - hw * .745, cy - hh * .667), p(cx - hw * .392, cy - hh), p(cx, cy - hh),
        p(cx + hw * .745, cy - hh * .667), p(cx + hw, cy),
        p(cx + hw * .745, cy + hh * .667), p(cx + hw * .392, cy + hh), p(cx, cy + hh),
        p(cx - hw * .745, cy + hh * .667), p(cx - hw, cy)))


def spark(cx, cy, r, waist):
    """Four-point signal spark with straight edges."""
    w = waist
    pts = [(cx, cy - r), (cx + w, cy - w), (cx + r, cy), (cx + w, cy + w),
           (cx, cy + r), (cx - w, cy + w), (cx - r, cy), (cx - w, cy - w)]
    return "M" + " ".join("%s %s" % (f(x), f(y)) for x, y in pts) + "Z"


def arc(cx, cy, r, a0, a1):
    """Arc from angle a0 to a1 (degrees, clockwise on screen)."""
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return "M%s %sA%s %s 0 %d 1 %s %s" % (f(x0), f(y0), f(r), f(r), large, f(x1), f(y1))


# ---------------------------------------------------------------- motifs
# Colour roles: core = Signal 100 % (solid forms), support = Signal at 70 %
# (75 % on dark) for containers and secondary strokes, spark = Accent cyan,
# used for exactly ONE element: the thing the product protects or watches.
def motif(key, mode):
    m = MODES[mode]
    P, so, A = m["core"], m["support"], ACCENT
    if key == "master":
        return ('<path d="M32 6 58 19 32 32 6 19Z" fill="%s"/>' % P +
                '<path d="M6 30.5 32 43.5 58 30.5" %s/>' % stroke(P, so) +
                '<path d="M6 42 32 55 58 42" %s/>' % stroke(A))
    if key == "strata":
        # Layers of history converging on one solid restore point (cyan keystone).
        return ('<path d="M32 8.75 55.25 20.38 32 32 8.75 20.38Z" %s/>' % stroke(P) +
                '<path d="M8.75 31 32 42.63 55.25 31" %s/>' % stroke(P, so) +
                '<path d="M32 45 45 51.5 32 58 19 51.5Z" fill="%s"/>' % A)
    if key == "central":
        # Hub: the platform core inside one ring, one product in orbit.
        a = -45
        return ('<path d="%s" %s/>' % (arc(32, 32, 22.5, a + 30, a + 330), stroke(P, so)) +
                '<path d="M32 21 43 32 32 43 21 32Z" fill="%s" stroke="%s" stroke-width="3" '
                'stroke-linejoin="round"/>' % (P, P) +
                '<circle cx="%s" cy="%s" r="5.75" fill="%s"/>' % (
                    f(32 + 22.5 * math.cos(math.radians(a))),
                    f(32 + 22.5 * math.sin(math.radians(a))), A))
    if key == "control":
        # Remote command: a console with a prompt and a live cursor.
        return ('<rect x="8.75" y="11.75" width="46.5" height="40.5" rx="8" %s/>' % stroke(P, so) +
                '<path d="M21 25 28 32 21 39" %s/>' % stroke(P) +
                '<path d="M35 39H44" %s/>' % stroke(A))
    if key == "aiguard":
        # Shield (top edge on the master's 2:1 slope) guarding one AI spark.
        return ('<path d="M32 8.75 54 19.75V31C54 43 45 51.5 32 55.75 19 51.5 10 43 10 31V19.75Z" %s/>'
                % stroke(P, so) +
                '<path d="%s" fill="%s" stroke="%s" stroke-width="2" stroke-linejoin="round"/>'
                % (spark(32, 32.5, 11.5, 3.1), A, A))
    if key == "endpoint-watch":
        # Watch eye; the pupil is a device (host), one cyan status light.
        return ('<path d="%s" %s/>' % (almond(23.25, 15.5), stroke(P, so)) +
                '<rect x="23" y="23" width="18" height="18" rx="4.5" fill="%s"/>' % P +
                '<circle cx="36.5" cy="27.5" r="3" fill="%s"/>' % A)
    if key == "network-watch":
        # Same Watch eye; its corners become network nodes, the pupil is the
        # flow being watched.
        return ('<path d="%s" %s/>' % (almond(20.5, 14), stroke(P, so)) +
                '<circle cx="11.5" cy="32" r="5.25" fill="%s"/>' % P +
                '<circle cx="52.5" cy="32" r="5.25" fill="%s"/>' % P +
                '<circle cx="32" cy="32" r="7.5" fill="%s"/>' % A)
    if key == "aware":
        # Security awareness: a message (envelope) that makes you pause — one
        # cyan alert spark rising from it. No hook (cliche) and no eye (Watch).
        return ('<rect x="8.75" y="24.5" width="38" height="30.75" rx="6" %s/>' % stroke(P, so) +
                '<path d="M14.5 31 27.75 41 41 31" %s/>' % stroke(P) +
                '<path d="%s" fill="%s" stroke="%s" stroke-width="2" stroke-linejoin="round"/>'
                % (spark(48.5, 16, 8.5, 2.4), A, A))
    raise KeyError(key)


def mark_svg(key, mode, label, size=64):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="%d" height="%d" '
            'role="img" aria-label="%s">%s</svg>' % (size, size, label, motif(key, mode)))


def icon_inner(key, scale=TILE_GLYPH, rounded=True):
    t = (64 - 64 * scale) / 2
    bg = ('<rect width="64" height="64" rx="%s" fill="%s"/>' % (TILE_RX, INK) if rounded
          else '<rect width="64" height="64" fill="%s"/>' % INK)
    return bg + '<g transform="translate(%s %s) scale(%s)">%s</g>' % (f(t), f(t), f(scale), motif(key, "dark"))


def icon_svg(key, label, scale=TILE_GLYPH, rounded=True):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
            'role="img" aria-label="%s">%s</svg>' % (label, icon_inner(key, scale, rounded)))


# ---------------------------------------------------------------- text
class Type:
    def __init__(self, font_path):
        self.fonts = {}
        for w in (400, 500, 700):
            tt = TTFont(font_path)
            if "fvar" in tt:
                tt = instantiateVariableFont(tt, {"wght": w})
            tt.flavor = None
            buf = io.BytesIO()
            tt.save(buf)
            data = buf.getvalue()
            tt = TTFont(io.BytesIO(data))
            self.fonts[w] = (tt, hb.Font(hb.Face(data)))

    def path(self, s, weight, size, x, y):
        """Return (svg path data, advance end x)."""
        tt, hbf = self.fonts[weight]
        b = hb.Buffer()
        b.add_str(s)
        b.guess_segment_properties()
        hb.shape(hbf, b, {"kern": True, "liga": True})
        gs, order = tt.getGlyphSet(), tt.getGlyphOrder()
        k = size / tt["head"].unitsPerEm
        pen = SVGPathPen(gs, f)
        cx = x
        for info, pos in zip(b.glyph_infos, b.glyph_positions):
            tp = TransformPen(pen, (k, 0, 0, -k, cx + pos.x_offset * k, y - pos.y_offset * k))
            gs[order[info.codepoint]].draw(tp)
            cx += pos.x_advance * k
        return pen.getCommands(), cx

    def width(self, s, weight, size):
        return self.path(s, weight, size, 0, 0)[1]

    def text(self, s, weight, size, x, y, fill, anchor="start"):
        if anchor != "start":
            w = self.width(s, weight, size)
            x -= w if anchor == "end" else w / 2
        d, _ = self.path(s, weight, size, x, y)
        return '<path d="%s" fill="%s"/>' % (d, fill)


# ---------------------------------------------------------------- lockups
def lockup_h(T, key, endorser, name, mode, label):
    """Horizontal lockup: mark | deeplab <name>. Returns (svg, width, height)."""
    m = MODES[mode]
    d1, end = T.path(endorser, 700, TEXT_SIZE, TEXT_X, BASELINE)
    body = motif(key, mode) + '<path d="%s" fill="%s"/>' % (d1, m["word"])
    if name:
        d2, end = T.path(name, 400, TEXT_SIZE, end + NAME_GAP, BASELINE)
        body += '<path d="%s" fill="%s"/>' % (d2, m["name"])
    w = math.ceil(end)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d 64" width="%d" height="64" '
           'role="img" aria-label="%s">%s</svg>' % (w, w, label, body))
    return svg, w, 64


def lockup_stacked(T, keys, endorser, name, mode, label):
    """Stacked lockup: mark(s) on top, 'deeplab' then the product name, centred."""
    m = MODES[mode]
    ms = 96  # mark size (1.5x)
    gap_marks = 12
    marks_w = len(keys) * ms + (len(keys) - 1) * gap_marks
    w1 = T.width(endorser, 700, TEXT_SIZE)
    w2 = T.width(name, 400, TEXT_SIZE) if name else 0
    W = math.ceil(max(marks_w, w1, w2)) + 2
    cx = W / 2
    body = ""
    x = cx - marks_w / 2
    for k in keys:
        body += '<g transform="translate(%s 0) scale(1.5)">%s</g>' % (f(x), motif(k, mode))
        x += ms + gap_marks
    b1 = ms + 16 + 28  # top of 'd' ascender sits 16 below the mark
    body += T.text(endorser, 700, TEXT_SIZE, cx, b1, m["word"], "middle")
    H = b1 + 11
    if name:
        b2 = b1 + 44
        body += T.text(name, 400, TEXT_SIZE, cx, b2, m["name"], "middle")
        H = b2 + 11
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="%s">%s</svg>' % (W, H, W, H, label, body))
    return svg, W, H


# ---------------------------------------------------------------- output helpers
WRITTEN = []


def write(rel, data):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(p, mode) as fh:
        fh.write(data)
    WRITTEN.append(rel)


def png(rel, svg, width, height=None):
    data = cairosvg.svg2png(bytestring=svg.encode(), output_width=width,
                            output_height=height or None)
    write(rel, data)


def nest(svg_body_w_h, x, y, scale=1.0):
    """Place an (svg, w, h) lockup at x,y with a scale, returns markup."""
    svg, w, h = svg_body_w_h
    inner = svg[svg.index(">") + 1: svg.rindex("</svg>")]
    return '<g transform="translate(%s %s) scale(%s)">%s</g>' % (f(x), f(y), f(scale), inner)


# ---------------------------------------------------------------- products
def build_product(T, endorser, p):
    pid, key, name = p["id"], p["motif"], p["name"]
    full = "%s %s" % (endorser["name"], name)
    d = "products/%s/" % pid
    for mode, suf in (("light", ""), ("dark", "-dark")):
        s = mark_svg(key, mode, full)
        write(d + "%s-mark%s.svg" % (pid, suf), s + "\n")
        png(d + "%s-mark%s-512.png" % (pid, suf), s, 512, 512)
        lk = lockup_h(T, key, endorser["wordmark"], p["wordmark"], mode, full)
        write(d + "%s-logo%s.svg" % (pid, suf), lk[0] + "\n")
        png(d + "%s-logo%s.png" % (pid, suf), lk[0], lk[1] * 4, 256)
        st = lockup_stacked(T, [key], endorser["wordmark"], p["wordmark"], mode, full)
        write(d + "%s-logo-stacked%s.svg" % (pid, suf), st[0] + "\n")
        png(d + "%s-logo-stacked%s.png" % (pid, suf), st[0], st[1] * 2, st[2] * 2)
    icon = icon_svg(key, full)
    write(d + "%s-icon.svg" % pid, icon + "\n")
    png(d + "%s-icon-16.png" % pid, icon_svg(key, full, TILE_GLYPH_16), 16, 16)
    png(d + "%s-icon-32.png" % pid, icon, 32, 32)
    png(d + "%s-icon-180.png" % pid, icon_svg(key, full, rounded=False), 180, 180)
    png(d + "%s-icon-512.png" % pid, icon_svg(key, full, rounded=False), 512, 512)
    if p.get("readme") != "hand":
        write(d + "README.md", product_readme(endorser, p))


def product_readme(endorser, p):
    pid, name = p["id"], p["name"]
    full = "%s %s" % (endorser["name"], name)
    bundle = ""
    if p.get("bundle"):
        bundle = ("\nPart of the **%s %s** bundle (see `../%s/`).\n"
                  % (endorser["name"], p["bundle"].capitalize(), p["bundle"]))
    return f"""<p align="center"><img src="{pid}-logo.svg" alt="{full}" width="360"></p>

# {full}

{p['role']}.
{bundle}
Generated by `family/build.py` from `family/products.json`; don't edit these files by hand.
Naming, colours and usage rules: [BRAND.md](../../BRAND.md#product-family).

| File | Use |
|---|---|
| `{pid}-logo.svg` / `.png` | Horizontal lockup on white or light backgrounds |
| `{pid}-logo-dark.svg` / `.png` | Horizontal lockup on Ink or dark backgrounds |
| `{pid}-logo-stacked.svg` / `-dark.svg` (+ `.png`) | Stacked lockup for square spaces |
| `{pid}-mark.svg` / `-dark.svg` (+ `-512.png`) | Product mark alone, transparent |
| `{pid}-icon.svg` | Favicon / app icon (mark on an Ink rounded tile) |
| `{pid}-icon-16.png`, `-32.png` | Browser favicons (rounded tile, transparent corners) |
| `{pid}-icon-180.png`, `-512.png` | Apple touch / app icon (full Ink square, the OS rounds the corners) |

Hotlink base: `https://fkeil.github.io/deeplab-brand/products/{pid}/`. Shipped software bundles its own copy.
"""


def build_bundle(T, endorser, b, products):
    keys = [next(p["motif"] for p in products if p["id"] == m) for m in b["members"]]
    full = "%s %s" % (endorser["name"], b["name"])
    d = "products/%s/" % b["id"]
    for mode, suf in (("light", ""), ("dark", "-dark")):
        # horizontal: both marks side by side, then the wordmark
        mm = MODES[mode]
        offs = 64 + 8
        d1, end = T.path(endorser["wordmark"], 700, TEXT_SIZE, TEXT_X + offs, BASELINE)
        d2, end = T.path(b["wordmark"], 400, TEXT_SIZE, end + NAME_GAP, BASELINE)
        body = motif(keys[0], mode) + '<g transform="translate(%d 0)">%s</g>' % (offs, motif(keys[1], mode))
        body += '<path d="%s" fill="%s"/><path d="%s" fill="%s"/>' % (d1, mm["word"], d2, mm["name"])
        w = math.ceil(end)
        s = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d 64" width="%d" height="64" '
             'role="img" aria-label="%s">%s</svg>' % (w, w, full, body))
        write(d + "%s-logo%s.svg" % (b["id"], suf), s + "\n")
        png(d + "%s-logo%s.png" % (b["id"], suf), s, w * 4, 256)
        st = lockup_stacked(T, keys, endorser["wordmark"], b["wordmark"], mode, full)
        write(d + "%s-logo-stacked%s.svg" % (b["id"], suf), st[0] + "\n")
        png(d + "%s-logo-stacked%s.png" % (b["id"], suf), st[0], st[1] * 2, st[2] * 2)
    names = " and ".join("%s %s" % (endorser["name"], p["name"]) for p in products if p["id"] in b["members"])
    write(d + "README.md", f"""<p align="center"><img src="{b['id']}-logo.svg" alt="{full}" width="420"></p>

# {full} (bundle)

{names}, sold together. The bundle has no mark of its own: its lockup shows both product marks side by side.
Use it only where the bundle itself is meant (price lists, the bundle's product page). Each product keeps its own icon.

Generated by `family/build.py` from `family/products.json`; don't edit by hand.

| File | Use |
|---|---|
| `{b['id']}-logo.svg` / `-dark.svg` (+ `.png`) | Horizontal bundle lockup |
| `{b['id']}-logo-stacked.svg` / `-dark.svg` (+ `.png`) | Stacked bundle lockup |
""")


def build_master(T, endorser):
    for mode, suf in (("light", ""), ("dark", "-dark")):
        st = lockup_stacked(T, ["master"], endorser["wordmark"], None, mode, endorser["name"])
        write("logo/deeplab-logo-stacked%s.svg" % suf, st[0] + "\n")
        png("logo/deeplab-logo-stacked%s.png" % suf, st[0], st[1] * 2, st[2] * 2)


# ---------------------------------------------------------------- sheets
def sheet_overview(T, endorser, products, bundles):
    W = 1680
    pad = 64
    out = []
    y = pad
    out.append(T.text("DeepLab product family", 700, 40, pad, y + 36, INK))
    out.append(T.text("One platform, six products. Generated from family/products.json.", 400, 20, pad, y + 72, MUTED))
    y += 120
    # master logo row
    out.append(T.text("MASTER", 700, 13, pad, y, MUTED))
    master = lockup_h(T, "master", endorser["wordmark"], None, "light", "DeepLab")
    out.append(nest(master, pad, y + 20, 1.5))
    mst = lockup_stacked(T, ["master"], endorser["wordmark"], None, "light", "DeepLab")
    out.append(nest(mst, pad + 420, y + 12, 0.75))
    y += 20 + 150
    # product cards: 3 x 2
    out.append(T.text("PRODUCTS", 700, 13, pad, y, MUTED))
    y += 20
    cw, ch, gx, gy = (W - 2 * pad - 2 * 24) / 3, 230, 24, 24
    for i, p in enumerate(products):
        cx = pad + (i % 3) * (cw + gx)
        cy = y + (i // 3) * (ch + gy)
        out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="14" fill="#fff" stroke="%s"/>'
                   % (f(cx), f(cy), f(cw), ch, BORDER))
        out.append('<g transform="translate(%s %s) scale(1.5)">%s</g>' % (f(cx + 24), f(cy + 24), icon_inner(p["motif"])))
        lk = lockup_h(T, p["motif"], endorser["wordmark"], p["wordmark"], "light", "")
        sc = min(0.62, (cw - 48) / lk[1])
        out.append(nest(lk, cx + 24, cy + 140, sc))
        out.append(T.text(p["role"], 400, 15, cx + 24, cy + 205, MUTED))
        # small sizes next to the big icon
        out.append('<g transform="translate(%s %s) scale(0.5)">%s</g>' % (f(cx + 136), f(cy + 24), icon_inner(p["motif"])))
        out.append('<g transform="translate(%s %s) scale(0.25)">%s</g>' % (f(cx + 180), f(cy + 24), icon_inner(p["motif"], TILE_GLYPH_16)))
        out.append('<g transform="translate(%s %s) scale(0.75)">%s</g>' % (f(cx + 136), f(cy + 72), motif(p["motif"], "light")))
    y += 2 * ch + gy + 48
    # dark band
    bh = 330
    out.append('<rect x="0" y="%s" width="%s" height="%s" fill="%s"/>' % (y, W, bh, INK))
    out.append(T.text("ON DARK", 700, 13, pad, y + 40, "#94A3B8"))
    for i, p in enumerate(products):
        cx = pad + (i % 3) * (cw + gx)
        cy = y + 64 + (i // 3) * 120
        lk = lockup_h(T, p["motif"], endorser["wordmark"], p["wordmark"], "dark", "")
        out.append(nest(lk, cx, cy, min(1.0, (cw - 24) / lk[1])))
    y += bh + 48
    # bundle row
    for b in bundles:
        out.append(T.text("BUNDLE", 700, 13, pad, y, MUTED))
        keys = [next(p["motif"] for p in products if p["id"] == m) for m in b["members"]]
        st = lockup_stacked(T, keys, endorser["wordmark"], b["wordmark"], "light", "")
        out.append(nest(st, pad, y + 20, 0.8))
        out.append(T.text("%s %s = %s" % (endorser["name"], b["name"], " + ".join(
            "%s %s" % (endorser["name"], p["name"]) for p in products if p["id"] in b["members"])),
            400, 18, pad + st[1] * 0.8 + 40, y + 100, INK))
        out.append(T.text("Shared Watch motif: the eye. Endpoint = device pupil, Network = node corners.",
                          400, 16, pad + st[1] * 0.8 + 40, y + 130, MUTED))
        y += 20 + st[2] * 0.8 + 40
    H = int(y + pad - 40)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="DeepLab product family"><rect width="%d" height="%d" fill="%s"/>%s</svg>'
           % (W, H, W, H, W, H, PAPER, "".join(out)))
    write("family/family-overview.svg", svg + "\n")
    png("family/family-overview.png", svg, W, H)


def grid_panel(T, key, x, y, u, title):
    """Construction drawing of one mark at u px per grid unit."""
    o = ['<g transform="translate(%s %s)">' % (x, y)]
    S = 64 * u
    o.append('<rect width="%s" height="%s" fill="#fff" stroke="%s"/>' % (S, S, BORDER))
    for i in range(65):
        c = "#CBD5E1" if i % 8 == 0 else "#EEF1F5"
        o.append('<path d="M%s 0V%s M0 %sH%s" stroke="%s" stroke-width="1"/>' % (i * u, S, i * u, S, c))
    a, b = LIVE
    o.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="#DC2626" stroke-dasharray="6 4" stroke-width="1.5"/>'
             % (a * u, a * u, (b - a) * u, (b - a) * u))
    o.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="#B45309" stroke-dasharray="2 4" stroke-width="1.5"/>'
             % (KEY * u, KEY * u, (64 - 2 * KEY) * u, (64 - 2 * KEY) * u))
    o.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="#B45309" stroke-dasharray="2 4" stroke-width="1.5"/>'
             % (32 * u, 32 * u, (32 - KEY) * u))
    # 2:1 slope guides through the centre (the master's layer angle)
    for s in (1, -1):
        o.append('<path d="M0 %s L%s %s" stroke="#7C3AED" stroke-opacity=".35" stroke-width="1.5"/>'
                 % ((32 + s * 16) * u, S, (32 - s * 16) * u))
    o.append('<g transform="scale(%s)" opacity=".92">%s</g>' % (u, motif(key, "light")))
    o.append("</g>")
    o.append(T.text(title, 700, 18, x, y - 14, INK))
    return "".join(o)


def sheet_system(T):
    W, H = 1680, 1060
    o = ['<rect width="%d" height="%d" fill="%s"/>' % (W, H, PAPER)]
    o.append(T.text("Family construction", 700, 40, 64, 100, INK))
    o.append(T.text("64-unit grid. Live area 6-58 (red). Stroke 5.5, round caps and joins; stroke centres on the 8.75 keylines (amber). "
                    "Angles 0, 45, 90 degrees or the 2:1 layer slope (violet).", 400, 18, 64, 136, MUTED))
    o.append(grid_panel(T, "strata", 64, 200, 6, "Mark grid (Strata shown)"))
    # tile template
    x0 = 520
    o.append(T.text("App icon / favicon tile", 700, 18, x0, 186, INK))
    o.append('<g transform="translate(%d 200) scale(5)">%s'
             '<rect x="8" y="8" width="48" height="48" fill="none" stroke="#DC2626" stroke-width=".3" stroke-dasharray="1.2 .8"/></g>'
             % (x0, icon_inner("aiguard")))
    o.append(T.text("Ink tile, radius 14/64. Glyph at 75 % (8-56).", 400, 15, x0, 548, MUTED))
    o.append(T.text("16 px favicon: glyph at 87.5 %.", 400, 15, x0, 570, MUTED))
    # 16/32 strip
    for i, (k, sc) in enumerate((("central", TILE_GLYPH_16), ("strata", TILE_GLYPH_16), ("control", TILE_GLYPH_16),
                                 ("aiguard", TILE_GLYPH_16), ("endpoint-watch", TILE_GLYPH_16), ("network-watch", TILE_GLYPH_16))):
        o.append('<g transform="translate(%d 590) scale(.25)">%s</g>' % (x0 + i * 24, icon_inner(k, sc)))
        o.append('<g transform="translate(%d 616) scale(.5)">%s</g>' % (x0 + i * 40, icon_inner(k)))
    # colour roles
    x1 = 900
    o.append(T.text("Colour roles in a mark", 700, 18, x1, 186, INK))
    roles = [("Core", SIGNAL, 1, "Signal 100 %: solid forms, the product's subject"),
             ("Support", SIGNAL, .7, "Signal 70 % (75 % on dark): containers, secondary strokes"),
             ("Spark", ACCENT, 1, "Accent cyan: exactly one element, what is protected or watched")]
    for i, (n, c, op, d) in enumerate(roles):
        yy = 210 + i * 70
        o.append('<rect x="%d" y="%d" width="52" height="52" rx="10" fill="%s" fill-opacity="%s"/>' % (x1, yy, c, op))
        o.append(T.text(n, 700, 17, x1 + 68, yy + 22, INK))
        o.append(T.text(d, 400, 15, x1 + 68, yy + 44, MUTED))
    o.append(T.text("On dark: core = Signal light #5B8DEF; cyan unchanged. No gradients, shadows or outlines.", 400, 15, x1, 438, MUTED))
    # lockup spec
    y2 = 700
    o.append(T.text("Lockup", 700, 18, 64, y2 - 14, INK))
    lk = lockup_h(T, "strata", "deeplab", "strata", "light", "")
    sc = 2.5
    o.append('<rect x="64" y="%d" width="%s" height="%s" fill="#fff" stroke="%s"/>' % (y2, f(lk[1] * sc + 2 * 11.5 * sc), f(64 * sc + 2 * 11.5 * sc), BORDER))
    gx, gy = 64 + 11.5 * sc, y2 + 11.5 * sc
    o.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="#DC2626" stroke-dasharray="6 4"/>' % (f(gx), f(gy), f(lk[1] * sc), f(64 * sc)))
    o.append(nest(lk, gx, gy, sc))
    for xx, lab in ((0, "0"), (64, "64"), (76, "76: wordmark"), ):
        o.append('<path d="M%s %s V%s" stroke="#7C3AED" stroke-width="1"/>' % (f(gx + xx * sc), f(gy - 8), f(gy + 64 * sc + 8)))
        o.append(T.text(lab, 400, 13, gx + xx * sc + 4, gy + 64 * sc + 22, "#7C3AED"))
    o.append('<path d="M%s %s H%s" stroke="#7C3AED" stroke-width="1"/>' % (f(gx - 8), f(gy + 44 * sc), f(gx + lk[1] * sc + 8)))
    o.append(T.text("baseline 44", 400, 13, gx + lk[1] * sc + 12, gy + 44 * sc + 4, "#7C3AED"))
    o.append(T.text("Inter Bold 38 \"deeplab\" (Ink) + one word space (10.7) + Inter Regular 38 product name (Signal), all lowercase, outlined.",
                    400, 15, 64, y2 + 64 * sc + 2 * 11.5 * sc + 30, MUTED))
    o.append(T.text("Clear space: 11.5 units (one layer step of the master mark) on every side (white panel); the dashed box is the lockup itself.",
                    400, 15, 64, y2 + 64 * sc + 2 * 11.5 * sc + 54, MUTED))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="DeepLab family construction">%s</svg>' % (W, H, W, H, "".join(o)))
    write("family/family-system.svg", svg + "\n")
    png("family/family-system.png", svg, W, H)


def template_svg():
    """Working template for drawing a new product mark (guides locked in their own group)."""
    g = []
    for i in range(0, 65, 4):
        g.append('<path d="M%d 0V64M0 %dH64" stroke="#CBD5E1" stroke-width=".1"/>' % (i, i))
    a, b = LIVE
    g.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#DC2626" stroke-width=".2"/>' % (a, a, b - a, b - a))
    g.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="#B45309" stroke-width=".15" stroke-dasharray=".6 .6"/>'
             % (f(KEY), f(KEY), f(64 - 2 * KEY), f(64 - 2 * KEY)))
    g.append('<circle cx="32" cy="32" r="%s" fill="none" stroke="#B45309" stroke-width=".15" stroke-dasharray=".6 .6"/>' % f(32 - KEY))
    g.append('<path d="M0 48 64 16M0 16 64 48" stroke="#7C3AED" stroke-opacity=".4" stroke-width=".15"/>')
    g.append('<rect x="8" y="8" width="48" height="48" fill="none" stroke="#0EA5E9" stroke-width=".15" stroke-dasharray="1 .5"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="640" height="640">\n'
            '<!-- DeepLab product mark template. Red: live area 6-58 (nothing, stroke included, leaves it).\n'
            '     Amber: keylines at 8.75 for stroke centres (square and circle). Violet: 2:1 slopes.\n'
            '     Blue: what the 48-unit tile glyph area covers after scaling (icon = 75 %).\n'
            '     Stroke 5.5, round caps and joins. Colours: core #2F6FED, support #2F6FED at 70 %, spark #22C3EE (one element).\n'
            '     Delete the guides group before export; add the new motif to family/build.py. -->\n'
            '<g id="guides">' + "".join(g) + '</g>\n'
            '<g id="artwork">\n'
            '  <!-- example: a container in support tone, a solid core, one cyan spark -->\n'
            '  <rect x="8.75" y="8.75" width="46.5" height="46.5" rx="10" fill="none" stroke="#2F6FED" stroke-opacity=".7" '
            'stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>\n'
            '  <circle cx="32" cy="32" r="9" fill="#2F6FED"/>\n'
            '  <circle cx="44" cy="20" r="4" fill="#22C3EE"/>\n'
            '</g>\n</svg>\n')


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", default=os.environ.get("INTER_FONT"),
                    help="Inter variable font (ttf or woff2); or set INTER_FONT")
    ap.add_argument("--table", default=os.path.join(ROOT, "family", "products.json"))
    a = ap.parse_args()
    if not a.font:
        sys.exit("need --font /path/to/Inter variable font (or INTER_FONT)")
    T = Type(a.font)
    tbl = json.load(open(a.table))
    endorser, products, bundles = tbl["endorser"], tbl["products"], tbl.get("bundles", [])
    for p in products:
        build_product(T, endorser, p)
    for b in bundles:
        build_bundle(T, endorser, b, products)
    build_master(T, endorser)
    sheet_overview(T, endorser, products, bundles)
    sheet_system(T)
    write("family/template-mark.svg", template_svg())
    owned = {p["id"] for p in products} | {b["id"] for b in bundles}
    for d in sorted(os.listdir(os.path.join(ROOT, "products"))):
        if os.path.isdir(os.path.join(ROOT, "products", d)) and d not in owned:
            print("warning: products/%s/ is not in the names table (renamed? delete it by hand)" % d)
    print("wrote %d files" % len(WRITTEN))


if __name__ == "__main__":
    main()
