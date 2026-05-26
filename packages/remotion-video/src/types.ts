export interface ManifestMeta {
  title: string;
  authors: string[];
  venue: string;
  year: number | null;
}

export interface ManifestSettings {
  fps: number;
  width: number;
  height: number;
}

export interface ManifestScene {
  id: string;
  type: "hook" | "problem" | "approach" | "results" | "significance" | "closing";
  durationSec: number;

  // Visual text (displayed on slide)
  headline: string;
  body: string;

  // Audio (TTS narration, not displayed)
  narration: string;
  audioFile: string | null;

  // Image (AI-generated, displayed on slide)
  imageFile: string | null;
  imagePrompt: string;

  transition: "fade" | "cut" | "slide";
  colorAccent: string;
}

export interface VideoManifest {
  meta: ManifestMeta;
  settings: ManifestSettings;
  scenes: ManifestScene[];
}
