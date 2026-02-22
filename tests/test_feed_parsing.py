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

    def test_rdf_feed_parses_items(self):
        xml = b"""<?xml version='1.0'?>
<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
         xmlns='http://purl.org/rss/1.0/'
         xmlns:dc='http://purl.org/dc/elements/1.1/'>
  <item rdf:about='https://example.com/post-1'>
    <title>RDF Title</title>
    <link>https://example.com/post-1</link>
    <description>RDF description</description>
    <dc:date>2026-02-21T07:00:00Z</dc:date>
    <dc:creator>Author X</dc:creator>
  </item>
</rdf:RDF>"""
        items = parse_feed_items("https://example.com/rdf.xml", xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "RDF Title")
        self.assertEqual(items[0].url, "https://example.com/post-1")
        self.assertEqual(items[0].author, "Author X")

    def test_generic_namespaced_feed_parses_entries(self):
        xml = b"""<?xml version='1.0'?>
<root xmlns:a='http://example.com/a'>
  <a:entry>
    <a:title>Generic Entry</a:title>
    <a:link href='https://example.com/generic' />
    <a:summary>Generic description</a:summary>
    <a:updated>2026-02-21T10:30:00Z</a:updated>
  </a:entry>
</root>"""
        items = parse_feed_items("https://example.com/generic.xml", xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Generic Entry")
        self.assertEqual(items[0].url, "https://example.com/generic")


if __name__ == "__main__":
    unittest.main()
