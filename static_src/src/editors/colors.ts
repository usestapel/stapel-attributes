// Ported 1:1 from the legacy color_mappings.js (LOGIC-NOTES LN-X01..X03). The
// value-editor uses THIS table — `custom` has a conic-gradient here (18/18),
// unlike feature_types.js's copy.

export const SIMPLE_COLORS: readonly string[] = [
  "black", "white", "gray", "silver",
  "red", "pink", "orange", "yellow",
  "green", "blue", "purple", "brown",
  "gold", "beige", "turquoise",
  "clear", "multicolor", "custom",
];

export const SIMPLE_COLOR_STYLES: Record<string, string> = {
  black: "#222222",
  white: "#FFFFFF",
  gray: "#A0A0A0",
  silver: "linear-gradient(135deg, #797979 10%, #FFFFFF 60%, #C0C0C0 100%)",
  red: "#F35555",
  pink: "#FFC0CB",
  orange: "#FFA500",
  yellow: "#FFFF00",
  green: "#0ED70E",
  blue: "#4285F4",
  purple: "#8A73FF",
  brown: "#B1662A",
  gold: "linear-gradient(135deg, #F1A100 10%, #FFF4AD 60%, #FFC200 100%)",
  beige: "#DDCEBA",
  turquoise: "#4DC7C2",
  clear: "linear-gradient(135deg, #FFFFFF 40%, #E1E1E1 50%, #FFFFFF 60%)",
  multicolor:
    "linear-gradient(135deg, #FF6B6B 20%, #FF9E4D 30%, #FFE75A 40%, #6EE87A 50%, #63D8FF 60%, #5C7CFF 70%, #C07CFF 80%)",
  custom: "conic-gradient(red, yellow, lime, aqua, blue, magenta, red)",
};

export interface ColorOption {
  simple?: string;
  hex?: string;
  label?: string;
}

/** LN-X03: hex wins; else simple->style; else fallback #CCCCCC. */
export function getColorStyle(option: ColorOption): string {
  if (option.hex) return option.hex;
  if (option.simple && SIMPLE_COLOR_STYLES[option.simple]) return SIMPLE_COLOR_STYLES[option.simple];
  return "#CCCCCC";
}

export function isGradient(style: string | undefined): boolean {
  return !!style && style.includes("gradient");
}
