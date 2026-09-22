"""Download NIFTY 50 daily OHLC from NIFTY Indices (NSE Indices Ltd) and save it unmodified.

The website's UI limits a query to 1 year, but that check is client-side only; the
backend endpoint the page itself calls returns the full range in one request.

Usage:  python src/fetch_data.py [START dd-Mon-yyyy] [END dd-Mon-yyyy]
Output: data/raw/nifty50_niftyindices_raw.csv  (fields exactly as returned, no cleaning)
"""

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests

PAGE_URL = "https://www.niftyindices.com/reports/historical-data"
API_URL = "https://www.niftyindices.com/BackPage/getHistoricaldatatabletoString"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Safari/537.36"
)
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "nifty50_niftyindices_raw.csv"


def fetch(start: str, end: str, index_name: str = "NIFTY 50") -> pd.DataFrame:
    session = requests.Session()
    session.get(PAGE_URL, headers={"User-Agent": USER_AGENT}, timeout=30)  # obtain session cookies
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "https://www.niftyindices.com",
        "Referer": PAGE_URL,
        "X-Requested-With": "XMLHttpRequest",
    }
    # Payload format copied from the site's own JS (IISLComponet.js -> HistoricalData)
    cinfo = f"{{'name':'{index_name}','startDate':'{start}','endDate':'{end}','indexName':'{index_name}'}}"
    resp = session.post(API_URL, headers=headers, data=json.dumps({"cinfo": cinfo}), timeout=120)
    resp.raise_for_status()
    return pd.DataFrame(json.loads(resp.text))


def main() -> None:
    start = sys.argv[1] if len(sys.argv) > 1 else "01-Jan-2000"
    end = sys.argv[2] if len(sys.argv) > 2 else date.today().strftime("%d-%b-%Y")
    df = fetch(start, end)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(df)} rows ({start} -> {end}) to {OUT_PATH}")


if __name__ == "__main__":
    main()
