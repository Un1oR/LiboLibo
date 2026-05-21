#!/usr/bin/env python3
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("transcribe_with_parakeet.py")
SPEC = importlib.util.spec_from_file_location("transcribe_with_parakeet", SCRIPT_PATH)
transcribe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transcribe)


class TranscribeWithParakeetTests(unittest.TestCase):
    def test_model_dir_prefers_cli_argument_over_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            cli_model = Path(tmp) / "cli-model"
            env_model = Path(tmp) / "env-model"
            cli_model.mkdir()
            env_model.mkdir()

            resolved = transcribe.resolve_model_dir(
                cli_model,
                auto_handy_model=False,
                env={"PARAKEET_MODEL_DIR": str(env_model)},
                home=Path(tmp),
            )

            self.assertEqual(resolved, cli_model)

    def test_model_dir_uses_environment_when_cli_argument_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_model = Path(tmp) / "env-model"
            env_model.mkdir()

            resolved = transcribe.resolve_model_dir(
                None,
                auto_handy_model=False,
                env={"PARAKEET_MODEL_DIR": str(env_model)},
                home=Path(tmp),
            )

            self.assertEqual(resolved, env_model)

    def test_auto_handy_model_finds_xdg_data_home_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = (
                Path(tmp)
                / "xdg"
                / "com.pais.handy"
                / "models"
                / transcribe.DEFAULT_HANDY_MODEL_NAME
            )
            model.mkdir(parents=True)

            resolved = transcribe.resolve_model_dir(
                None,
                auto_handy_model=True,
                env={"XDG_DATA_HOME": str(Path(tmp) / "xdg")},
                home=Path(tmp),
            )

            self.assertEqual(resolved, model)

    def test_missing_model_dir_explains_how_to_reuse_handy_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as error:
                transcribe.resolve_model_dir(
                    None,
                    auto_handy_model=False,
                    env={},
                    home=Path(tmp),
                )

            self.assertIn("--model-dir", str(error.exception))
            self.assertIn("PARAKEET_MODEL_DIR", str(error.exception))
            self.assertIn("--auto-handy-model", str(error.exception))

    def test_output_path_uses_txt_extension_for_each_audio_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / "chunk-001.wav"
            audio.write_bytes(b"not real audio")
            out_dir = Path(tmp) / "out"

            self.assertEqual(
                transcribe.output_path_for(audio, out_dir),
                out_dir / "chunk-001.txt",
            )

    def test_infer_quantization_detects_handy_int8_model_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "model"
            model.mkdir()
            (model / "encoder-model.int8.onnx").write_bytes(b"")
            (model / "decoder_joint-model.int8.onnx").write_bytes(b"")

            self.assertEqual(transcribe.infer_quantization(model), "int8")

    def test_infer_quantization_uses_default_for_non_quantized_model_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "model"
            model.mkdir()
            (model / "encoder-model.onnx").write_bytes(b"")
            (model / "decoder_joint-model.onnx").write_bytes(b"")

            self.assertIsNone(transcribe.infer_quantization(model))


if __name__ == "__main__":
    unittest.main()
