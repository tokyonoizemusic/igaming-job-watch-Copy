# European iGaming Job Watch — V6

An incremental update of the user's GitHub Pages website. **Do not upload a private application JSON backup to the public repository.**

**Public website:** `https://tokyonoizemusic.github.io/igaming-job-watch-Copy/`

## What changed

1. **Desktop/landscape fix:** Backup controls were moved from the right sidebar to a full-width panel immediately above the job list. Import JSON / Export JSON / Export CSV remain reachable at laptop and mobile sizes.
2. **31 monitored employer sources:** four public ATS endpoints (Oddin.gg, Betsson Group, Playtech, Enjoy Gaming) plus 27 public employer careers pages. The jobs collector uses structured JobPosting data and public job links when available. Pages without extractable vacancies are reported as having **0 extractable matches**, not as proof of no vacancies.
3. **Best-effort LinkedIn-indexed discovery:** four small public Bing RSS web-search queries daily, looking for `linkedin.com/jobs/view/` links. This is **not direct LinkedIn access**, is not complete, may produce no results, and does **not verify that posts are still open**. Every such entry is prominently tagged *Search-index lead — NOT verified open*.
4. **Optional Google Alerts RSS:** Configure Google Alerts for `site:linkedin.com/jobs/view/` job titles. Paste *RSS feed URLs* (one per line) into a GitHub Actions repository secret named `JOB_ALERT_RSS_URLS` to supplement the default search. Do not commit private feed URLs to the public repository. Results are tagged unverified.
5. **Application preservation:** the browser's localStorage key remains `european_igaming_job_watch_v1`. The daily public feed merges by vacancy URL or ID and preserves status/bookmarks/notes, so applied jobs should not reset. Back up first anyway.
6. **GitHub workflow:** daily 08:13 `Europe/Bucharest` (timezone aware), manual run, updated checkout/setup-python versions, safe fetch/rebase before publishing without force push. GitHub Actions schedules are best-effort and may run late.

## Upgrade your existing repo (recommended)

The `V6_Upgrade.zip` includes ONLY new/changed files. **It does not include `public/data/jobs.json`** to avoid overwriting the snapshot already in your GitHub repo.

1. Before updating, open your live website *on the browser where you marked jobs Applied*, click **Export JSON backup**, and keep the file privately. Your latest supplied backup had seven applied roles, including Kendoo and ARRISE.
2. Extract `European_iGaming_Job_Watch_V6_Upgrade.zip` on your computer. Ensure hidden `.github` directory is visible.
3. In GitHub repository `tokyonoizemusic/igaming-job-watch-Copy`, upload/replace these files **at the same paths**:

```
public/index.html
scripts/update_jobs.py
scripts/sources_extra.py
scripts/test_extra_sources.py
scripts/test_update_jobs.py
.github/workflows/daily-refresh.yml
README.md
```

4. Open **Actions > Daily iGaming jobs refresh & publish > Run workflow**. Check that the test, refresh, commit and Pages deployment steps all succeed. The public page can be visited at the URL above.
5. In Chrome refresh the site using Ctrl+Shift+R. You should see **Applications & backups** in a full-width panel, *above* the jobs list. If the applied count disappears, use **Import JSON backup** in the same browser and choose your saved JSON file.
6. Check **Daily vacancy discovery** source health. Each provider is explicitly marked as succeeded or unavailable; an unavailable LinkedIn-indexed RSS source is not a no-jobs result.

### Optional extra LinkedIn discovery

1. At [Google Alerts](https://www.google.com/alerts), create alerts for search terms like `site:linkedin.com/jobs/view/ ("Game Producer" OR "Product Owner") (Remote OR "European Union" OR Romania)` and equivalent sound-design searches.
2. Select RSS delivery when available and copy each RSS URL.
3. In GitHub, go to **Settings > Secrets and variables > Actions > New repository secret**, name it `JOB_ALERT_RSS_URLS`, and paste each RSS URL on its own line.
4. Run the GitHub workflow again. Public RSS results may include many stale or unrelated items; only direct LinkedIn vacancy URLs matching role keywords are imported, always unverified.

The optional alert feeds do **not** log into LinkedIn, bypass restrictions, or grant this website access to your LinkedIn account. LinkedIn search buttons are still provided for manual verification.

## What still does NOT happen automatically

- No complete search of LinkedIn (the indexed feed is small, may fail, and cannot guarantee coverage).
- No automatic extraction from JavaScript-only career pages, private accounts, or protected job boards.
- No synchronization between ChatGPT's daily scheduled job report and the GitHub website.
- No synchronization of private application history across devices; the app remains browser-local.
- No guarantee a public job link is currently accepting applications.

## Technical structure

- `scripts/update_jobs.py`: 4 public ATS collectors plus parallel public-careers checks and small RSS discovery.
- `scripts/sources_extra.py`: list of 27 monitored public employer careers pages, conservative job-link/JobPosting parser, search-index RSS processing.
- `public/index.html`: responsive dashboard; saved applications in browser-local storage; multi-source status and daily feed merge.
- `public/data/jobs.json`: public feed snapshot. **Never store resumes or private applications here**.
- `.github/workflows/daily-refresh.yml`: daily collection, tests, commit, GitHub Pages deployment.

## Troubleshooting

- **No new jobs:** A successful API query might legitimately have zero matching job titles; search-index RSS is best effort and may be unavailable. Check source status on the website and workflow logs.
- **Actions fail on Git push:** Another commit occurred after the workflow started. Workflow fetches and rebases without force push. Re-run the workflow if a simultaneous edit causes an unavoidable conflict.
- **Applied jobs missing:** Application data is stored in the exact browser's localStorage, not on GitHub. Import your last JSON backup from that browser.
- **Export/import still hidden:** Hard refresh; verify that `public/index.html` from V6 was uploaded and Pages deployment was successful.
- **404 / old website:** Confirm Settings > Pages > Source = GitHub Actions. Look for a successful `deploy-pages` step.

## Validation

- Python `unittest` suite contains 10 passing unit tests for ATS parsing, role selection, public page parsing, LinkedIn-indexed RSS, and country-eligibility caveats.
- JavaScript syntax is checked with Node.js 22 (`node --check`).
- Headless Chromium visual testing was attempted but blocked by the current execution environment's browser policy; the layout has not yet been independently verified on a real desktop browser.
- Actual live ATS, RSS, and GitHub Pages deployments were not executed from this file-generation environment. Source availability must be checked in the first workflow run.
