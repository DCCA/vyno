export const colors = {
  bg: "#0D0D0D",
  surface: "#1A1A1A",
  surfaceMuted: "#2A2A2A",
  gold: "#C9A962",
  textPrimary: "#F5F4F2",
  textSecondary: "#8A8A8A",
  textMuted: "#5A5A5A",
  textDisabled: "#6A6A6A",
  border: "#2A2A2A",
} as const;

export const fonts = {
  heading: "Bebas Neue",
  body: "Cormorant Garamond",
} as const;

export const FPS = 30;

export const SLIDE_DURATIONS = {
  cover: 4 * FPS,
  problem: 5 * FPS,
  solution: 5 * FPS,
  howItWorks: 7 * FPS,
  scoring: 7 * FPS,
  selfHosted: 5 * FPS,
  mobileControl: 7 * FPS,
  archive: 6 * FPS,
  differentiators: 7 * FPS,
  closing: 5 * FPS,
} as const;

export const TOTAL_FRAMES = Object.values(SLIDE_DURATIONS).reduce(
  (a, b) => a + b,
  0,
);
