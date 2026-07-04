// Key-derivation & translation-key primitives, ported 1:1 (LOGIC-NOTES
// LN-C01/LN-R05..R09). These are the highest-fidelity requirement of the port:
// they decide option value keys and the `feature.<slug>.` prefixing. Preserve
// exactly — including the no-dedup / no-trim behavior (LN-B09).

/** LN-C01/LN-R09: lowercase, collapse whitespace runs to `_`, strip anything
 *  not a Unicode letter/number/underscore. No dedup, no `_`-collapse, no trim. */
export function labelToValue(label: string): string {
  return label
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^\p{L}\p{N}_]/gu, "");
}

/** LN-R06: title translation key from a slug. `'feature.' + slug` with
 *  whitespace/hyphen runs collapsed to `_`. */
export function slugToTranslationKey(slug: string): string {
  return "feature." + slug.toLowerCase().replace(/[\s-]+/g, "_");
}

/** LN-R08: slug formatting — lowercase, spaces->`_`, strip non `[a-z0-9_-]`. */
export function formatSlug(value: string): string {
  return value
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_-]/g, "");
}

/** LN-C18: add `prefix` to `label` unless empty or already prefixed. */
export function addPrefix(label: string, prefix: string): string {
  if (!prefix || !label || label.startsWith(prefix)) return label;
  return prefix + label;
}

/** LN-C18: strip `prefix` from `label` only if present. */
export function removePrefix(label: string, prefix: string): string {
  return prefix && label.startsWith(prefix) ? label.substring(prefix.length) : label;
}

interface OptionLike {
  label?: string;
  children?: OptionLike[];
  [k: string]: unknown;
}

/** LN-R05 (P1): recursively prefix option `label`s (never value/icon), guarded
 *  by `startsWith` so it is idempotent (won't double-prefix P2 output). Mutates
 *  the passed array — callers deep-clone first for payload-only transforms. */
export function addPrefixToOptions(options: OptionLike[], prefix: string): void {
  for (const opt of options) {
    if (opt.label && !opt.label.startsWith(prefix)) {
      opt.label = prefix + opt.label;
    }
    if (Array.isArray(opt.children)) {
      addPrefixToOptions(opt.children, prefix);
    }
  }
}
