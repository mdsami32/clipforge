"use client";

export type HookOverlay = {
  text: string;
  start: number;
  end: number;
  position: "top" | "center" | "bottom";
  font_size: number;
  color: string;
  animation: "none" | "pop" | "fade";
};

const BLANK: HookOverlay = {
  text: "",
  start: 0,
  end: 3,
  position: "top",
  font_size: 72,
  color: "white",
  animation: "pop",
};

export function HookTextEditor({
  overlays,
  onChange,
}: {
  overlays: HookOverlay[];
  onChange: (overlays: HookOverlay[]) => void;
}) {
  function update(i: number, patch: Partial<HookOverlay>) {
    const next = overlays.slice();
    next[i] = { ...next[i], ...patch };
    onChange(next);
  }

  function add() {
    onChange([...overlays, { ...BLANK }]);
  }

  function remove(i: number) {
    onChange(overlays.filter((_, idx) => idx !== i));
  }

  return (
    <div>
      {overlays.map((o, i) => (
        <div key={i} className="card">
          <input
            type="text"
            placeholder="Hook text…"
            value={o.text}
            onChange={(e) => update(i, { text: e.target.value })}
          />
          <div style={{ display: "flex", gap: 12, marginTop: 8, flexWrap: "wrap" }}>
            <label style={{ fontSize: 13 }}>
              Start
              <input
                type="number"
                step={0.1}
                value={o.start}
                onChange={(e) => update(i, { start: Number(e.target.value) })}
                style={{ width: 60, marginLeft: 4 }}
              />
            </label>
            <label style={{ fontSize: 13 }}>
              End
              <input
                type="number"
                step={0.1}
                value={o.end}
                onChange={(e) => update(i, { end: Number(e.target.value) })}
                style={{ width: 60, marginLeft: 4 }}
              />
            </label>
            <label style={{ fontSize: 13 }}>
              Position
              <select value={o.position} onChange={(e) => update(i, { position: e.target.value as any })}>
                <option value="top">Top</option>
                <option value="center">Center</option>
                <option value="bottom">Bottom</option>
              </select>
            </label>
            <label style={{ fontSize: 13 }}>
              Font size
              <input
                type="number"
                value={o.font_size}
                onChange={(e) => update(i, { font_size: Number(e.target.value) })}
                style={{ width: 60, marginLeft: 4 }}
              />
            </label>
            <label style={{ fontSize: 13 }}>
              Animation
              <select value={o.animation} onChange={(e) => update(i, { animation: e.target.value as any })}>
                <option value="none">None</option>
                <option value="pop">Pop</option>
                <option value="fade">Fade</option>
              </select>
            </label>
            <button onClick={() => remove(i)}>Remove</button>
          </div>
        </div>
      ))}
      <button onClick={add}>+ Add hook text</button>
    </div>
  );
}
