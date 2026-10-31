# DeepLab brand guide: "Signal"

Chosen 2026-10-31. Calm, technical, dependable: navy and blue, one cyan highlight.

## Name
- In text: **DeepLab** (capital D, capital L). Products: **DeepLab BKP**.
- In the logo: lowercase **deeplab** wordmark.
- Domain for services: `deeplab.work`.

## Logo
The mark is three stacked layers (depth, layered backups): a solid diamond and two chevrons; the bottom one is cyan.

| File | Use |
|---|---|
| `logo/deeplab-logo.svg` | Mark + wordmark, on white or light backgrounds |
| `logo/deeplab-logo-dark.svg` | Mark + wordmark, on Ink or dark backgrounds |
| `logo/deeplab-mark.svg` / `deeplab-mark-dark.svg` | Mark alone (avatars, app icons, small spaces) |
| `logo/favicon.svg`, `favicon-32.png`, `favicon-192.png` | Browser tab icon (mark on an Ink rounded square) |
| `logo/app-icon-512.png`, `apple-touch-icon.png` | App / home-screen icon (full Ink square, the OS rounds the corners) |
| `logo/deeplab-logo.png`, `deeplab-logo-dark.png` | PNG versions of the full logo (904×256, transparent) for apps that don't take SVG |
| `logo/deeplab-mark-512.png`, `deeplab-mark-dark-512.png` | PNG mark (transparent) |

Rules:
- Keep clear space around the logo of at least the height of one chevron.
- Don't recolor, stretch, rotate or add effects. Use the dark version on dark backgrounds instead.
- Minimum size: mark 16 px, full logo 96 px wide.
- The wordmark is outlined Inter Bold (no font needed to display it).

## Colors
| Name | Hex | Use |
|---|---|---|
| Ink | `#0F1729` | Dark surfaces, sidebars, headings on light |
| Signal | `#2F6FED` | Primary: buttons, links, brand moments |
| Signal hover | `#2559C4` | Hover / pressed |
| Signal light | `#5B8DEF` | Brand blue on dark backgrounds |
| Accent | `#22C3EE` | Highlights on dark only. Never as text on white |
| Paper | `#F5F6F8` | Light page background |
| Muted text | `#64748B` | Secondary text |
| Border | `#E2E5EA` | Lines, dividers |
| Success / Warning / Danger | `#15803D` / `#B45309` / `#DC2626` | Status only |

Contrast (WCAG): white on Signal 4.55:1 (AA), white on Signal hover 6.35:1, Ink on white 17.9:1, Accent on Ink 8.6:1, Accent on white **2.1:1 (don't)**.

Rough ratio: 60% Paper/white, 30% Ink, 10% Signal, with Accent as a small spark.

## Type
- **Inter**: headings (Bold 700, slight negative tracking) and body (Regular 400, Medium 500 for UI labels).
- **JetBrains Mono**: code, IDs, hostnames, log output.
- Both are free (SIL Open Font License, Google Fonts).

## Voice
Plain, precise, reassuring. Say what happened and what to do next. No hype.
Example: "Backup finished. 3 files skipped, see details." Not: "Awesome! Your data is supercharged!"

## Applying it
- `tokens.css` has every value as CSS variables.
- **DeepLab BKP portal:** already uses Signal blue. To align it: sidebar `#141A26` to Ink `#0F1729`, text `#1D2330` to Ink, system font to Inter, and replace the purple "DB" icon with the mark. (Not done; product work happens in its own thread.)
- **Cloudflare Access login page:** see `cloudflare-login.md`.
