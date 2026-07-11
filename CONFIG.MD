# CONFIG.MD — stapel-attributes

Config registry for **stapel-attributes** (`static-scaffold-and-config.md` §2).
One row per configuration key the module reads, its **source** (`env` = the
process environment / the `STAPEL_ATTRIBUTES` settings dict), what it is for,
whether it is required, and its default.

stapel-attributes is an **L1 library** — no models, migrations, views, urls or
comm surface of its own; it is imported by stapel-categories / stapel-listings /
stapel-tasks. It is therefore **headless**: the scaffolder installs it as a pip
dependency but mounts it in neither `INSTALLED_APPS` nor the URL conf.

Every key is read through `attributes_settings`
(`stapel_attributes.conf.AppSettings`, namespace `STAPEL_ATTRIBUTES`).
Resolution order per key: `settings.STAPEL_ATTRIBUTES` dict → a flat Django
setting of the same name → environment variable → the default below.

## stapel-attributes

| Key | Source | Purpose | Required | Default |
|-----|--------|---------|----------|---------|
| EXTRA_TYPES | env | extra feature types MERGED over the built-ins (dotted paths to a BaseFeatureType subclass or a registering module). | no | [] |
| ADMIN_LOCALES | env | extra/override admin locales MERGED over built-in en+ru (lang → static path or inline dict). | no | {} |
| ADMIN_WIDGETS | env | override the Django config widget per use, MERGED (name → dotted path). | no | {} |
| ADMIN_EXTRA_CSS | env | extra CSS assets appended to the widget Media. | no | [] |
| ADMIN_EXTRA_JS | env | extra JS assets appended to the widget Media. | no | [] |
