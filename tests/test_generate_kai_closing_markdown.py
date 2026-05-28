import unittest

from generate_kai_closing_markdown import classify_chunk, format_timestamp


class GenerateKaiClosingMarkdownTests(unittest.TestCase):
    def test_format_timestamp_rounds_to_minutes_and_seconds(self):
        self.assertEqual(format_timestamp(83.2), "01:23")

    def test_classify_chunk_detects_commentary(self):
        text = "So, right there, pre-framing the call. I'm explaining why I say it that way."
        self.assertEqual(classify_chunk(text), "commentary")


if __name__ == "__main__":
    unittest.main()
