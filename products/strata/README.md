# DeepLab Strata

Product name chosen 2026-11-01. Replaces **DeepLab BKP**: the product now covers backup, disaster recovery, disk images (P2V/V2V/V2P), boot verification, Microsoft 365 backup, immutability, RMM and a built-in WAF, so "BKP" no longer fits.

## Naming
- Full name: **DeepLab Strata**. Short form after first mention: **Strata**.
- Never "Strata BKP", "DeepLab BKP" or "DLBKP" in anything a user sees.
- Tagline: *Every layer of your IT, protected.*
- Internal identifiers (`dlbkp-agent`, `dlbkp-server`, service names, binaries, install paths, Go module, repo name) **stay unchanged for now**. Installed agents auto-update, so renaming them needs its own migration plan.

## Logo
| File | Use |
|---|---|
| `strata-logo.svg` / `.png` | Lockup on white or light backgrounds |
| `strata-logo-dark.svg` / `.png` | Lockup on Ink or dark backgrounds |
| `strata-icon.svg`, `strata-icon-512.png` | App icon, favicon, installer icon, tray icon (replaces the purple "DB" icon) |

Hotlink base: `https://fkeil.github.io/deeplab-brand/products/strata/`. For shipped software, copy the files into the product (don't hotlink from installed agents or the portal).

## Colors and type
Same as the company brand ([../../BRAND.md](../../BRAND.md), [../../tokens.css](../../tokens.css)):

| Token | Hex | In the portal |
|---|---|---|
| Ink | `#0F1729` | Sidebar, top bar, dark surfaces (was `#141a26`) |
| Signal | `#2F6FED` | Primary buttons, links, active nav (unchanged) |
| Signal hover | `#2559C4` | Hover / pressed (unchanged) |
| Signal light | `#5B8DEF` | Blue on dark backgrounds |
| Accent | `#22C3EE` | Highlights on dark only, never text on white |
| Paper | `#F5F6F8` | Page background (unchanged) |
| Text | `#0F1729` | Body text (was `#1d2330`) |
| Muted | `#64748B` | Secondary text |
| Status | `#15803D` / `#B45309` / `#DC2626` | Success / warning / danger |

Fonts: **Inter** (UI, headings), **JetBrains Mono** (IDs, hostnames, logs). Bundle the font files with the portal; don't load them from Google at runtime.

## Where it must change
Portal (login, header, sidebar, page titles, favicon), setup/"name your service" defaults, installers (Windows `.exe` metadata and icon, macOS/Linux banners), tray app, alert e-mails and webhooks, recovery ISO boot menu/splash, docs, README, `assets/icon.svg`.
