// Test dialog — live value-editor for a config + a JSON DTO preview
// (docs "Test-диалог с live-рендером value-editor'а и DTO-выводом").
import { openDialog } from "./runtime/dialog.js";
import { resolveValueEditor } from "./registry.js";
import type { FeatureConfig, I18nLike } from "./types.js";

export function openTestDialog(config: FeatureConfig, i18n: I18nLike): () => void {
  const wrap = document.createElement("div");

  const title = document.createElement("h3");
  title.textContent = i18n.t("admin.attributes.test.title");

  const editorHost = document.createElement("div");
  const dtoLabel = document.createElement("div");
  dtoLabel.style.marginTop = "12px";
  dtoLabel.style.color = "var(--stapel-color-text-muted, #6b7280)";
  dtoLabel.textContent = i18n.t("admin.attributes.test.dto");

  const pre = document.createElement("pre");
  pre.textContent = "null";

  const editor = resolveValueEditor(config.type)({
    config,
    i18n,
    onChange: (dto) => {
      pre.textContent = JSON.stringify(dto, null, 2);
    },
  });
  editorHost.appendChild(editor);

  wrap.append(title, editorHost, dtoLabel, pre);
  return openDialog(wrap);
}
