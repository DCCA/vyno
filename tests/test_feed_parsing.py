import unittest

from digest.connectors.rss import parse_feed_items


class TestFeedParsing(unittest.TestCase):
    def test_atom_feed_parses_entries(self):
        xml = b"""<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <entry>
    <title>Video One</title>
    <link rel='alternate' href='https://youtube.com/watch?v=abc123'/>
    <published>2026-02-21T07:00:00Z</published>
    <summary>Latest AI video</summary>
    <author><name>Channel Name</name></author>
  </entry>
</feed>"""
        items = parse_feed_items("https://www.youtube.com/feeds/videos.xml?channel_id=abc", xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Video One")
        self.assertEqual(items[0].url, "https://youtube.com/watch?v=abc123")


if __name__ == "__main__":
    unittest.main()
