import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

interface SceneWrapperProps {
  children: React.ReactNode;
  durationInFrames: number;
  transition: "fade" | "cut" | "slide";
}

const FADE_FRAMES = 15; // 500ms at 30fps

export const SceneWrapper: React.FC<SceneWrapperProps> = ({ children, durationInFrames, transition }) => {
  const frame = useCurrentFrame();

  let opacity = 1;
  if (transition === "fade") {
    const fadeIn = interpolate(frame, [0, FADE_FRAMES], [0, 1], { extrapolateRight: "clamp" });
    const fadeOut = interpolate(frame, [durationInFrames - FADE_FRAMES, durationInFrames], [1, 0], { extrapolateRight: "clamp" });
    opacity = Math.min(fadeIn, fadeOut);
  }

  return (
    <AbsoluteFill style={{ opacity }}>
      {children}
    </AbsoluteFill>
  );
};
