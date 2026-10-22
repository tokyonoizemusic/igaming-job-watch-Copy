# European iGaming Job Watch — Daily Live

A ready-to-publish GitHub Pages site based on the existing V3 dashboard.

**Status:** This is a deployment package, **not yet a published website**. The published URL will be `https://YOUR-GITHUB-USERNAME.github.io/YOUR-REPO-NAME/` after deployment.

## What updates automatically?

A scheduled GitHub Action runs **daily at 08:13 Europe/Bucharest** and fetches published vacancies from several employer recruiting systems. Its snapshot is saved to `public/data/jobs.json`, then the static site is republished to GitHub Pages. Jobs are filtered to production/product and audio positions, with iGaming employers favored.

Currently configured automatic sources:

- Oddin.gg — Lever public job board API
- Betsson Group — Greenhouse public job board API
- Playtech — SmartRecruiters public Posting API
- Enjoy Gaming — Recruitee careers API (may require authentication in future; a failed source is shown clearly)

Each provider may reject access, change systems or return no matches. The site displays failures instead of claiming that no jobs exist. This **does not continuously scrape all European sites**, and it **does not automatically ingest LinkedIn jobs**. The broader LinkedIn/Google/job-board searches from V3 remain available as outbound live search links.

This website updater is **separate from your ChatGPT Daily European iGaming Job Watch**. That ChatGPT task searches more broadly and sends you a report, but it does not write results to your GitHub repository automatically.

## Publish on GitHub Pages

1. Create a **new public repository** on GitHub, for example `igaming-job-watch`.
2. Upload all contents of this ZIP to the repository root, preserving `.github/workflows/daily-refresh.yml`, `scripts/`, and `public/`.
   - Easiest local method: unzip, then use GitHub Desktop or `git` to upload the entire directory (GitHub web upload sometimes hides dotfolders).
3. Under repository **Settings → Actions → General → Workflow permissions**, allow **Read and write permissions** for workflows. The updater commits its snapshot to your repository.
4. Under **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions**.
5. Open **Actions → Daily iGaming jobs refresh & publish → Run workflow** once for the initial collection and deployment.
6. Once the workflow succeeds, find your public address under **Settings → Pages**. It will generally look like `https://YOUR-GITHUB-USERNAME.github.io/igaming-job-watch/`.

The daily workflow is also triggered by edits to the website and code. It does not require an API key for the configured public endpoints. If a source later requires authentication, that source is marked as unavailable; do not add someone else's private API token.

**Important:** GitHub scheduling can be delayed or skipped under load, and public repositories can have schedules disabled after prolonged inactivity. Use the **Run workflow** button to recover or force a refresh. See repository Actions logs if the feed shows failures.

## Working locally

Opening `public/index.html` directly in Chrome shows your existing curated leads and search links, but the automatic feed may fail due to local `file://` restrictions. To test the full site locally:

```bash
cd public
python -m http.server 8000
# open http://localhost:8000/ in Chrome
```

To manually update the feed from your terminal (network required):

```bash
python scripts/update_jobs.py
```

The website's **Refresh list** button reloads the latest JSON already published to GitHub Pages; it does **not** trigger new employer searches on demand. New employer searches happen when the daily GitHub Action runs or when you manually select **Run workflow** on GitHub.

## Your data and privacy

- Saved jobs, status, bookmarks and notes stay in **your own Chrome local storage**. They do not sync between devices or upload to the site.
- Keep exporting JSON backups; you can import your V3 backup into this version.
- **Never put your CV, phone number, passwords, or personal application notes into `public/`**. GitHub Pages is public.
- “Remote” or “Europe” is not automatic proof of eligibility to work from Romania. Confirm with the employer.
- A returned ATS posting means it is present on the published board at feed-check time, not that the employer will accept your application.

## Repository structure

```
public/index.html                 The existing V3 dashboard with daily-feed enhancements
public/data/jobs.json            Daily snapshot (generated automatically)
scripts/update_jobs.py           Job source collectors
scripts/test_update_jobs.py      Simple source parser tests
.github/workflows/daily-refresh.yml   Daily updater + GitHub Pages deployment
```

## Extend automatic sources

Add a valid employer token in `SOURCES` in `scripts/update_jobs.py` for a supported ATS, then push the change. API-supported sources only; do not scrape private, authenticated, or forbidden listings. APIs can change without notice.
