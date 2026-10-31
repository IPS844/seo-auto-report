# SEO Auto Report

Pulls Google Search Console and GA4 data through their APIs, finds the pages and queries that need attention, and writes everything into Google Sheets. No more exporting CSVs and building the same report by hand every week.

I built the first version of this while managing SEO for a 7,000+ page website. Reporting that took hours every week now runs on its own, and that system cut our manual work by 70%. This repo is a clean, public version of that idea.

## What you get

Every run creates or refreshes these tabs in your Google Sheet:

| Tab | What it tells you |
|---|---|
| Summary | Clicks, impressions, organic sessions and key events, this period vs the previous one |
| Top Gainers | Pages that gained the most clicks, with position change |
| Top Losers | Pages that lost the most clicks, so you can catch drops early |
| Striking Distance | Queries ranking 8 to 20 with good impressions. A small push gets them to page one |
| Low CTR Pages | Top 10 pages getting far fewer clicks than their position should bring, with estimated missed clicks. Usually a title or meta description problem |
| Landing Page Value | GSC visibility joined with GA4 sessions, key events and conversion rate per page |
| Raw GSC | The full page and query data for your own analysis |

The point is simple: the report tells you what to fix next, not just what happened.

## Try it in 1 minute (no API keys needed)

```bash
git clone https://github.com/IPS844/seo-auto-report.git
cd seo-auto-report
pip install -r requirements.txt
python main.py --demo
```

This runs on sample data and saves every tab as a CSV in the `output/` folder.

## Run it on your own site

**1. Create a service account**
In Google Cloud Console, create a project, enable the **Search Console API**, **Google Analytics Data API**, **Google Sheets API** and **Google Drive API**, then create a service account and download its JSON key as `service_account.json`.

**2. Give it access**
Add the service account email as a user in Search Console, as a Viewer in your GA4 property, and as an Editor on your Google Sheet.

**3. Add your settings**

```bash
cp config.example.yaml config.yaml
```

Fill in your site URL, GA4 property ID and Sheet ID.

**4. Run**

```bash
python main.py --config config.yaml          # writes to Google Sheets
python main.py --config config.yaml --csv    # saves CSVs only
```

## Run it every week automatically

The workflow in `.github/workflows/weekly-report.yml` runs the report every Monday at 9 AM IST. Add two repository secrets:

- `GOOGLE_SERVICE_ACCOUNT_JSON`: the full content of your key file
- `REPORT_CONFIG_YAML`: the full content of your `config.yaml`

Your Sheet updates itself every week.

## How it works

```
Search Console API ─┐
                    ├─> pandas (compare periods, find opportunities) ─> Google Sheets
GA4 Data API ───────┘
```

- `seo_report/gsc.py` pulls page and query data, paging past the 25,000 row API limit
- `seo_report/ga4.py` pulls organic landing page sessions and key events
- `seo_report/insights.py` builds every insight table
- `seo_report/sheets.py` writes one tab per table
- `main.py` ties it together

Positions are impression weighted, so a page's average position reflects where it actually showed up most.

## Stack

`Python` `pandas` `Search Console API` `GA4 Data API` `Google Sheets API` `GitHub Actions`

## What's next

- AI written summary of the week using Claude, in plain English for clients
- Alerts on Slack or email when a top page drops
- Looker Studio template on top of the Sheet

## Author

**Gaurav Prakash**, AI Search and Growth. Founder of [StackFree](https://stackfree.io).
[LinkedIn](https://www.linkedin.com/in/prak-gaur123456/) | [GitHub](https://github.com/IPS844)
