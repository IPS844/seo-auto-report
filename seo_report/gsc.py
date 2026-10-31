"""Pull Search Console performance data into a DataFrame."""

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
ROW_LIMIT = 25000


def get_service(key_file):
    creds = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def fetch(service, site_url, start_date, end_date, dimensions=("page", "query")):
    """Return every row for the date range, paging past the 25k API limit."""
    rows, start_row = [], 0
    while True:
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": list(dimensions),
            "rowLimit": ROW_LIMIT,
            "startRow": start_row,
        }
        resp = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
        batch = resp.get("rows", [])
        rows.extend(batch)
        if len(batch) < ROW_LIMIT:
            break
        start_row += ROW_LIMIT

    records = []
    for r in rows:
        rec = dict(zip(dimensions, r["keys"]))
        rec.update(
            clicks=r["clicks"],
            impressions=r["impressions"],
            ctr=r["ctr"],
            position=r["position"],
        )
        records.append(rec)

    cols = list(dimensions) + ["clicks", "impressions", "ctr", "position"]
    return pd.DataFrame(records, columns=cols)
