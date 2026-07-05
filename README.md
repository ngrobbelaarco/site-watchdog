# Site Watchdog

A small toolkit built around one coherent concept — website health
monitoring for freelancers and agencies managing multiple client sites.
Each piece demonstrates a different skill, all tied to the same product
idea rather than three unrelated demos.

| Folder | Demonstrates | Stack |
|---|---|---|
| [`1-site-health-checker/`](./1-site-health-checker) | Python automation/scripting — checks a list of URLs for uptime, response time, and broken content | Python (standard library only) |
| [`2-qa-case-study/`](./2-qa-case-study) | QA methodology — spec-based test design, real bugs found and documented, verified fixes | Python, pytest |
| [`3-ui-dashboard/`](./3-ui-dashboard) | UI/frontend — an interactive dashboard visualizing site health data | HTML, CSS, JavaScript |

## Live demo

GitHub doesn't execute HTML/JS in its file viewer — it just shows the
source. To see the dashboard actually running:

- **Live link:** *(enable GitHub Pages — see below — then put the URL here)*
- **Locally:** download [`3-ui-dashboard/site-watchdog-dashboard.html`](./3-ui-dashboard/site-watchdog-dashboard.html) and open it directly in a browser (not through github.com).

The same applies to [`1-site-health-checker/sample_report.html`](./1-site-health-checker/sample_report.html), which is a static report (no interactivity by design — it's a report, not an app) but still needs to be opened as a file, not viewed as GitHub source, to see it styled correctly.

## Highlights

- **Everything here actually runs.** The health checker was executed against real live sites (see `sample_report.json`). The QA suite's bug reports are real pytest failures, not invented examples — 5/21 tests fail against the buggy code, all 21 pass after the fix.
- Zero runtime dependencies for the Python tool; pytest only needed to run tests.
- The dashboard is vanilla HTML/CSS/JS — no build step, no framework, opens directly in any browser.

## Running things locally

```bash
git clone https://github.com/ngrobbelaarco/site-watchdog.git
cd site-watchdog

# Project 1: run the health checker
cd 1-site-health-checker
python site_health_checker.py --urls urls.txt --out report
pip install pytest && pytest -v

# Project 2: run the QA suite
cd ../2-qa-case-study
pip install pytest && pytest test_task_manager.py -v
```

Each subfolder has its own README with full details.

## About this repo

Built as a portfolio project to demonstrate Python scripting, QA
testing practice, and front-end UI work in one cohesive package.
