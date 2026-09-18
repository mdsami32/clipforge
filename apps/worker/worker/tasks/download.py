"""Download source video. self_hosted backend uses yt-dlp directly."""
import os

import yt_dlp

from ..config import settings


def download_youtube_video(url: str, out_dir: str) -> tuple[str, dict]:
    """Downloads the best mp4 stream and returns (local_path, info_dict)."""
    outtmpl = os.path.join(out_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
        # merge_output_format can change the extension after download
        if not os.path.exists(path):
            path = os.path.splitext(path)[0] + ".mp4"
    return path, info
