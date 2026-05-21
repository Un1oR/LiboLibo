#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).with_name("transcribe_youtube_with_parakeet.py")
SPEC = importlib.util.spec_from_file_location("transcribe_youtube_with_parakeet", SCRIPT_PATH)
youtube = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(youtube)


class TranscribeYoutubeWithParakeetTests(unittest.TestCase):
    def test_section_slug_is_filesystem_safe(self):
        self.assertEqual(
            youtube.section_slug("00:01:02-00:03:04"),
            "00-01-02_00-03-04",
        )

    def test_download_command_limits_download_to_requested_section(self):
        command = youtube.download_command(
            url="https://www.youtube.com/watch?v=mKjCHo7GKko",
            section="00:00:00-00:30:00",
            output_template=Path("/tmp/libolibo/section-001.%(ext)s"),
        )

        self.assertEqual(command[0], "yt-dlp")
        self.assertIn("--download-sections", command)
        self.assertIn("*00:00:00-00:30:00", command)
        self.assertIn("worstaudio/worst", command)
        self.assertEqual(command[-1], "https://www.youtube.com/watch?v=mKjCHo7GKko")

    def test_split_command_creates_pcm_wav_chunks(self):
        command = youtube.split_command(
            audio_path=Path("/tmp/libolibo/section-001.m4a"),
            chunk_seconds=25,
            chunk_pattern=Path("/tmp/libolibo/chunks/section-001-%04d.wav"),
        )

        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("-segment_time", command)
        self.assertIn("25", command)
        self.assertIn("pcm_s16le", command)
        self.assertEqual(command[-1], "/tmp/libolibo/chunks/section-001-%04d.wav")

    def test_transcribe_command_reuses_handy_cache_by_default(self):
        command = youtube.transcribe_command(
            python_executable="/usr/bin/python3",
            transcribe_script=Path("scripts/transcribe_with_parakeet.py"),
            chunks=[Path("/tmp/chunks/a.wav"), Path("/tmp/chunks/b.wav")],
            output_dir=Path("/tmp/transcripts"),
            model_dir=None,
            auto_handy_model=True,
        )

        self.assertEqual(command[:2], ["/usr/bin/python3", "scripts/transcribe_with_parakeet.py"])
        self.assertIn("--auto-handy-model", command)
        self.assertNotIn("--model-dir", command)
        self.assertEqual(command[-2:], ["/tmp/chunks/a.wav", "/tmp/chunks/b.wav"])

    def test_transcribe_command_can_pass_explicit_model_dir(self):
        command = youtube.transcribe_command(
            python_executable="/usr/bin/python3",
            transcribe_script=Path("scripts/transcribe_with_parakeet.py"),
            chunks=[Path("/tmp/chunks/a.wav")],
            output_dir=Path("/tmp/transcripts"),
            model_dir=Path("/models/parakeet"),
            auto_handy_model=True,
        )

        self.assertIn("--model-dir", command)
        self.assertIn("/models/parakeet", command)
        self.assertNotIn("--auto-handy-model", command)

    def test_find_downloaded_audio_rejects_missing_section_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as error:
                youtube.find_downloaded_audio(Path(tmp), "section-001")

            self.assertIn("No downloaded audio found", str(error.exception))

    def test_combined_transcript_orders_chunk_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcripts = Path(tmp) / "transcripts"
            transcripts.mkdir()
            (transcripts / "section-001-0001.txt").write_text("second\n", encoding="utf-8")
            (transcripts / "section-001-0000.txt").write_text("first\n", encoding="utf-8")
            combined = Path(tmp) / "combined.md"

            youtube.write_combined_transcript([transcripts], combined)

            self.assertEqual(
                combined.read_text(encoding="utf-8"),
                "# Transcript\n\n## section-001-0000\n\nfirst\n\n## section-001-0001\n\nsecond\n",
            )

    def test_dry_run_prints_shell_quoted_command(self):
        with patch("builtins.print") as print_mock:
            youtube.run_command(["yt-dlp", "--download-sections", "*00:00:00-00:30:00"], dry_run=True)

        print_mock.assert_called_once_with(
            "$ yt-dlp --download-sections '*00:00:00-00:30:00'",
            flush=True,
        )


if __name__ == "__main__":
    unittest.main()
