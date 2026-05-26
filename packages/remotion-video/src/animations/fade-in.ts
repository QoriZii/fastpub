import { interpolate, useCurrentFrame } from "remotion";

export function useFadeIn(delay: number = 0, duration: number = 15, offsetY: number = 40) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [delay, delay + duration], [0, 1], { extrapolateRight: "clamp" });
  const translateY = interpolate(frame, [delay, delay + duration], [offsetY, 0], { extrapolateRight: "clamp" });
  return { opacity, transform: `translateY(${translateY}px)` };
}
