import unittest
from datetime import datetime, timezone, timedelta

from timestamp_parser_range import parse_timestamp, split_range, parse_range


class TestParseTimestamp(unittest.TestCase):
    def test_zulu_with_fractional(self):
        ts = parse_timestamp("2024-01-02T03:04:05.678911Z")
        self.assertEqual(
            ts,
            datetime(2024, 1, 2, 3, 4, 5, 678911, timezone.utc),
        )

    def test_explicit_offset_positive(self):
        ts = parse_timestamp("2024-01-02T03:04:05+05:30")
        expected = datetime(
            2024, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=5, minutes=30))
        )
        self.assertEqual(ts, expected)

    def test_explicit_offset_negative(self):
        ts = parse_timestamp("2024-01-02T03:04:05-08:00")
        expected = datetime(
            2024, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=-8))
        )
        self.assertEqual(ts, expected)

    def test_fractional_one_digit(self):
        ts = parse_timestamp("2024-01-02T03:04:05.5Z")
        # ".5" = 500000us
        self.assertEqual(ts.microsecond, 500000)

    def test_fractional_truncated_not_rounded(self):
        ts = parse_timestamp("2024-01-02T03:04:05.9999999Z")
        # Truncate, do not round up to the next second.
        self.assertEqual(ts.microsecond, 999999)
        self.assertEqual(ts.second, 5)

    def test_no_fractional(self):
        ts = parse_timestamp("2024-01-02T03:04:05Z")
        self.assertEqual(ts.microsecond, 0)

    def test_rejects_naive(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02T03:04:05")

    def test_rejects_space_separator(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02 03:04:05Z")

    def test_rejects_offset_without_colon(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02T03:04:05+0500")

    def test_rejects_offset_hours_out_of_range(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02T03:04:05+24:00")

    def test_rejects_offset_minutes_out_of_range(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02T03:04:05+05:60")

    def test_rejects_invalid_calendar(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-13-01T00:00:00Z")

    def test_rejects_non_string(self):
        with self.assertRaises(ValueError):
            parse_timestamp(12345)  # type: ignore[arg-type]

    def test_rejects_trailing_garbage(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02T03:04:05Zextra")


class TestSplitRange(unittest.TestCase):
    def test_basic_split(self):
        a, b = split_range("2024-01-02T00:00:00Z/2024-01-03T00:00:00Z")
        self.assertEqual(a, "2024-01-02T00:00:00Z")
        self.assertEqual(b, "2024-01-03T00:00:00Z")

    def test_missing_slash_rejected(self):
        with self.assertRaises(ValueError):
            split_range("2024-01-02T00:00:00Z")

    def test_too_many_slashes_rejected(self):
        with self.assertRaises(ValueError):
            split_range("a/b/c")

    def test_empty_segment_rejected(self):
        with self.assertRaises(ValueError):
            split_range("2024-01-02T00:00:00Z/")

    def test_leading_slash_rejected(self):
        with self.assertRaises(ValueError):
            split_range("/2024-01-02T00:00:00Z")


class TestParseRange(unittest.TestCase):
    def test_both_endpoints_parsed(self):
        start, end = parse_range("2024-01-02T03:04:05Z/2024-01-02T06:06:06Z")
        self.assertEqual(start, datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
        self.assertEqual(end, datetime(2024, 1, 2, 6, 6, 6, tzinfo=timezone.utc))

    def test_mixed_offsets(self):
        start, end = parse_range(
            "2024-01-02T03:04:05+02:00/2024-01-02T01:04:05Z"
        )
        # Both represent the same instant.
        self.assertEqual(start, end)

    def test_bad_endpoint_raises(self):
        with self.assertRaises(ValueError):
            parse_range("not-a-timestamp/2024-01-02T00:00:00Z")

    def test_double_solidus_not_supported(self):
        with self.assertRaises(ValueError):
            parse_range("2024-01-02T00:00:00Z//P1D")


if __name__ == "__main__":
    unittest.main()
