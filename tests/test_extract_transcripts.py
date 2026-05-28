import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from extract_transcripts import (
    extract_bulk_transcripts,
    extract_single_transcript,
    load_video_ids,
    output_file_path,
    save_to_json,
)


class ExtractSingleTranscriptTests(unittest.TestCase):
    @patch("extract_transcripts.fetch_transcript")
    def test_extract_single_transcript_returns_joined_text(self, fetch_transcript):
        fetch_transcript.return_value = [
            SimpleNamespace(start=1.2, text="Hello"),
            SimpleNamespace(start=2.8, text="world"),
        ]

        result = extract_single_transcript("abc123def45")

        fetch_transcript.assert_called_once_with("abc123def45", "en")
        self.assertEqual(result["video_id"], "abc123def45")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["transcript"], "Hello world")
        self.assertIsNone(result["error"])

    @patch("extract_transcripts.fetch_transcript")
    def test_extract_single_transcript_can_include_timestamps(self, fetch_transcript):
        fetch_transcript.return_value = [
            SimpleNamespace(start=1.234, text="Hello"),
            SimpleNamespace(start=2.0, text="world"),
        ]

        result = extract_single_transcript("abc123def45", include_timestamps=True)

        self.assertEqual(result["transcript"], "[1.23s] Hello\n[2.00s] world")

    @patch("extract_transcripts.fetch_transcript")
    def test_extract_single_transcript_handles_failures(self, fetch_transcript):
        fetch_transcript.side_effect = RuntimeError("transcript unavailable")

        result = extract_single_transcript("abc123def45")

        self.assertEqual(result["video_id"], "abc123def45")
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["transcript"])
        self.assertEqual(result["error"], "transcript unavailable")

    def test_extract_bulk_transcripts_preserves_input_order(self):
        def fake_extract(video_id, include_timestamps=False, lang="en"):
            return {
                "video_id": video_id,
                "transcript": video_id,
                "status": "success",
                "error": None,
            }

        with patch("extract_transcripts.extract_single_transcript", side_effect=fake_extract):
            results = extract_bulk_transcripts(
                ["first", "second", "third"],
                max_workers=3,
                show_progress=False,
            )

        self.assertEqual([result["video_id"] for result in results], ["first", "second", "third"])

    def test_load_video_ids_ignores_blank_lines_and_comments(self):
        with TemporaryDirectory() as temp_dir:
            ids_path = Path(temp_dir) / "ids.txt"
            ids_path.write_text(
                "\n# a comment\nhttps://youtu.be/dQw4w9WgXcQ\n"
                "https://www.youtube.com/watch?v=abc123def45&list=demo\n",
                encoding="utf-8",
            )

            self.assertEqual(
                load_video_ids([str(ids_path)]),
                ["dQw4w9WgXcQ", "abc123def45"],
            )

    def test_load_video_ids_accepts_raw_ids_and_urls(self):
        self.assertEqual(
            load_video_ids(["raw123", "www.youtube.com/shorts/short123"]),
            ["raw123", "short123"],
        )

    def test_output_file_path_does_not_duplicate_extension(self):
        self.assertEqual(output_file_path("transcripts", "json"), Path("transcripts.json"))
        self.assertEqual(output_file_path("transcripts.json", "json"), Path("transcripts.json"))

    def test_save_to_json_creates_parent_directories(self):
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nested" / "transcripts.json"
            with redirect_stdout(StringIO()):
                save_to_json(
                    [
                        {
                            "video_id": "abc123def45",
                            "transcript": "Hello world",
                            "status": "success",
                            "error": None,
                        }
                    ],
                    output_path,
                )

            self.assertTrue(output_path.is_file())


if __name__ == "__main__":
    unittest.main()
