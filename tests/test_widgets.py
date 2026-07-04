"""Stage 3 — Django ConfigEditorWidget (docs/attributes-admin-ui.md §4)."""
import json


def test_render_has_textarea_json_script_mount_and_module():
    from stapel_attributes.widgets import ConfigEditorWidget

    html = ConfigEditorWidget().render("config", {"type": "int", "min": 1})
    # Progressive enhancement: a textarea carries the config JSON (works w/o JS).
    assert '<textarea name="config"' in html
    assert '"type": "int"' in html or '"type":"int"' in html
    # json_script block with the mount data + an ES-module init.
    assert 'id="id_config-data"' in html
    assert 'id="id_config-mount"' in html
    assert 'type="module"' in html
    assert "mountConfigEditor" in html
    assert "attributes-admin.js" in html


def test_render_embeds_declarations_config_locale_messages():
    from stapel_attributes.widgets import ConfigEditorWidget

    html = ConfigEditorWidget().render("config", {"type": "select", "options": [{"value": "a"}]})
    # Extract the json_script payload.
    start = html.index('id="id_config-data"')
    body = html[start:]
    text = body[body.index(">") + 1 : body.index("</script>")]
    payload = json.loads(text)
    assert payload["slug"] == "select"
    assert "select" in payload["declarations"]
    assert payload["config"] == {"type": "select", "options": [{"value": "a"}]}
    assert "en" in payload["messages"] and "ru" in payload["messages"]
    assert payload["messages"]["en"]["admin.attributes.type.select"] == "Select"


def test_empty_value_renders_empty_textarea_no_crash():
    from stapel_attributes.widgets import ConfigEditorWidget

    html = ConfigEditorWidget().render("config", None)
    assert "<textarea" in html  # empty but present; module init early-returns (no slug)


def test_media_includes_tokens_and_extra_assets(settings):
    from stapel_attributes.widgets import ConfigEditorWidget

    settings.STAPEL_ATTRIBUTES = {"ADMIN_EXTRA_CSS": ["host/x.css"], "ADMIN_EXTRA_JS": ["host/y.js"]}
    media = ConfigEditorWidget().media
    css = media.render_css()
    assert any("admin-tokens.css" in str(c) for c in css)
    assert any("host/x.css" in str(c) for c in css)
    assert any("host/y.js" in str(j) for j in media.render_js())


def test_admin_locales_merge(settings):
    from stapel_attributes.widgets import _messages

    settings.STAPEL_ATTRIBUTES = {"ADMIN_LOCALES": {"de": {"admin.attributes.add": "Hinzufügen"}}}
    msgs = _messages()
    assert msgs["de"] == {"admin.attributes.add": "Hinzufügen"}
    assert "en" in msgs and "ru" in msgs  # builtins still present


def test_admin_widgets_override_resolves(settings):
    from stapel_attributes.widgets import ConfigEditorWidget, get_config_editor_widget

    assert get_config_editor_widget("config") is ConfigEditorWidget

    class MyWidget(ConfigEditorWidget):
        pass

    settings.STAPEL_ATTRIBUTES = {"ADMIN_WIDGETS": {"config": MyWidget}}
    assert get_config_editor_widget("config") is MyWidget


def test_value_from_datadict_reads_textarea():
    from stapel_attributes.widgets import ConfigEditorWidget

    assert ConfigEditorWidget().value_from_datadict({"config": '{"type":"int"}'}, {}, "config") == '{"type":"int"}'


def test_widget_import_is_lazy_django_free():
    # Importing the package must not import the Django-dependent widgets module.
    import importlib
    import sys

    for mod in ("stapel_attributes", "stapel_attributes.widgets"):
        sys.modules.pop(mod, None)
    importlib.import_module("stapel_attributes")
    assert "stapel_attributes.widgets" not in sys.modules
    # Accessing the lazy attribute triggers the import.
    import stapel_attributes

    assert stapel_attributes.ConfigEditorWidget is not None
    assert "stapel_attributes.widgets" in sys.modules
