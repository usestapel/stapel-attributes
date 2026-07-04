// Shared types. The declaration shapes mirror the Python side 1:1
// (stapel_attributes/config_form.py -> form_declarations()).

/** A field-kind understood by the config editor (LOGIC-NOTES §1). */
export type FieldKind =
  | "number"
  | "text"
  | "checkbox"
  | "translatable_text"
  | "number_options"
  | "string_options"
  | "color_options"
  | "select"
  | "select_options_with_default"
  | "max_selected_dropdown"
  | "hierarchical_options"
  | "timestamp"
  | "timestamp_array";

/** Inline option for the fixed `select` kind. */
export interface InlineOption {
  value: string;
  label: string;
}

/** One declared config-form field (mirrors Python FormField.to_dict()). */
export interface FormFieldDecl {
  name: string;
  kind: FieldKind | string;
  label_key: string;
  required?: boolean;
  default?: unknown;
  params?: {
    step?: number;
    itemType?: "number";
    placeholder?: string;
    options?: InlineOption[];
    [k: string]: unknown;
  };
}

/** A type's full config-form declaration (one entry of form_declarations()). */
export interface TypeDecl {
  label_key: string;
  fields: FormFieldDecl[];
}

/** slug -> declaration. */
export type FormDeclarations = Record<string, TypeDecl>;

/** A feature config object (has a `type` discriminator + kind-specific keys). */
export interface FeatureConfig {
  type: string;
  [k: string]: unknown;
}

/** A value DTO (has a `type` discriminator + a `value`). Empty is `null`. */
export interface ValueDto {
  type: string;
  value: unknown;
}

/** i18n locale catalog: flat key -> template string (with `{param}` slots). */
export type Locale = Record<string, string>;

/** Minimal i18n surface consumed by components (the I18n class satisfies it). */
export interface I18nLike {
  t(key: string, params?: Record<string, unknown>): string;
  readonly locale?: string;
}

/** Mount config handed to a widget from the server (via json_script). */
export interface MountConfig {
  declarations?: FormDeclarations;
  config?: FeatureConfig | null;
  locale?: string;
  messages?: Record<string, Locale>;
  csrfToken?: string;
  errorEndpoint?: string;
}
