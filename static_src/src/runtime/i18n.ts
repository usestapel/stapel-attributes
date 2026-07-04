// Mini i18n engine (LOGIC-NOTES LN-R04, docs decision 2): dictionary +
// `{param}` interpolation + fallback to the key itself. Partial locales merge
// over the `en` base, so a host `ADMIN_LOCALES` entry may translate only some
// keys and inherit the rest — no fork.
import type { Locale } from "../types.js";

export class I18n {
  readonly locale: string;
  private readonly catalog: Locale;

  constructor(locale: string, messages: Record<string, Locale> = {}) {
    this.locale = locale;
    const base = messages["en"] ?? {};
    const requested = messages[locale] ?? {};
    // requested (possibly partial) merges over the en base.
    this.catalog = { ...base, ...requested };
  }

  /** Translate `key`, interpolating `{param}` slots; unknown key -> the key. */
  t(key: string, params?: Record<string, unknown>): string {
    let out = this.catalog[key] ?? key;
    if (params) {
      for (const [name, value] of Object.entries(params)) {
        out = out.split(`{${name}}`).join(String(value));
      }
    }
    return out;
  }

  has(key: string): boolean {
    return key in this.catalog;
  }
}
