"""Pull organic landing page data from GA4."""

import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def get_client(key_file):
    creds = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)
    return BetaAnalyticsDataClient(credentials=creds)


def fetch_organic_landing_pages(client, property_id, start_date, end_date):
    """Sessions, engaged sessions and key events per landing page, organic search only."""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="landingPage")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="keyEvents"),
        ],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="sessionDefaultChannelGroup",
                string_filter=Filter.StringFilter(value="Organic Search"),
            )
        ),
        limit=100000,
    )
    resp = client.run_report(request)

    records = []
    for row in resp.rows:
        records.append(
            {
                "landing_page": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "engaged_sessions": int(row.metric_values[1].value),
                "key_events": float(row.metric_values[2].value),
            }
        )
    return pd.DataFrame(
        records, columns=["landing_page", "sessions", "engaged_sessions", "key_events"]
    )
