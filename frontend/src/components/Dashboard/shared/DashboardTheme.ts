export const WIDGET_ACCENT = {
  agent: '#38bdf8',
  osint: '#a78bfa',
  datasource: '#22d3ee',
  landhaus: '#D4AF37',
  sitdeck: '#a78bfa',
  energy: '#4ade80',
  trace: '#94a3b8',
} as const;

export function accentColorAlpha(accent: string, alphaHex: string): string {
  return `${accent}${alphaHex}`;
}
