# X Daily Automation Bot

Automates daily discovery of new posts from your X account, creates **promotion planning records** (no artificial-engagement order placement), writes JSON state, generates Markdown reports, and can optionally send Telegram notifications.

> Schedule is configured for **17:00 UTC** (11:00 PM Bangladesh time). GitHub Actions schedules can be delayed by GitHub load.

## Important compliance notes

- Uses official **X API v2** only.
- Does **not** scrape X pages.
- Does **not** submit SMMSOC engagement orders.
- SMMSOC docs host (`https://smmsoc.com/api`) may be inaccessible from some environments; when inaccessible, endpoint/field verification is limited to documented values you provide.

## Project structure

- `x-daily-automation/main.py` - daily entrypoint
- `x-daily-automation/src/*` - clients, scanner, storage, reporting, Telegram helper
- `x-daily-automation/tests/*` - pytest suite with mocked API behavior
- `.github/workflows/daily.yml` - scheduled workflow

## 1) Create/use a GitHub repository

```bash
git init
git add .
git commit -m "Initial X daily automation bot"
```

If already in a repository, skip `git init`.

## 2) Python setup on macOS

```bash
cd /path/to/repo
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r x-daily-automation/requirements.txt
```

## 3) Obtain X API credentials

1. Create a developer app in X Developer Portal.
2. Generate a ****** with read permissions.
3. Set:
   - `X_BEARER_TOKEN`
   - `X_USERNAME`
   - Optional `X_USER_ID` (auto-resolved if omitted)

## 4) Add GitHub Actions secrets

In GitHub: **Settings → Secrets and variables → Actions → New repository secret**.

Required:
- `X_BEARER_TOKEN`
- `X_USERNAME`

Optional:
- `X_USER_ID`, `X_INCLUDE_QUOTES`
- `SMM_API_URL`, `SMM_API_KEY`, `SMM_IMPRESSION_SERVICE_ID`, `SMM_LIKE_SERVICE_ID`
- `TELEGRAM_ENABLED`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## 5) Configure SMMSOC credentials

Copy env template and fill values:

```bash
cp x-daily-automation/.env.example x-daily-automation/.env
```

The default documented base URL is `https://smmsoc.com/api/v2`.

## 6) Enable GitHub Actions

- Ensure Actions are enabled for the repository.
- Confirm workflow file exists at `.github/workflows/daily.yml`.

## 7) Run workflow manually

From GitHub UI:
- Actions → **Daily X automation** → **Run workflow**.

Or run locally:

```bash
python x-daily-automation/main.py
```

## 8) Verify first report

Check:
- `x-daily-automation/data/state.json`
- `x-daily-automation/reports/report-YYYY-MM-DD.md`

## 9) Troubleshooting

- `401` from X API: invalid `X_BEARER_TOKEN`
- `401` from SMMSOC: invalid `SMM_API_KEY`
- lock-file error: overlapping run detected
- state parse error: inspect and repair state file, then optionally run once with `ALLOW_STATE_RECOVERY=true`

## 10) Recover from failed scans

- Failed scans do **not** advance `last_successful_scan_at`.
- Fix root cause and rerun.
- Overlap window prevents missing posts after transient failures.

## 11) Disable automation

- Remove schedule trigger from workflow, or disable workflow in GitHub Actions UI.

## 12) Estimate costs

- Infrastructure: GitHub Actions free-tier dependent.
- X API: depends on your X API access tier.
- SMMSOC spend: only report/inspection unless you separately authorize campaign/order systems.

## Useful commands

```bash
pytest x-daily-automation/tests -q
python x-daily-automation/main.py
```
