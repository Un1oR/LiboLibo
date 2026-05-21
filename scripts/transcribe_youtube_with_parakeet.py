#!/usr/bin/env python3
"""
Download a YouTube audio section, split it into WAV chunks, and transcribe it
with scripts/transcribe_with_parakeet.py.

Run this script via uv with onnx-asr installed in the same environment:

  uv run --with 'onnx-asr[cpu]' scripts/transcribe_youtube_with_parakeet.py \
    --auto-handy-model \
    --section 00:00:00-00:30:00 \
    https://www.youtube.com/watch?v=mKjCHo7GKko
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORK_DIR = Path("/tmp/libolibo-stream")
DEFAULT_CHUNK_SECONDS = 25


def section_slug(section: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z]+", "-", section).strip("-")
    parts = safe.split("-", 3)
    if len(parts) == 4:
        return f"{parts[0]}-{parts[1]}-{parts[2]}_{parts[3]}"
    return safe.replace("-", "_", 1)


def download_command(url: str, section: str, output_template: Path) -> list[str]:
    return [
        "yt-dlp",
        "--no-warnings",
        "--download-sections",
        f"*{section}",
        "-f",
        "worstaudio/worst",
        "-o",
        str(output_template),
        url,
    ]


def split_command(audio_path: Path, chunk_seconds: int, chunk_pattern: Path) -> list[str]:
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(audio_path),
        "-vn",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-reset_timestamps",
        "1",
        "-c:a",
        "pcm_s16le",
        str(chunk_pattern),
    ]


def transcribe_command(
    *,
    python_executable: str,
    transcribe_script: Path,
    chunks: Sequence[Path],
    output_dir: Path,
    model_dir: Path | None,
    auto_handy_model: bool,
) -> list[str]:
    command = [
        python_executable,
        str(transcribe_script),
        "--output-dir",
        str(output_dir),
    ]
    if model_dir is not None:
        command.extend(["--model-dir", str(model_dir)])
    elif auto_handy_model:
        command.append("--auto-handy-model")
    command.extend(str(chunk) for chunk in chunks)
    return command


def run_command(command: Sequence[str], *, dry_run: bool) -> None:
    print("$ " + shlex.join(command), flush=True)
    if dry_run:
        return
    subprocess.run(command, check=True)


def find_downloaded_audio(section_dir: Path, section_name: str) -> Path:
    matches = sorted(
        path
        for path in section_dir.glob(f"{section_name}.*")
        if path.is_file() and not path.name.endswith(".part")
    )
    if not matches:
        raise SystemExit(f"No downloaded audio found for {section_name} in {section_dir}")
    if len(matches) > 1:
        preferred = [path for path in matches if path.suffix.lower() in {".m4a", ".webm", ".opus", ".mp3"}]
        if len(preferred) == 1:
            return preferred[0]
        raise SystemExit(
            f"Multiple downloaded audio files found for {section_name}: "
            + ", ".join(str(path) for path in matches)
        )
    return matches[0]


def find_chunks(chunks_dir: Path, section_name: str) -> list[Path]:
    chunks = sorted(chunks_dir.glob(f"{section_name}-*.wav"))
    if not chunks:
        raise SystemExit(f"No WAV chunks found for {section_name} in {chunks_dir}")
    return chunks


def write_combined_transcript(transcript_dirs: Iterable[Path], combined_output: Path) -> None:
    transcript_files: list[Path] = []
    for transcript_dir in transcript_dirs:
        transcript_files.extend(sorted(transcript_dir.glob("*.txt")))

    lines = ["# Transcript", ""]
    for transcript_file in sorted(transcript_files):
        text = transcript_file.read_text(encoding="utf-8").strip()
        lines.append(f"## {transcript_file.stem}")
        lines.append("")
        lines.append(text)
        lines.append("")

    combined_output.parent.mkdir(parents=True, exist_ok=True)
    combined_output.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download YouTube audio sections and transcribe them with local Parakeet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  uv run --with 'onnx-asr[cpu]' scripts/transcribe_youtube_with_parakeet.py \\
    --auto-handy-model \\
    --section 00:00:00-00:30:00 \\
    https://www.youtube.com/watch?v=mKjCHo7GKko

  uv run --with 'onnx-asr[cpu]' scripts/transcribe_youtube_with_parakeet.py \\
    --model-dir "$PARAKEET_MODEL_DIR" \\
    --work-dir /tmp/libolibo-stream \\
    --section 00:00:00-00:30:00 \\
    --section 00:30:00-01:00:00 \\
    https://www.youtube.com/watch?v=mKjCHo7GKko

Notes:
  - --section is required to avoid accidentally downloading a 10-hour stream.
  - The script stores audio, chunks, and transcripts under --work-dir.
  - Model files are not downloaded; pass --model-dir or use --auto-handy-model.
""",
    )
    parser.add_argument("url", help="YouTube URL.")
    parser.add_argument(
        "--section",
        action="append",
        required=True,
        help="Time range for yt-dlp --download-sections, e.g. 00:00:00-00:30:00. Repeatable.",
    )
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--chunk-seconds", type=int, default=DEFAULT_CHUNK_SECONDS)
    parser.add_argument("--model-dir", type=Path, help="Local Parakeet ONNX model directory.")
    parser.add_argument(
        "--auto-handy-model",
        action="store_true",
        help="Reuse Handy's standard Parakeet V3 model cache.",
    )
    parser.add_argument(
        "--transcribe-script",
        type=Path,
        default=ROOT / "scripts/transcribe_with_parakeet.py",
        help="Path to scripts/transcribe_with_parakeet.py.",
    )
    parser.add_argument(
        "--combined-output",
        type=Path,
        help="Combined markdown transcript path. Defaults to <work-dir>/transcript.md.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    work_dir = args.work_dir.expanduser()
    audio_dir = work_dir / "audio"
    chunks_dir = work_dir / "chunks"
    transcripts_dir = work_dir / "transcripts"
    combined_output = args.combined_output or work_dir / "transcript.md"

    if args.chunk_seconds < 5:
        raise SystemExit("--chunk-seconds must be at least 5")
    if not args.model_dir and not args.auto_handy_model:
        raise SystemExit("Pass --model-dir or --auto-handy-model.")

    audio_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    transcript_dirs: list[Path] = []
    for index, section in enumerate(args.section, start=1):
        section_name = f"section-{index:03d}-{section_slug(section)}"
        output_template = audio_dir / f"{section_name}.%(ext)s"
        section_chunks_dir = chunks_dir / section_name
        section_transcripts_dir = transcripts_dir / section_name
        section_chunks_dir.mkdir(parents=True, exist_ok=True)
        section_transcripts_dir.mkdir(parents=True, exist_ok=True)

        run_command(download_command(args.url, section, output_template), dry_run=args.dry_run)
        audio_path = output_template if args.dry_run else find_downloaded_audio(audio_dir, section_name)

        chunk_pattern = section_chunks_dir / f"{section_name}-%04d.wav"
        run_command(split_command(audio_path, args.chunk_seconds, chunk_pattern), dry_run=args.dry_run)
        chunks = [chunk_pattern] if args.dry_run else find_chunks(section_chunks_dir, section_name)

        run_command(
            transcribe_command(
                python_executable=sys.executable,
                transcribe_script=args.transcribe_script,
                chunks=chunks,
                output_dir=section_transcripts_dir,
                model_dir=args.model_dir,
                auto_handy_model=args.auto_handy_model,
            ),
            dry_run=args.dry_run,
        )
        transcript_dirs.append(section_transcripts_dir)

    if args.dry_run:
        print(f"Would write combined transcript: {combined_output}")
        return 0

    write_combined_transcript(transcript_dirs, combined_output)
    print(combined_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
