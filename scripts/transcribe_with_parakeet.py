#!/usr/bin/env python3
"""
Transcribe prepared audio chunks with a local Parakeet ONNX model.

This script intentionally does not download models. Point it at an existing
model directory, for example the Parakeet V3 cache downloaded by Handy.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Mapping, Sequence


DEFAULT_HANDY_MODEL_NAME = "parakeet-tdt-0.6b-v3-int8"


def existing_dir(path: Path, label: str) -> Path:
    expanded = path.expanduser()
    if not expanded.is_dir():
        raise SystemExit(f"{label} does not exist or is not a directory: {expanded}")
    return expanded


def handy_model_candidates(
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> list[Path]:
    env = os.environ if env is None else env
    home = Path.home() if home is None else home

    xdg_data_home = Path(env.get("XDG_DATA_HOME", home / ".local/share")).expanduser()
    return [
        xdg_data_home / "com.pais.handy" / "models" / DEFAULT_HANDY_MODEL_NAME,
        home / "Library/Application Support/com.pais.handy/models" / DEFAULT_HANDY_MODEL_NAME,
    ]


def resolve_model_dir(
    model_dir: Path | None,
    *,
    auto_handy_model: bool,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    env = os.environ if env is None else env
    home = Path.home() if home is None else home

    if model_dir is not None:
        return existing_dir(model_dir, "--model-dir")

    env_model_dir = env.get("PARAKEET_MODEL_DIR")
    if env_model_dir:
        return existing_dir(Path(env_model_dir), "PARAKEET_MODEL_DIR")

    if auto_handy_model:
        for candidate in handy_model_candidates(env=env, home=home):
            if candidate.is_dir():
                return candidate
        candidates = "\n".join(f"  - {path}" for path in handy_model_candidates(env=env, home=home))
        raise SystemExit(
            "Could not find Handy Parakeet model cache. Checked:\n"
            f"{candidates}\n"
            "Pass --model-dir explicitly if your Handy data directory is elsewhere."
        )

    raise SystemExit(
        "Missing model directory. Pass --model-dir, set PARAKEET_MODEL_DIR, "
        "or use --auto-handy-model to reuse a standard Handy model cache."
    )


def output_path_for(audio_path: Path, output_dir: Path) -> Path:
    return output_dir / f"{audio_path.stem}.txt"


def infer_quantization(model_dir: Path) -> str | None:
    if (
        (model_dir / "encoder-model.int8.onnx").is_file()
        and (model_dir / "decoder_joint-model.int8.onnx").is_file()
    ):
        return "int8"
    return None


def load_model(model_dir: Path, quantization: str):
    try:
        import onnx_asr
    except ImportError as error:
        raise SystemExit(
            "Missing Python package onnx-asr. Run via uv, for example:\n"
            "  uv run --with 'onnx-asr[cpu]' scripts/transcribe_with_parakeet.py "
            "--auto-handy-model /tmp/chunk.wav"
        ) from error

    resolved_quantization = infer_quantization(model_dir) if quantization == "auto" else quantization
    kwargs = {"quantization": resolved_quantization} if resolved_quantization else {}
    return onnx_asr.load_model("nemo-conformer-tdt", str(model_dir), **kwargs)


def transcribe_audio_files(model, audio_paths: Sequence[Path]) -> list[tuple[Path, str]]:
    results: list[tuple[Path, str]] = []
    for audio_path in audio_paths:
        if not audio_path.is_file():
            raise SystemExit(f"Audio file does not exist: {audio_path}")
        text = model.recognize(str(audio_path))
        results.append((audio_path, str(text).strip()))
    return results


def write_results(results: Sequence[tuple[Path, str]], output_dir: Path | None) -> None:
    if output_dir is None:
        for index, (audio_path, text) in enumerate(results):
            if len(results) > 1:
                if index:
                    print()
                print(f"### {audio_path}")
            print(text)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    for audio_path, text in results:
        out_path = output_path_for(audio_path, output_dir)
        out_path.write_text(text + "\n", encoding="utf-8")
        print(out_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcribe prepared audio chunks with a local Parakeet ONNX model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""Examples:
  # Reuse Handy's standard Linux/macOS model cache if present:
  uv run --with 'onnx-asr[cpu]' scripts/transcribe_with_parakeet.py \\
    --auto-handy-model /tmp/libolibo-stream/chunk-001.wav

  # Pass a model directory explicitly:
  export PARAKEET_MODEL_DIR="${{XDG_DATA_HOME:-$HOME/.local/share}}/com.pais.handy/models/{DEFAULT_HANDY_MODEL_NAME}"
  uv run --with 'onnx-asr[cpu]' scripts/transcribe_with_parakeet.py \\
    --model-dir "$PARAKEET_MODEL_DIR" --output-dir /tmp/libolibo-stream/transcripts \\
    /tmp/libolibo-stream/chunk-*.wav

Notes:
  - Prepare audio chunks separately with ffmpeg/yt-dlp.
  - WAV PCM chunks are the safest input format for onnx-asr.
  - Quantization defaults to auto; Handy's Parakeet V3 cache is detected as int8.
  - The script never downloads a model by itself.
""",
    )
    parser.add_argument("audio", nargs="+", type=Path, help="Audio file(s) to transcribe.")
    parser.add_argument("--model-dir", type=Path, help="Local Parakeet ONNX model directory.")
    parser.add_argument(
        "--auto-handy-model",
        action="store_true",
        help="Look for Handy's standard Parakeet V3 model cache in the app data directory.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Directory for .txt transcripts. Defaults to stdout.",
    )
    parser.add_argument(
        "--quantization",
        choices=["auto", "int8"],
        default="auto",
        help="Model quantization. Default: auto-detect int8 model files.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    model_dir = resolve_model_dir(args.model_dir, auto_handy_model=args.auto_handy_model)
    model = load_model(model_dir, args.quantization)
    results = transcribe_audio_files(model, args.audio)
    write_results(results, args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
