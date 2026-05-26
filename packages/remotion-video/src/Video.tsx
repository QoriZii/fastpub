import React from "react";
import { Composition, AbsoluteFill, Series } from "remotion";
import type { VideoManifest } from "./types";
import { Scene } from "./Scene";
import { SceneWrapper } from "./SceneWrapper";
import { AudioTrack } from "./AudioTrack";

const VideoComposition: React.FC<{ manifest: VideoManifest }> = ({ manifest }) => {
  const { settings, scenes } = manifest;

  return (
    <AbsoluteFill>
      <Series>
        {scenes.map((scene) => {
          const durationInFrames = Math.round(scene.durationSec * settings.fps);
          return (
            <Series.Sequence key={scene.id} durationInFrames={durationInFrames}>
              <SceneWrapper durationInFrames={durationInFrames} transition={scene.transition}>
                <Scene scene={scene} />
              </SceneWrapper>
            </Series.Sequence>
          );
        })}
      </Series>
      <AudioTrack scenes={scenes} fps={settings.fps} />
    </AbsoluteFill>
  );
};

export const Video: React.FC = () => {
  const defaultManifest: VideoManifest = {
    meta: { title: "Preview", authors: [], venue: "", year: null },
    settings: { fps: 30, width: 1920, height: 1080 },
    scenes: [
      { id: "p1", type: "hook", durationSec: 5, headline: "Preview Hook Scene", body: "This is a preview.", narration: "", audioFile: null, imageFile: null, imagePrompt: "", transition: "fade", colorAccent: "#c8aa78" },
      { id: "p2", type: "approach", durationSec: 5, headline: "Preview Method", body: "Method details here.", narration: "", audioFile: null, imageFile: null, imagePrompt: "", transition: "fade", colorAccent: "#5b8fa8" },
    ],
  };

  const totalFrames = defaultManifest.scenes.reduce(
    (sum, s) => sum + Math.round(s.durationSec * defaultManifest.settings.fps), 0
  );

  return (
    <Composition
      id="Video"
      component={VideoComposition}
      durationInFrames={totalFrames}
      fps={defaultManifest.settings.fps}
      width={defaultManifest.settings.width}
      height={defaultManifest.settings.height}
      defaultProps={{ manifest: defaultManifest }}
    />
  );
};
