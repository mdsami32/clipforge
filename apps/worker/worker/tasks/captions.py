"""Builds an .ass subtitle file from a clip's word-level captions + style, for
ffmpeg to burn in via the `subtitles` filter. Word-level timing is what lets
the in-browser caption editor's "click a word to edit/retime" UX map 1:1 to
what gets rendered.
"""
import os

DEFAULT_STYLE = {
    "font": "Arial",
    "font_size": 64,
    "color": "&H00FFFFFF",  # ASS BGR hex, white
    "highlight_color": "&H0000D7FF",  # highlighted/active word, orange-ish
    "position": "bottom",  # "bottom" | "center" | "top"
    "outline": 3,
}


def _ass_position_alignment(position: str) -> int:
    # ASS \an alignment codes: 2 = bottom-center, 5 = middle-center, 8 = top-center
    return {"bottom": 2, "center": 5, "top": 8}.get(position, 2)


def write_ass_file(captions: list[dict], style: dict | None, out_path: str, video_w: int, video_h: int):
    style = {**DEFAULT_STYLE, **(style or {})}
    alignment = _ass_position_alignment(style["position"])
    margin_v = int(video_h * 0.12)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_w}
PlayResY: {video_h}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginV
Style: Default,{style['font']},{style['font_size']},{style['color']},&H00000000,1,1,{style['outline']},0,{alignment},{margin_v}

[Events]
Format: Layer, Start, End, Style, Text
"""
    lines = [header]

    # Group words into ~4-word caption chunks for readability, one Dialogue
    # event per chunk so words don't overlap on screen.
    chunk_size = 4
    for i in range(0, len(captions), chunk_size):
        chunk = captions[i : i + chunk_size]
        if not chunk:
            continue
        start = _fmt_ts(chunk[0]["start"])
        end = _fmt_ts(chunk[-1]["end"])
        text = " ".join(w["word"] for w in chunk)
        lines.append(f"Dialogue: 0,{start},{end},Default,{text}\n")

    with open(out_path, "w") as f:
        f.writelines(lines)

    return out_path


def _fmt_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"
