import { useCurrentFrame } from "remotion";

export function useTypewriter(text: string, charsPerFrame: number = 0.8, delay: number = 0) {
  const frame = useCurrentFrame();
  const elapsed = Math.max(0, frame - delay);
  const visibleChars = Math.min(Math.floor(elapsed * charsPerFrame), text.length);
  return text.slice(0, visibleChars);
}
