import React from "react";
import { Audio, Sequence } from "remotion";
import type { ManifestScene } from "./types";

interface AudioTrackProps {
  scenes: ManifestScene[];
  fps: number;
}

export const AudioTrack: React.FC<AudioTrackProps> = ({ scenes, fps }) => {
  let frameOffset = 0;

  return (
    <>
      {scenes.map((scene) => {
        const durationInFrames = Math.round(scene.durationSec * fps);
        const from = frameOffset;
        frameOffset += durationInFrames;

        if (!scene.audioFile) return null;

        return (
          <Sequence key={scene.id} from={from} durationInFrames={durationInFrames}>
            <Audio src={scene.audioFile} />
          </Sequence>
        );
      })}
    </>
  );
};
