import { interpolate, useCurrentFrame } from "remotion";

export function useStagger(index: number, delayPerItem: number = 5, duration: number = 12, offsetX: number = 20) {
  const frame = useCurrentFrame();
  const delay = index * delayPerItem;
  const opacity = interpolate(frame, [delay, delay + duration], [0, 1], { extrapolateRight: "clamp" });
  const translateX = interpolate(frame, [delay, delay + duration], [-offsetX, 0], { extrapolateRight: "clamp" });
  return { opacity, transform: `translateX(${translateX}px)` };
}
