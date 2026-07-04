"""Django admin widget for editing a feature Config JSONField.

``ConfigEditorWidget`` renders the schema-driven admin UI (docs/attributes-admin-ui.md
Stage 3): a ``<textarea>`` holding the config JSON (works with no JS —
progressive enhancement), a mount point, and ``json_script`` blocks (declarations
from :func:`form_declarations`, the current config, the resolved locale and the
merged message catalogs). An inline ES-module dynamically imports the committed
bundle and calls ``window.StapelAttributes.mountConfigEditor``; on change it
writes the config JSON back into the textarea, so the normal form field submits.

This module imports Django at import time (it is a widget); the package
``__init__`` exports it lazily so ``import stapel_attributes`` stays Django-free.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from django import forms
from django.templatetags.static import static
from django.utils.html import format_html, json_script
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

_STATIC_DIR = Path(__file__).resolve().parent / "static" / "stapel_attributes"


def _builtin_locale(code: str) -> Dict[str, str]:
    path = _STATIC_DIR / "locales" / f"{code}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _messages() -> Dict[str, Dict[str, str]]:
    """Built-in en+ru plus ``ADMIN_LOCALES`` (dict inline or a static path).

    Raw catalogs are handed to the client, which merges the requested locale
    over the ``en`` base (partial host locales supplement, never fork).
    """
    from stapel_attributes.conf import attributes_settings

    messages: Dict[str, Dict[str, str]] = {"en": _builtin_locale("en"), "ru": _builtin_locale("ru")}
    for code, val in (attributes_settings.ADMIN_LOCALES or {}).items():
        if isinstance(val, dict):
            messages[code] = dict(val)
        elif isinstance(val, str):
            from django.contrib.staticfiles import finders

            found = finders.find(val)
            if found:
                messages[code] = json.loads(Path(found).read_text(encoding="utf-8"))
    return messages


class ConfigEditorWidget(forms.Widget):
    """Schema-driven config editor for a feature ``config`` JSONField."""

    template_name = None  # rendered directly

    def __init__(self, attrs: Any = None, *, translate_mode: str = "all", prefix_name: str = "") -> None:
        super().__init__(attrs)
        self.translate_mode = translate_mode
        self.prefix_name = prefix_name

    @property
    def media(self) -> forms.Media:
        from stapel_attributes.conf import attributes_settings

        css = ["stapel_attributes/admin-tokens.css", *(attributes_settings.ADMIN_EXTRA_CSS or [])]
        js = list(attributes_settings.ADMIN_EXTRA_JS or [])  # the ESM bundle is imported inline
        return forms.Media(css={"all": css}, js=js)

    def value_from_datadict(self, data, files, name):
        return data.get(name)

    def render(self, name, value, attrs=None, renderer=None) -> str:
        from stapel_attributes.config_form import form_declarations

        # Normalize the incoming config (dict from the model, or a JSON string).
        config: Any
        if isinstance(value, dict):
            config = value
        elif value:
            try:
                config = json.loads(value)
            except (TypeError, ValueError):
                config = None
        else:
            config = None

        config_text = json.dumps(config, ensure_ascii=False) if config is not None else ""
        slug = config.get("type", "") if isinstance(config, dict) else ""
        field_id = (attrs or {}).get("id") or f"id_{name}"
        mount_id = f"{field_id}-mount"
        data_id = f"{field_id}-data"

        payload = {
            "declarations": form_declarations(),
            "config": config,
            "slug": slug,
            "locale": get_language() or "en",
            "messages": _messages(),
            "prefixName": self.prefix_name,
            "translateMode": self.translate_mode,
        }

        textarea = format_html(
            '<textarea name="{}" id="{}" rows="6" class="stapel-attr-fallback"'
            ' style="width:100%;font-family:monospace">{}</textarea>',
            name, field_id, config_text,
        )
        mount = format_html('<div id="{}" class="stapel-attr-mount"></div>', mount_id)
        data_block = json_script(payload, data_id)
        bundle_url = static("stapel_attributes/attributes-admin.js")

        # Inline ES module: dynamic-import the bundle (deduped by URL), mount the
        # editor, hide the fallback textarea, and sync config JSON back to it.
        init = format_html(
            '<script type="module">'
            'import({bundle!r}).then(function(m){{'
            'var d=JSON.parse(document.getElementById("{data_id}").textContent);'
            'var host=document.getElementById("{mount_id}");'
            'var ta=document.getElementById("{field_id}");'
            'if(!host||!ta||!d.slug||!d.declarations[d.slug]){{return;}}'
            'ta.style.display="none";'
            'm.mountConfigEditor(host,{{declaration:d.declarations[d.slug],slug:d.slug,'
            'config:d.config,locale:d.locale,messages:d.messages,prefixName:d.prefixName,'
            'translateMode:d.translateMode,onChange:function(cfg){{ta.value=JSON.stringify(cfg);}}}});'
            '}});'
            "</script>",
            bundle=bundle_url, data_id=data_id, mount_id=mount_id, field_id=field_id,
        )
        return mark_safe(textarea + str(mount) + str(data_block) + str(init))


def get_config_editor_widget(name: str = "config") -> type:
    """Resolve the config-editor widget, honouring ``ADMIN_WIDGETS`` overrides
    (dotted-path merge over the builtin) — swap the widget without a fork."""
    from django.utils.module_loading import import_string

    from stapel_attributes.conf import attributes_settings

    override = (attributes_settings.ADMIN_WIDGETS or {}).get(name)
    if override:
        return import_string(override) if isinstance(override, str) else override
    return ConfigEditorWidget


__all__ = ["ConfigEditorWidget", "get_config_editor_widget"]
