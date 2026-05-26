import { interpolate, useCurrentFrame } from "remotion";

export function useSlideIn(delay: number = 0, duration: number = 12, fromX: number = 100) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [delay, delay + duration], [0, 1], { extrapolateRight: "clamp" });
  const translateX = interpolate(frame, [delay, delay + duration], [fromX, 0], { extrapolateRight: "clamp" });
  return { opacity, transform: `translateX(${translateX}px)` };
}
