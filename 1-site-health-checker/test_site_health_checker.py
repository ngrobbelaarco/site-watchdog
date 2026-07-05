"""
test_site_health_checker.py

Unit tests for site_health_checker.py.

These tests use mocking for the network-dependent function (check_url) so
the suite runs instantly and deterministically, with no dependency on any
external site being up. Pure/logic functions (_extract_title, load_urls,
write_json_report) are tested directly against real inputs.

Run with:
    pytest test_site_health_checker.py -v
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error

import pytest

from site_health_checker import (
    CheckResult,
    _extract_title,
    check_url,
    load_urls,
    write_json_report,
    write_html_report,
    HEALTHY_STATUS_RANGE,
)


# ---------------------------------------------------------------------------
# _extract_title: pure function tests
# ---------------------------------------------------------------------------

class TestExtractTitle:
    def test_extracts_simple_title(self):
        html = "<html><head><title>Hello World</title></head></html>"
        assert _extract_title(html) == "Hello World"

    def test_extracts_title_with_attributes(self):
        html = '<title data-x="1">Spaced   Out   Title</title>'
        # Multiple internal whitespace should be collapsed to single spaces.
        assert _extract_title(html) == "Spaced Out Title"

    def test_returns_none_when_no_title_tag(self):
        html = "<html><body>No title here</body></html>"
        assert _extract_title(html) is None

    def test_returns_none_for_empty_title(self):
        html = "<title>   </title>"
        assert _extract_title(html) is None

    def test_case_insensitive_tag_matching(self):
        html = "<TITLE>Shouting Title</TITLE>"
        assert _extract_title(html) == "Shouting Title"

    def test_title_spanning_multiple_lines(self):
        html = "<title>\n  Multi\n  Line\n</title>"
        assert _extract_title(html) == "Multi Line"


# ---------------------------------------------------------------------------
# load_urls: file parsing tests
# ---------------------------------------------------------------------------

class TestLoadUrls:
    def test_loads_simple_list(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("https://example.com\nhttps://example.org\n")
        assert load_urls(f) == ["https://example.com", "https://example.org"]

    def test_skips_blank_lines(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("https://example.com\n\n\nhttps://example.org\n")
        assert load_urls(f) == ["https://example.com", "https://example.org"]

    def test_skips_comment_lines(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("# my sites\nhttps://example.com\n# another comment\n")
        assert load_urls(f) == ["https://example.com"]

    def test_strips_surrounding_whitespace(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("   https://example.com   \n")
        assert load_urls(f) == ["https://example.com"]

    def test_empty_file_returns_empty_list(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("")
        assert load_urls(f) == []


# ---------------------------------------------------------------------------
# check_url: network-dependent, mocked
# ---------------------------------------------------------------------------

class TestCheckUrl:
    def test_healthy_200_response(self):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"<title>Home Page</title>"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = check_url("https://example.com")

        assert result.ok is True
        assert result.status_code == 200
        assert result.has_title is True
        assert result.title == "Home Page"
        assert result.error is None

    def test_http_error_404_is_captured_not_raised(self):
        error = urllib.error.HTTPError(
            url="https://example.com/missing", code=404, msg="Not Found", hdrs=None, fp=None
        )
        with patch("urllib.request.urlopen", side_effect=error):
            result = check_url("https://example.com/missing")

        assert result.ok is False
        assert result.status_code == 404
        assert "HTTP error" in result.error

    def test_connection_failure_does_not_raise(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("nowhere to go")):
            result = check_url("https://this-does-not-resolve.invalid")

        assert result.ok is False
        assert result.status_code is None
        assert result.error is not None

    def test_redirect_status_counts_as_healthy(self):
        # A 301 is in HEALTHY_STATUS_RANGE (200-399) because a resolving
        # redirect is a healthy outcome, not a broken page.
        assert 301 in HEALTHY_STATUS_RANGE

    def test_server_error_status_is_unhealthy(self):
        assert 500 not in HEALTHY_STATUS_RANGE


# ---------------------------------------------------------------------------
# write_json_report: output correctness
# ---------------------------------------------------------------------------

class TestWriteJsonReport:
    def test_summary_counts_are_correct(self, tmp_path):
        results = [
            CheckResult("https://a.com", True, 200, 120.0, True, "A", None, "2026-01-01T00:00:00+00:00"),
            CheckResult("https://b.com", False, 500, 300.0, None, None, "server error", "2026-01-01T00:00:01+00:00"),
            CheckResult("https://c.com", True, 200, 90.0, True, "C", None, "2026-01-01T00:00:02+00:00"),
        ]
        out = tmp_path / "report.json"
        write_json_report(results, out)

        data = json.loads(out.read_text())
        assert data["total_checked"] == 3
        assert data["healthy_count"] == 2
        assert data["unhealthy_count"] == 1
        assert len(data["results"]) == 3

    def test_empty_results_list(self, tmp_path):
        out = tmp_path / "report.json"
        write_json_report([], out)
        data = json.loads(out.read_text())
        assert data["total_checked"] == 0
        assert data["healthy_count"] == 0


# ---------------------------------------------------------------------------
# write_html_report: doesn't crash on tricky input (HTML escaping)
# ---------------------------------------------------------------------------

class TestWriteHtmlReport:
    def test_escapes_angle_brackets_in_title(self, tmp_path):
        # A title containing "<script>" should never end up unescaped in the
        # report -- that would be a stored XSS bug in a tool a client opens
        # in their browser.
        result = CheckResult(
            "https://a.com", True, 200, 100.0, True, "<script>bad</script>",
            None, "2026-01-01T00:00:00+00:00",
        )
        out = tmp_path / "report.html"
        write_html_report([result], out)
        content = out.read_text()
        assert "<script>bad</script>" not in content
        assert "&lt;script&gt;" in content

    def test_writes_valid_looking_html(self, tmp_path):
        result = CheckResult("https://a.com", True, 200, 100.0, True, "A", None, "2026-01-01T00:00:00+00:00")
        out = tmp_path / "report.html"
        write_html_report([result], out)
        content = out.read_text()
        assert content.startswith("<!DOCTYPE html>")
        assert "https://a.com" in content


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
