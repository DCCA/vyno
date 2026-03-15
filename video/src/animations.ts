import { interpolate, spring } from "remotion";
import { FPS } from "./theme";

const CLAMP = { extrapolateRight: "clamp" as const, extrapolateLeft: "clamp" as const };

export function fadeIn(frame: number, delay = 0, duration = 15) {
  return interpolate(frame, [delay, delay + duration], [0, 1], CLAMP);
}

export function slideUp(frame: number, delay = 0, distance = 40) {
  return interpolate(frame, [delay, delay + 20], [distance, 0], CLAMP);
}

export function scaleIn(frame: number, delay = 0) {
  return interpolate(frame, [delay, delay + 20], [0.95, 1], CLAMP);
}

export function wipeRight(frame: number, delay = 0, duration = 20) {
  return interpolate(frame, [delay, delay + duration], [0, 1], CLAMP);
}

export function springIn(frame: number, delay = 0) {
  return spring({
    frame: Math.max(0, frame - delay),
    fps: FPS,
    config: { damping: 15, stiffness: 120, mass: 0.8 },
  });
}

export function stagger(index: number, baseDelay = 0, gap = 8) {
  return baseDelay + index * gap;
}

export function fadeUpStyle(frame: number, delay = 0): React.CSSProperties {
  return {
    opacity: fadeIn(frame, delay),
    transform: `translateY(${slideUp(frame, delay)}px)`,
  };
}
