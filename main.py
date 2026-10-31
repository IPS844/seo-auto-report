"""SEO Auto Report: GSC + GA4 data straight into Google Sheets, with insights.

Usage:
    python main.py --demo                 # sample data, saves CSVs to output/
    python main.py --config config.yaml   # live data, writes to Google Sheets
    python main.py --config config.yaml --csv   # live data, CSVs only
"""

import argparse
from datetime import date, timedelta
from pathlib import Path

import yaml

from seo_report import insights


def date_windows(days, lag=3):
    """Current and previous periods of equal length. GSC data lags about 3 days."""
    end = date.today() - timedelta(days=lag)
    start = end - timedelta(days=days - 1)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    return (str(start), str(end)), (str(prev_start), str(prev_end))


def load_live(cfg):
    from seo_report import ga4, gsc

    (start, end), (p_start, p_end) = date_windows(cfg.get("days", 28))
    print(f"Current period:  {start} to {end}")
    print(f"Previous period: {p_start} to {p_end}")

    key = cfg["service_account_file"]
    service = gsc.get_service(key)
    current = gsc.fetch(service, cfg["gsc_site_url"], start, end)
    previous = gsc.fetch(service, cfg["gsc_site_url"], p_start, p_end)

    client = ga4.get_client(key)
    ga = ga4.fetch_organic_landing_pages(client, cfg["ga4_property_id"], start, end)
    return current, previous, ga


def load_demo():
    from seo_report import sample_data
    return sample_data.gsc_current(), sample_data.gsc_previous(), sample_data.ga4()


def build_tables(current, previous, ga, cfg):
    gainers, losers = insights.compare_periods(current, previous, cfg.get("top_n", 20))
    return {
        "Summary": insights.summary(current, previous, ga),
        "Top Gainers": gainers,
        "Top Losers": losers,
        "Striking Distance": insights.striking_distance(
            current, cfg.get("striking_min_impressions", 100)),
        "Low CTR Pages": insights.low_ctr_pages(
            current, cfg.get("low_ctr_min_impressions", 500)),
        "Landing Page Value": insights.landing_page_value(current, ga),
        "Raw GSC": current,
    }


def save_csv(tables, out_dir="output"):
    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    for name, df in tables.items():
        df.to_csv(out / f"{name.lower().replace(' ', '_')}.csv", index=False)
    print(f"Saved {len(tables)} CSV files to {out}/")


def main():
    parser = argparse.ArgumentParser(description="SEO Auto Report")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--demo", action="store_true", help="run on sample data")
    parser.add_argument("--csv", action="store_true", help="save CSVs instead of Sheets")
    args = parser.parse_args()

    if args.demo:
        cfg = {}
        current, previous, ga = load_demo()
    else:
        cfg = yaml.safe_load(Path(args.config).read_text())
        current, previous, ga = load_live(cfg)

    tables = build_tables(current, previous, ga, cfg)
    print(tables["Summary"].to_string(index=False))

    if args.demo or args.csv:
        save_csv(tables)
    else:
        from seo_report import sheets
        sheet = sheets.open_sheet(cfg["service_account_file"], cfg["spreadsheet_id"])
        sheets.write_all(sheet, tables)
        print(f"Report written to https://docs.google.com/spreadsheets/d/{cfg['spreadsheet_id']}")


if __name__ == "__main__":
    main()
