# Site Health Checker

A lightweight command-line tool that checks a list of website URLs and
reports which ones are up, how fast they responded, and whether they
returned a real page. Built for freelancers and small agencies who
maintain several client websites and want a fast way to check "is
everything still working?" without logging into each site individually.

## What it does

Give it a text file with one URL per line, and it will:

- Check whether each URL is reachable and returns a healthy status code
- Measure response time in milliseconds
- Confirm the page actually returned content (not a blank error page)
- Produce two reports: a `.json` file for automation/logging, and a
  `.html` file that's readable and presentable — you could email it
  straight to a client

## Requirements

- Python 3.10 or later
- No external packages needed to run the tool itself (uses only the
  standard library — see [Design notes](#design-notes) for why)
- `pytest` is required only if you want to run the test suite

## Quick start

```bash
# 1. Create a text file listing the URLs you want to check
cat > urls.txt << EOF
https://example.com
https://example.com/pricing
https://example.com/blog
EOF

# 2. Run the checker
python site_health_checker.py --urls urls.txt --out report

# 3. Open the result
open report.html   # or double-click it in your file browser
```

### Options

| Flag | Description | Default |
|---|---|---|
| `--urls` | Path to a text file, one URL per line. Lines starting with `#` are treated as comments and skipped. | required |
| `--out` | Output filename prefix. Writes `<out>.json` and `<out>.html`. | `report` |
| `--timeout` | Per-request timeout in seconds. | `8` |

### Example output (real run against live sites)

This repo includes `sample_report.json` / `sample_report.html`, generated
by actually running the tool against four real URLs — including one
intentionally broken link — to demonstrate real behavior rather than a
mocked example:

| Status | URL | Code | Response time |
|---|---|---|---|
| OK | github.com | 200 | 187 ms |
| OK | pypi.org | 200 | 63 ms |
| ISSUE | npmjs.com | 403 | 128 ms |
| ISSUE | github.com/this-page-does-not-exist-xyz123 | 404 | 192 ms |

## Running the tests

```bash
pip install pytest
pytest test_site_health_checker.py -v
```

20 tests, covering title extraction, URL file parsing, network error
handling (timeouts, DNS failures, HTTP errors), report generation, and
an HTML-escaping check to make sure a page with `<script>` in its title
can never inject unescaped HTML into the report a client opens in their
browser.

## Design notes

- **Zero runtime dependencies.** A client might run this on a machine
  that isn't set up for Python development. Using only the standard
  library means `python site_health_checker.py` just works.
- **Failures are data, not exceptions.** A broken or slow URL is an
  expected, normal outcome for a health-check tool — so `check_url()`
  catches every network-level failure and returns it as a result, rather
  than letting one bad URL crash the whole run.
- **HTML output is escaped.** Page titles are pulled from live,
  untrusted web pages. The report generator escapes `<`, `>`, and `&`
  before writing them into HTML, so a malicious or malformed title can't
  break or inject into the report.

## Possible extensions

Ideas for taking this further on a real engagement: scheduled runs via
cron with email/Slack alerts on failure, a broken-internal-link crawler
(follow links found on the page, not just a fixed list), historical
tracking of response times to catch gradual slowdowns.
