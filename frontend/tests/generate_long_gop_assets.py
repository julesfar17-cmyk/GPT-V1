"""Generate repeatable long-GOP H264 assets for BeatCut preview baseline tests."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import imageio_ffmpeg


OUT_DIR = Path("/root/beatcut-test-assets")
MANIFEST = OUT_DIR / "manifest.json"


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr[-500:]}")


def _make_asset(path: Path, size: str, duration_s: int = 185, fps: int = 24) -> None:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    # Long GOP target: GOP=240 @24fps => keyframe every 10s, with B-frames enabled.
    cmd = [
        ff,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size={size}:rate={fps}:duration={duration_s}",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "high",
        "-preset",
        "veryfast",
        "-crf",
        "30",
        "-g",
        str(fps * 10),
        "-keyint_min",
        str(fps * 10),
        "-sc_threshold",
        "0",
        "-bf",
        "3",
        "-movflags",
        "+faststart",
        str(path),
    ]
    _run(cmd)


def _probe_keyframe_gaps(path: Path) -> list[float]:
    ffprobe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-skip_frame",
        "nokey",
        "-show_entries",
        "frame=pts_time",
        "-of",
        "csv=p=0",
        str(path),
    ]
    try:
        proc = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return []
    if proc.returncode != 0:
        return []
    pts = []
    for raw in proc.stdout.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            pts.append(float(raw.split(",")[0]))
        except ValueError:
            continue
    gaps = []
    for i in range(1, len(pts)):
        gaps.append(round(pts[i] - pts[i - 1], 3))
    return gaps


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    f_720 = OUT_DIR / "h264_longgop_1280x720_185s.mp4"
    f_800 = OUT_DIR / "h264_longgop_1280x800_185s.mp4"

    if not f_720.exists():
        _make_asset(f_720, "1280x720")
    if not f_800.exists():
        _make_asset(f_800, "1280x800")

    manifest = {
        "h264_720": str(f_720),
        "h264_800": str(f_800),
        "sizes": {
            "h264_720_bytes": f_720.stat().st_size,
            "h264_800_bytes": f_800.stat().st_size,
        },
        "keyframe_gaps": {
            "h264_720": _probe_keyframe_gaps(f_720)[:10],
            "h264_800": _probe_keyframe_gaps(f_800)[:10],
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
