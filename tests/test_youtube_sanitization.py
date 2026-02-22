import unittest

from digest.pipeline.clean_text import clean_youtube_text


class TestYoutubeSanitization(unittest.TestCase):
    def test_removes_sponsor_cta_line(self):
        text = "Check out Lambda GPU Cloud now!\nReal-time relighting in neural shaders."
        out = clean_youtube_text(text)
        self.assertNotIn("Check out", out)
        self.assertIn("Real-time relighting", out)

    def test_removes_patreon_block(self):
        text = "Our Patreon if you wish to support us\nGreat rendering method"
        out = clean_youtube_text(text)
        self.assertNotIn("Patreon", out)
        self.assertIn("Great rendering method", out)

    def test_removes_hashtag_tail(self):
        text = "Paper shows fast denoising\n#ai #nvidia #adobe"
        out = clean_youtube_text(text)
        self.assertNotIn("#ai", out)
        self.assertIn("Paper shows", out)

    def test_collapses_repeated_urls(self):
        text = "Read this https://x.com/a https://x.com/a then details"
        out = clean_youtube_text(text)
        self.assertLessEqual(out.count("https://x.com/a"), 1)

    def test_removes_sources_section(self):
        text = "Key point here\nSources:\nhttps://a.com\nhttps://b.com\nEnd"
        out = clean_youtube_text(text)
        self.assertNotIn("Sources:", out)
        self.assertNotIn("https://a.com", out)
        self.assertIn("Key point", out)

    def test_preserves_first_meaningful_sentence(self):
        text = "\n\nThis method enables real-time glossy transport.\nCheck out sponsor"
        out = clean_youtube_text(text)
        self.assertTrue(out.startswith("This method enables"))

    def test_preserves_technical_keywords(self):
        text = "Differentiable rendering with NeRF and shader fusion"
        out = clean_youtube_text(text)
        self.assertIn("Differentiable", out)
        self.assertIn("NeRF", out)

    def test_handles_emoji_heavy_lines(self):
        text = "❤️❤️❤️ Check out our sponsor\nNew CUDA kernel for denoising"
        out = clean_youtube_text(text)
        self.assertNotIn("sponsor", out.lower())
        self.assertIn("CUDA kernel", out)

    def test_handles_empty_text(self):
        self.assertEqual(clean_youtube_text("   \n  "), "")

    def test_keeps_short_clean_text_unchanged(self):
        text = "Novel benchmark for agent planning"
        out = clean_youtube_text(text)
        self.assertEqual(out, text)


if __name__ == "__main__":
    unittest.main()
