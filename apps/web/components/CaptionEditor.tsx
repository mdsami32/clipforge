"use client";

import { useState } from "react";

export type CaptionWord = { word: string; start: number; end: number };

/** Word-level caption editor: click a word to edit its text or retime it. */
export function CaptionEditor({
  captions,
  onChange,
}: {
  captions: CaptionWord[];
  onChange: (captions: CaptionWord[]) => void;
}) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  function updateWord(i: number, patch: Partial<CaptionWord>) {
    const next = captions.slice();
    next[i] = { ...next[i], ...patch };
    onChange(next);
  }

  function removeWord(i: number) {
    onChange(captions.filter((_, idx) => idx !== i));
  }

  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {captions.map((w, i) => (
          <span
            key={i}
            onClick={() => setEditingIndex(i)}
            style={{
              padding: "4px 8px",
              borderRadius: 6,
              background: editingIndex === i ? "#111" : "#f0f0f0",
              color: editingIndex === i ? "#fff" : "#111",
              cursor: "pointer",
              fontSize: 14,
            }}
          >
            {w.word}
          </span>
        ))}
      </div>

      {editingIndex !== null && captions[editingIndex] && (
        <div className="card" style={{ marginTop: 12 }}>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <input
              type="text"
              value={captions[editingIndex].word}
              onChange={(e) => updateWord(editingIndex, { word: e.target.value })}
              style={{ maxWidth: 160 }}
            />
            <label style={{ fontSize: 13 }}>
              Start
              <input
                type="number"
                step={0.05}
                value={captions[editingIndex].start}
                onChange={(e) => updateWord(editingIndex, { start: Number(e.target.value) })}
                style={{ width: 70, marginLeft: 4 }}
              />
            </label>
            <label style={{ fontSize: 13 }}>
              End
              <input
                type="number"
                step={0.05}
                value={captions[editingIndex].end}
                onChange={(e) => updateWord(editingIndex, { end: Number(e.target.value) })}
                style={{ width: 70, marginLeft: 4 }}
              />
            </label>
            <button onClick={() => removeWord(editingIndex)}>Delete word</button>
            <button onClick={() => setEditingIndex(null)}>Done</button>
          </div>
        </div>
      )}
    </div>
  );
}
