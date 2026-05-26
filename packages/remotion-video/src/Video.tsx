import React from "react";
import { Composition, AbsoluteFill } from "remotion";
import type { VideoManifest } from "./types";

const VideoComposition: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#1a2332", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <h1 style={{ color: "#f0ebe3", fontFamily: "Georgia, serif" }}>FastPub Video</h1>
    </AbsoluteFill>
  );
};

export const Video: React.FC = () => {
  return (
    <Composition
      id="Video"
      component={VideoComposition}
      durationInFrames={150}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
