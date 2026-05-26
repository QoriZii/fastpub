import { interpolate, useCurrentFrame } from "remotion";

export function useScaleReveal(delay: number = 0, duration: number = 15) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [delay, delay + duration], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(frame, [delay, delay + duration], [0.95, 1], { extrapolateRight: "clamp" });
  return { opacity, transform: `scale(${scale})` };
}
