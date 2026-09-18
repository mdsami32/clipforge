"use client";

export function AudioPanel({
  settings,
  onChange,
}: {
  settings: { noise_reduction?: boolean; loudness_target_lufs?: number };
  onChange: (settings: { noise_reduction: boolean; loudness_target_lufs: number }) => void;
}) {
  const noiseReduction = settings.noise_reduction ?? false;
  const loudness = settings.loudness_target_lufs ?? -14;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input
          type="checkbox"
          checked={noiseReduction}
          onChange={(e) => onChange({ noise_reduction: e.target.checked, loudness_target_lufs: loudness })}
        />
        Noise reduction
      </label>
      <label>
        Loudness target: {loudness} LUFS
        <input
          type="range"
          min={-23}
          max={-8}
          step={1}
          value={loudness}
          onChange={(e) => onChange({ noise_reduction: noiseReduction, loudness_target_lufs: Number(e.target.value) })}
          style={{ display: "block", width: "100%" }}
        />
      </label>
    </div>
  );
}
