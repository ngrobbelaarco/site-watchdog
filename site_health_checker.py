"""
site_health_checker.py

A small CLI tool that checks a list of URLs and reports:
  - HTTP status code (and whether it counts as healthy)
  - Response time in milliseconds
  - Whether the page returned a <title> tag (a cheap proxy for "did we get
    a real page back, not an error stub or empty response")

Why this exists
----------------
Freelance clients who run a website (a small business, an agency managing
several client sites, a blog) regularly want to know: "are my pages up,
and are any of them slow or broken?" This script answers that in one run
and produces both a machine-readable JSON report and a simple HTML report
that's easy to hand to a non-technical client.

Usage
-----
    python site_health_checker.py --urls urls.txt --out report
    python site_health_checker.py --urls urls.txt --out report --timeout 5

This writes report.json and report.html into the current directory.

Design notes
------------
- Uses only the standard library (urllib) so it runs anywhere with no
  pip install required -- a deliberate choice for a tool a client might
  run on a machine that isn't set up for Python development.
- Every network call is wrapped so one broken URL never crashes the run;
  failures are captured as results, not exceptions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 8
USER_AGENT = "site-health-checker/1.0 (+portfolio-project)"

# Status codes we still treat as "reachable" even though they're not 200,
# because a redirect chain resolving correctly is a healthy outcome too.
HEALTHY_STATUS_RANGE = range(200, 400)


@dataclass
class CheckResult:
    url: str
    ok: bool
    status_code: int | None
    response_time_ms: float | None
    has_title: bool | None
    title: str | None
    error: str | None
    checked_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def check_url(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> CheckResult:
    """Check a single URL and return a CheckResult.

    This function never raises for network-level problems (timeouts, DNS
    failures, connection resets, HTTP error statuses). Those are all
    captured and returned as a non-ok CheckResult, because a broken URL
    is an expected, normal outcome for this tool -- not an exceptional one.
    """
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            elapsed_ms = (time.perf_counter() - start) * 1000
            status_code = response.status
            body = response.read(200_000).decode("utf-8", errors="replace")
            title = _extract_title(body)
            return CheckResult(
                url=url,
                ok=status_code in HEALTHY_STATUS_RANGE,
                status_code=status_code,
                response_time_ms=round(elapsed_ms, 1),
                has_title=title is not None,
                title=title,
                error=None,
                checked_at=checked_at,
            )
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return CheckResult(
            url=url,
            ok=exc.code in HEALTHY_STATUS_RANGE,
            status_code=exc.code,
            response_time_ms=round(elapsed_ms, 1),
            has_title=None,
            title=None,
            error=f"HTTP error: {exc.reason}",
            checked_at=checked_at,
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return CheckResult(
            url=url,
            ok=False,
            status_code=None,
            response_time_ms=None,
            has_title=None,
            title=None,
            error=f"{type(exc).__name__}: {exc}",
            checked_at=checked_at,
        )


def _extract_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip() or None


def check_urls(urls: list[str], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> list[CheckResult]:
    return [check_url(url, timeout=timeout) for url in urls]


def load_urls(path: Path) -> list[str]:
    urls = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def write_json_report(results: list[CheckResult], out_path: Path) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_checked": len(results),
        "healthy_count": sum(1 for r in results if r.ok),
        "unhealthy_count": sum(1 for r in results if not r.ok),
        "results": [r.to_dict() for r in results],
    }
    out_path.write_text(json.dumps(payload, indent=2))


def write_html_report(results: list[CheckResult], out_path: Path) -> None:
    rows = []
    for r in results:
        status_label = "OK" if r.ok else "ISSUE"
        status_class = "ok" if r.ok else "issue"
        status_code = r.status_code if r.status_code is not None else "—"
        response_time = f"{r.response_time_ms:.0f} ms" if r.response_time_ms is not None else "—"
        detail = r.error or (r.title or "(no title found)")
        rows.append(
            f"""
            <tr class="{status_class}">
              <td>{status_label}</td>
              <td><code>{_escape(r.url)}</code></td>
              <td>{status_code}</td>
              <td>{response_time}</td>
              <td>{_escape(detail)}</td>
            </tr>"""
        )

    healthy = sum(1 for r in results if r.ok)
    total = len(results)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Site Health Report</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; background: #f4f5f7; color: #1a1f26; padding: 2rem; }}
  h1 {{ margin-bottom: 0.25rem; }}
  .summary {{ color: #4b5563; margin-bottom: 1.5rem; }}
  table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  th, td {{ text-align: left; padding: 0.6rem 0.9rem; border-bottom: 1px solid #e5e7eb; font-size: 0.92rem; }}
  th {{ background: #eef0f3; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.04em; color: #4b5563; }}
  tr.ok td:first-child {{ color: #15803d; font-weight: 600; }}
  tr.issue td:first-child {{ color: #b91c1c; font-weight: 600; }}
  code {{ font-size: 0.85rem; }}
</style>
</head>
<body>
  <h1>Site Health Report</h1>
  <p class="summary">{healthy} of {total} URLs healthy — generated {datetime.now(timezone.utc).isoformat(timespec="seconds")}</p>
  <table>
    <tr><th>Status</th><th>URL</th><th>Code</th><th>Response time</th><th>Detail</th></tr>
    {"".join(rows)}
  </table>
</body>
</html>"""
    out_path.write_text(html)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a list of URLs for uptime, speed, and basic health.")
    parser.add_argument("--urls", required=True, type=Path, help="Path to a text file, one URL per line.")
    parser.add_argument("--out", default="report", help="Output filename prefix (writes <out>.json and <out>.html).")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Per-request timeout in seconds.")
    args = parser.parse_args(argv)

    if not args.urls.exists():
        print(f"Error: {args.urls} not found.", file=sys.stderr)
        return 1

    urls = load_urls(args.urls)
    if not urls:
        print("Error: no URLs found in input file.", file=sys.stderr)
        return 1

    print(f"Checking {len(urls)} URL(s)...")
    results = check_urls(urls, timeout=args.timeout)

    json_path = Path(f"{args.out}.json")
    html_path = Path(f"{args.out}.html")
    write_json_report(results, json_path)
    write_html_report(results, html_path)

    healthy = sum(1 for r in results if r.ok)
    print(f"Done: {healthy}/{len(results)} healthy.")
    print(f"Reports written to {json_path} and {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
