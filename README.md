# timestamp_parser_range

A small library for parsing a strict subset of ISO 8601 timestamps and `start/end` intervals into Python `datetime` objects. No third-party dependencies.

## Usage

```python
from timestamp_parser_range import parse_timestamp, split_range, parse_range

t = parse_timestamp("2024-01-02T03:04:05.678911Z")
# datetime(2024, 1, 2, 3, 4, 5, 678911, tzinfo=timezone.utc)

start, end = parse_range("2024-01-02T03:04:05+02:00/2024-01-02T01:04:05Z")
# Both endpoints represent the same instant.
```

## Why

The standard library's `datetime.fromisoformat` accepts a variety of shapes and will happily return a naive datetime if no offset is present. That ambiguity is a liability when timestamps are used as sort keys or deduplication keys. This library accepts exactly one shape — `YYYY-MM-DDTHH:MM:SS[.ffffff](Z|+HH:MM|-HH:MM)` — and requires an offset, so every returned `datetime` is timezone-aware and unambiguous.

Fractional seconds are truncated to microseconds rather than rounded, because rounding could silently push a value into the next second.

## Awkward edge

Interval parsing supports only the `<start>/<end>` solidus form. The double-solidus form (`<start>//<duration>`) is deliberately not supported: a string like `2020-01-01T00:00:00Z//P1D` would be ambiguous between "start//duration" and "start/end" where the end begins with `/P`. If you need duration syntax, parse it yourself before calling this library.

Offset hours are capped at 23 and minutes at 59, matching RFC 3339. Real-world offsets do not exceed these, but the grammar alone (two digits) would permit `+99:99`.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

