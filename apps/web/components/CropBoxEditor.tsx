"use client";

/** Manual crop override. Face tracking drives the crop automatically when no
 * override is set; toggling it off or entering explicit values here takes
 * over. A draggable on-video crop box is a natural follow-up once the
 * editor has an actual video element to overlay it on (needs a signed
 * playback URL from the API — see TODO in the editor page). */
export function CropBoxEditor({
  faceTrackEnabled,
  cropBox,
  onChange,
}: {
  faceTrackEnabled: boolean;
  cropBox: { x: number; y: number; w: number; h: number } | null;
  onChange: (faceTrackEnabled: boolean, cropBox: { x: number; y: number; w: number; h: number } | null) => void;
}) {
  return (
    <div>
      <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input
          type="checkbox"
          checked={faceTrackEnabled}
          onChange={(e) => onChange(e.target.checked, e.target.checked ? null : cropBox ?? { x: 0, y: 0, w: 1080, h: 1920 })}
        />
        Auto face-track vertical crop
      </label>

      {!faceTrackEnabled && (
        <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
          {(["x", "y", "w", "h"] as const).map((key) => (
            <label key={key} style={{ fontSize: 13 }}>
              {key.toUpperCase()}
              <input
                type="number"
                value={cropBox?.[key] ?? 0}
                onChange={(e) =>
                  onChange(false, { ...(cropBox ?? { x: 0, y: 0, w: 1080, h: 1920 }), [key]: Number(e.target.value) })
                }
                style={{ width: 70, marginLeft: 4 }}
              />
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
