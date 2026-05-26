import React from "react";
import type { ManifestScene } from "./types";
import { useFadeIn, useScaleReveal, useTypewriter } from "./animations";

interface SceneProps {
  scene: ManifestScene;
}

export const Scene: React.FC<SceneProps> = ({ scene }) => {
  const isDark = scene.type === "hook" || scene.type === "closing";
  const hasImage = !!scene.imageFile;

  if (isDark) return <DarkScene scene={scene} />;
  if (hasImage) return <SplitScene scene={scene} />;
  return <CenteredScene scene={scene} />;
};

const DarkScene: React.FC<SceneProps> = ({ scene }) => {
  const typedHeadline = useTypewriter(scene.headline, 0.8, 10);
  const bodyStyle = useFadeIn(30, 15);
  const dividerStyle = useFadeIn(5, 10);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "linear-gradient(135deg, #1a2332 0%, #2a3f5f 100%)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "80px 120px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Decorative circles */}
      <div style={{ position: "absolute", top: -40, right: -40, width: 300, height: 300, border: "2px solid rgba(200,170,120,0.1)", borderRadius: "50%" }} />
      <div style={{ position: "absolute", top: 20, right: 20, width: 200, height: 200, border: "2px solid rgba(200,170,120,0.06)", borderRadius: "50%" }} />

      {/* Brand */}
      <div style={{ position: "absolute", top: 40, left: 60, fontFamily: "-apple-system, sans-serif", fontSize: 14, fontWeight: 700, color: "#c8aa78", letterSpacing: "0.2em", textTransform: "uppercase" as const }}>
        fastpub
      </div>

      {/* Headline */}
      <h1 style={{
        fontFamily: "Georgia, serif",
        fontSize: scene.type === "hook" ? 72 : 52,
        fontWeight: 700,
        fontStyle: scene.type === "hook" ? "italic" : "normal",
        color: "#f0ebe3",
        lineHeight: 1.3,
        maxWidth: "75%",
      }}>
        {typedHeadline}
        <span style={{ opacity: 0.3 }}>|</span>
      </h1>

      {/* Divider */}
      <div style={{ ...dividerStyle, width: 60, height: 3, background: "linear-gradient(90deg, #c8aa78, transparent)", marginTop: 40, borderRadius: 2 }} />

      {/* Body */}
      {scene.body && (
        <p style={{ ...bodyStyle, fontFamily: "-apple-system, sans-serif", fontSize: 28, color: "#8a9ab0", marginTop: 24, lineHeight: 1.6, maxWidth: "65%" }}>
          {scene.body}
        </p>
      )}

      {/* Closing extras */}
      {scene.type === "closing" && (
        <div style={{ position: "absolute", bottom: 60, left: 0, right: 0, textAlign: "center" }}>
          <div style={{ fontFamily: "Georgia, serif", fontSize: 12, color: "#556a78", letterSpacing: "0.1em", textTransform: "uppercase" as const }}>fastpub</div>
        </div>
      )}
    </div>
  );
};

const SplitScene: React.FC<SceneProps> = ({ scene }) => {
  const labelStyle = useFadeIn(5, 10);
  const headlineStyle = useFadeIn(8, 15);
  const bodyStyle = useFadeIn(15, 15);
  const imageStyle = useScaleReveal(12, 18);

  return (
    <div style={{ width: "100%", height: "100%", background: "#faf8f5", display: "flex", padding: "60px 80px", gap: 60, position: "relative" }}>
      {/* Top accent bar */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 4, background: `linear-gradient(90deg, ${scene.colorAccent} 0%, transparent 100%)` }} />

      {/* Text side */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <div style={{ ...labelStyle, fontFamily: "-apple-system, sans-serif", fontSize: 14, color: scene.colorAccent, fontWeight: 700, letterSpacing: "0.15em", textTransform: "uppercase" as const, marginBottom: 16 }}>
          {scene.type}
        </div>
        <h2 style={{ ...headlineStyle, fontFamily: "Georgia, serif", fontSize: 48, fontWeight: 700, color: "#1a2332", lineHeight: 1.3, marginBottom: 32 }}>
          {scene.headline}
        </h2>
        {scene.body && (
          <div style={{ ...bodyStyle, fontSize: 22, color: "#4a5568", lineHeight: 1.7, fontFamily: "-apple-system, sans-serif", paddingLeft: 16, borderLeft: `3px solid ${scene.colorAccent}` }}>
            {scene.body}
          </div>
        )}
      </div>

      {/* Image side */}
      <div style={{ flex: 0.85, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <img
          src={scene.imageFile!}
          style={{ ...imageStyle, maxWidth: "100%", maxHeight: "100%", objectFit: "contain" as const, background: "#fff", border: "1px solid #e0ddd8", borderRadius: 6, boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}
        />
      </div>

      {/* Brand */}
      <div style={{ position: "absolute", bottom: 24, left: 80, fontFamily: "Georgia, serif", fontSize: 12, color: "#bbb", letterSpacing: "0.1em", textTransform: "uppercase" as const }}>fastpub</div>
    </div>
  );
};

const CenteredScene: React.FC<SceneProps> = ({ scene }) => {
  const labelStyle = useFadeIn(5, 10);
  const headlineStyle = useFadeIn(8, 15);
  const bodyStyle = useFadeIn(15, 15);

  return (
    <div style={{ width: "100%", height: "100%", background: "#faf8f5", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center" as const, padding: "80px 120px", position: "relative" }}>
      {/* Top accent bar */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 4, background: `linear-gradient(90deg, ${scene.colorAccent} 0%, transparent 100%)` }} />

      <div style={{ ...labelStyle, fontFamily: "-apple-system, sans-serif", fontSize: 14, color: scene.colorAccent, fontWeight: 700, letterSpacing: "0.15em", textTransform: "uppercase" as const, marginBottom: 16 }}>
        {scene.type}
      </div>
      <h2 style={{ ...headlineStyle, fontFamily: "Georgia, serif", fontSize: 56, fontWeight: 700, color: "#1a2332", lineHeight: 1.3, maxWidth: "80%", marginBottom: 32 }}>
        {scene.headline}
      </h2>
      {scene.body && (
        <p style={{ ...bodyStyle, fontSize: 26, color: "#4a5568", lineHeight: 1.7, fontFamily: "-apple-system, sans-serif", maxWidth: "65%" }}>
          {scene.body}
        </p>
      )}

      <div style={{ position: "absolute", bottom: 24, fontFamily: "Georgia, serif", fontSize: 12, color: "#bbb", letterSpacing: "0.1em", textTransform: "uppercase" as const }}>fastpub</div>
    </div>
  );
};
