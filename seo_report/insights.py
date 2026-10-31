"""Turn raw GSC and GA4 data into tables a marketer can act on."""

from urllib.parse import urlparse

import numpy as np
import pandas as pd

# Rough organic CTR by rounded position, used to spot titles that underperform.
EXPECTED_CTR = {1: 0.28, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05,
                6: 0.04, 7: 0.03, 8: 0.025, 9: 0.02, 10: 0.018}


def _weighted_position(df, key):
    tmp = df.assign(pos_x_imp=df["position"] * df["impressions"])
    g = tmp.groupby(key, as_index=False).agg(
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        pos_x_imp=("pos_x_imp", "sum"),
    )
    g["ctr"] = np.where(g["impressions"] > 0, g["clicks"] / g["impressions"], 0)
    g["position"] = np.where(g["impressions"] > 0, g["pos_x_imp"] / g["impressions"], 0)
    return g.drop(columns="pos_x_imp")


def page_summary(gsc_df):
    return _weighted_position(gsc_df, "page")


def compare_periods(current, previous, top_n=20):
    """Pages that gained or lost the most clicks against the previous period."""
    cur, prev = page_summary(current), page_summary(previous)
    merged = cur.merge(prev, on="page", how="outer", suffixes=("", "_prev")).fillna(0)
    merged["click_change"] = merged["clicks"] - merged["clicks_prev"]
    merged["position_change"] = merged["position_prev"] - merged["position"]
    cols = ["page", "clicks", "clicks_prev", "click_change",
            "position", "position_prev", "position_change"]
    gainers = merged.sort_values("click_change", ascending=False).head(top_n)[cols]
    losers = merged.sort_values("click_change").head(top_n)[cols]
    return gainers, losers


def striking_distance(gsc_df, min_impressions=100, top_n=50):
    """Queries sitting on positions 8 to 20: a small push gets them to page one."""
    q = _weighted_position(gsc_df, ["page", "query"])
    q = q[(q["position"] >= 8) & (q["position"] <= 20) & (q["impressions"] >= min_impressions)]
    return q.sort_values("impressions", ascending=False).head(top_n)


def low_ctr_pages(gsc_df, min_impressions=500, top_n=30):
    """Top 10 pages getting far fewer clicks than their position should bring."""
    p = page_summary(gsc_df)
    p = p[(p["position"] <= 10) & (p["impressions"] >= min_impressions)].copy()
    p["expected_ctr"] = p["position"].round().clip(1, 10).map(EXPECTED_CTR)
    p["missed_clicks"] = ((p["expected_ctr"] - p["ctr"]) * p["impressions"]).round()
    p = p[p["ctr"] < p["expected_ctr"] * 0.6]
    return p.sort_values("missed_clicks", ascending=False).head(top_n)


def landing_page_value(gsc_df, ga4_df):
    """Join search visibility with what visitors actually did on the page."""
    p = page_summary(gsc_df)
    p["path"] = p["page"].map(lambda u: urlparse(u).path or "/")
    g = ga4_df.rename(columns={"landing_page": "path"})
    merged = p.merge(g, on="path", how="left").fillna(
        {"sessions": 0, "engaged_sessions": 0, "key_events": 0})
    merged["conv_rate"] = np.where(
        merged["sessions"] > 0, merged["key_events"] / merged["sessions"], 0)
    return merged.sort_values("key_events", ascending=False)


def summary(current, previous, ga4_df):
    cur, prev = page_summary(current), page_summary(previous)

    def pct(a, b):
        return round((a - b) / b * 100, 1) if b else None

    clicks, clicks_prev = cur["clicks"].sum(), prev["clicks"].sum()
    imps, imps_prev = cur["impressions"].sum(), prev["impressions"].sum()
    rows = [
        ("Clicks", int(clicks), int(clicks_prev), pct(clicks, clicks_prev)),
        ("Impressions", int(imps), int(imps_prev), pct(imps, imps_prev)),
        ("Pages with clicks", int((cur["clicks"] > 0).sum()),
         int((prev["clicks"] > 0).sum()), None),
        ("Organic sessions (GA4)", int(ga4_df["sessions"].sum()), None, None),
        ("Organic key events (GA4)", float(ga4_df["key_events"].sum()), None, None),
    ]
    return pd.DataFrame(rows, columns=["metric", "this_period", "previous_period", "change_pct"])
