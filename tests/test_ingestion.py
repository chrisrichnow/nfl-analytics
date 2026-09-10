import unittest

from ingestion.load_raw import parse_seasons


class SeasonParserTests(unittest.TestCase):
    def test_inclusive_range(self):
        self.assertEqual(parse_seasons("2019-2025"), list(range(2019, 2026)))

    def test_combines_deduplicates_and_sorts(self):
        self.assertEqual(parse_seasons("2025, 2019-2021, 2020"), [2019, 2020, 2021, 2025])

    def test_rejects_descending_range(self):
        with self.assertRaises(ValueError):
            parse_seasons("2025-2019")

    def test_rejects_unsupported_year(self):
        with self.assertRaises(ValueError):
            parse_seasons("1998")

    def test_rejects_empty_input(self):
        with self.assertRaises(ValueError):
            parse_seasons("")


if __name__ == "__main__":
    unittest.main()
