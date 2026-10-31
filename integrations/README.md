# Where the brand is applied

| App | Container | What | Files on the server | Undo |
|---|---|---|---|---|
| Authentik | LXC 119 | Brand: title, logo (`%(theme)s`), favicon, flow background, primary-color CSS. Apps: names, groups, icons, descriptions, publisher | DB (Admin → System → Brands, Applications) | Old values in `/media/brand-backup-2026-10-31.json` and `/media/apps-backup-2026-10-31.json` in `authentik-server-1` |
| Gitea | LXC 108 | Logo, favicon, primary color (`templates/custom/header.tmpl`) | `capynote_gitea-data` volume → `custom/` (logo files from `../logo/`) | Delete `custom/public/assets/img/*` and `custom/templates/custom/header.tmpl`, restart |
| Guacamole | LXC 101 | Extension `deeplab-branding.jar` (zip of `guacamole/`): logo, background, colors, name "DeepLab Remote", favicon | `/etc/guacamole/extensions/deeplab-branding.jar` | Delete the jar, `systemctl restart tomcat` |
| Vaultwarden | LXC 103 | Primary colors | `/opt/vaultwarden/data/templates/scss/user.vaultwarden.scss.hbs` | Delete it, restart `vaultwarden` |
| Roundcube | LXC 105 | Logo (light/dark), favicon, name "DeepLab Webmail" | `/opt/roundcube/config/custom.inc.php` | Restore `custom.inc.php.bak-brand-20261031`, `docker restart roundcube` |
