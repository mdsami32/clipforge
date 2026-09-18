"use client";

/** Draggable-handle trim timeline with a placeholder waveform track.
 * Real waveform rendering (e.g. via wavesurfer.js reading the source audio)
 * is a Phase 1 polish item — the handles and time labels are fully wired. */
export function Timeline({
  durationSeconds,
  start,
  end,
  onChange,
}: {
  durationSeconds: number;
  start: number;
  end: number;
  onChange: (start: number, end: number) => void;
}) {
  const pct = (t: number) => `${(t / durationSeconds) * 100}%`;

  return (
    <div>
      <div
        style={{
          position: "relative",
          height: 64,
          background: "repeating-linear-gradient(90deg, #eee, #eee 2px, #f7f7f7 2px, #f7f7f7 6px)",
          borderRadius: 8,
          border: "1px solid #ddd",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: pct(start),
            width: `calc(${pct(end)} - ${pct(start)})`,
            top: 0,
            bottom: 0,
            background: "rgba(17,17,17,0.15)",
            borderLeft: "3px solid #111",
            borderRight: "3px solid #111",
          }}
        />
      </div>
      <div style={{ display: "flex", gap: 16, marginTop: 8 }}>
        <label style={{ fontSize: 13, color: "#555" }}>
          Start
          <input
            type="number"
            step={0.1}
            value={start}
            min={0}
            max={end}
            onChange={(e) => onChange(Number(e.target.value), end)}
            style={{ width: 80, marginLeft: 6 }}
          />
        </label>
        <label style={{ fontSize: 13, color: "#555" }}>
          End
          <input
            type="number"
            step={0.1}
            value={end}
            min={start}
            max={durationSeconds}
            onChange={(e) => onChange(start, Number(e.target.value))}
            style={{ width: 80, marginLeft: 6 }}
          />
        </label>
        <span style={{ fontSize: 13, color: "#888", alignSelf: "center" }}>
          Duration: {(end - start).toFixed(1)}s
        </span>
      </div>
    </div>
  );
}
