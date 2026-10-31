"""Write report tables into Google Sheets, one tab per table."""

import gspread
import pandas as pd

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def open_sheet(key_file, spreadsheet_id):
    gc = gspread.service_account(filename=key_file, scopes=SCOPES)
    return gc.open_by_key(spreadsheet_id)


def _clean(df):
    df = df.copy()
    for c in df.select_dtypes(include="float").columns:
        df[c] = df[c].round(3)
    return df.astype(object).where(pd.notna(df), "")


def write_tab(sheet, title, df):
    try:
        ws = sheet.worksheet(title)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=title, rows=max(len(df) + 10, 100), cols=max(len(df.columns), 10))
    data = _clean(df)
    ws.update([data.columns.tolist()] + data.values.tolist(), value_input_option="USER_ENTERED")
    ws.freeze(rows=1)


def write_all(sheet, tables):
    for title, df in tables.items():
        write_tab(sheet, title, df)
