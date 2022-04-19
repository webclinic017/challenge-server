from datetime import date
import os

import click
import pandas as pd
import requests
from tqdm import tqdm


class Client:
    def __init__(self):
        self.headers = {"Authorization": os.getenv("DATA_SECRET_KEY")}

    def get_daily_factor(self, path, ticker, start_date, end_date):
        response = requests.get(
            f"http://localhost:8000/daily/factor/{path}",
            headers=self.headers,
            params={
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        response_json = response.json()
        error = response_json["error"]
        data = response_json["data"]
        if data is None:
            return None, error
        dfm = pd.DataFrame.from_dict(data)
        dfm = dfm.set_index(["Date", "Stem"])
        return dfm, error

    def get_daily_ohlcv(self, ric, start_date, end_date):
        response = requests.get(
            f"http://localhost:8000/daily/ohlcv",
            headers=self.headers,
            params={
                "ric": ric,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        response_json = response.json()
        error = response_json["error"]
        data = response_json["data"]
        if data is None:
            return None, error
        dfm = pd.DataFrame.from_dict(data)
        dfm = dfm.set_index(["Date", "RIC"])
        return dfm, error

    def get_expiry_calendar(self, ticker, start_date, end_date):
        response = requests.get(
            f"http://localhost:8000/expiry-calendar",
            headers=self.headers,
            params={
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        response_json = response.json()
        error = response_json["error"]
        data = response_json["data"]
        if data is None:
            return None, error
        dfm = pd.DataFrame.from_dict(data)
        return dfm, error

    def get_tickers(self):
        response = requests.get(f"http://localhost:8000/tickers", headers=self.headers)
        response_json = response.json()
        data = response_json.get("data", [])
        error = response_json["error"]
        return data, error


@click.command()
@click.option("--from-ticker", default="", required=False)
@click.option("--to-ticker", default="", required=False)
@click.option("--with-expiry", default=False, required=False)
def main(from_ticker, to_ticker, with_expiry):
    client = Client()
    start_date = "1990-01-01"
    end_date = "2022-02-28"
    tickers, _ = client.get_tickers()
    for ticker, future in tqdm(tickers.items()):
        if (from_ticker != "" and ticker < from_ticker) or (
            to_ticker != "" and ticker > to_ticker
        ):
            continue
        if "Stem" not in future:
            continue
        carry_factor = future.get("CarryFactor", {})
        group = future.get("Group")
        if with_expiry:
            dfm, _ = client.get_expiry_calendar(
                ticker, start_date="1990-01-01", end_date=date.today().isoformat()
            )
            path = os.path.join(
                os.getenv("HOME"), "Downloads", f"{ticker}.download.csv"
            )
            dfm.to_csv(path, index=False)
        else:
            if group == "Commodities":
                dfm, _ = client.get_daily_factor(
                    "carry/commodity", ticker, start_date, end_date
                )
                print(dfm)
            if group == "Currencies":
                if "LocalInterestRate" in carry_factor:
                    dfm, _ = client.get_daily_factor(
                        "carry/currency", ticker, start_date, end_date
                    )
                    print(dfm)
            if group == "Equities":
                if "ExpectedDividend" in carry_factor:
                    dfm, _ = client.get_daily_factor(
                        "carry/equity", ticker, start_date, end_date
                    )
                    print(dfm)
            if group == "Rates":
                if "GovernmentInterestRate5Y" in carry_factor:
                    dfm, _ = client.get_daily_factor(
                        "carry/bond", ticker, start_date, end_date
                    )
                    print(dfm)
            if "COT" in future:
                dfm, _ = client.get_daily_factor("cot", ticker, start_date, end_date)
                print(dfm)
            if "CurrencyFactor" in future:
                dfm, _ = client.get_daily_factor(
                    "currency", ticker, start_date, end_date
                )
                print(dfm)
            dfm, _ = client.get_daily_factor(
                "roll-return", ticker, start_date, end_date
            )
            print(dfm)
            dfm, _ = client.get_daily_factor("nav/long", ticker, start_date, end_date)
            print(dfm)
            dfm, _ = client.get_daily_factor("nav/short", ticker, start_date, end_date)
            print(dfm)
            stem = future["Stem"]["Reuters"]
            ric = f"{stem}c1"
            dfm, _ = client.get_daily_ohlcv(ric, start_date, end_date)
            print(dfm)
            dfm, _ = client.get_daily_factor("splits", ticker, start_date, end_date)
            print(dfm)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
