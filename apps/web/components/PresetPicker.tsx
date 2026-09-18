"use client";

import { Preset } from "@/lib/api";

export function PresetPicker({
  presets,
  selectedId,
  onSelect,
}: {
  presets: Preset[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {presets.map((p) => (
        <button
          key={p.id}
          onClick={() => onSelect(p.id)}
          className={selectedId === p.id ? "primary" : ""}
        >
          {p.name} ({p.resolution_w}×{p.resolution_h})
        </button>
      ))}
    </div>
  );
}
