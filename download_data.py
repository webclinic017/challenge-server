import os
import requests

import click
import pandas as pd
from tqdm import tqdm



class Client():
    def __init__(self):
        self.headers={
            'Authorization': os.getenv('DATA_SECRET_KEY')
        }
    
    def get_daily(self, path, ticker, start_date, end_date):
        response = requests.get(
            f'http://localhost:8000/daily/{path}',
            headers=self.headers,
            params={
                'ticker': ticker,
                'start_date': start_date,
                'end_date': end_date,
            })
        response_json = response.json()
        error = response_json['error']
        if error is not None:
            print(error)
        data = response_json['data']
        if data is None:
            return
        dfm = pd.DataFrame.from_dict(data)
        dfm = dfm.set_index(['Date', 'Stem'])
        return dfm
    
    def get_tickers(self):
        response = requests.get(
            f'http://localhost:8000/tickers',
            headers=self.headers)
        data = response.json().get('data', [])
        return data


@click.command()
@click.option('--from-ticker', default='', required=False)
@click.option('--to-ticker', default='', required=False)
def main(from_ticker, to_ticker):
    client = Client()
    start_date = '1990-01-01'
    end_date = '2022-02-28'
    for ticker, future in tqdm(client.get_tickers().items()):
        if ticker < from_ticker or ticker > to_ticker:
            continue
        if 'Stem' not in future:
            continue
        carry_factor = future.get('CarryFactor', {})
        group = future.get('Group')
        if group == 'Rates':
            if 'GovernmentInterestRate5Y' in carry_factor:
                dfm = client.get_daily('factor/carry/bond', ticker, start_date, end_date)
        if group == 'Commodities':
            dfm = client.get_daily('factor/carry/commodity', ticker, start_date, end_date)
        if group == 'Currencies':    
            if 'LocalInterestRate' in carry_factor:
                dfm = client.get_daily('factor/carry/currency', ticker, start_date, end_date)
        if group == 'Equities':    
            if 'ExpectedDividend' in carry_factor:
                dfm = client.get_daily('factor/carry/equity', ticker, start_date, end_date)
        if 'COT' in future:
            dfm = client.get_daily('factor/cot', ticker, start_date, end_date) 
        if 'CurrencyFactor' in future:
            dfm = client.get_daily('factor/currency', ticker, start_date, end_date)  
        dfm = client.get_daily('factor/roll-return', ticker, start_date, end_date)
        # dfm = client.get_daily('nav/long', ticker, start_date, end_date)
        # dfm = client.get_daily('nav/short', ticker, start_date, end_date)
        dfm = client.get_daily('ohlcv', ticker, start_date, end_date)
        dfm = client.get_daily('splits', ticker, start_date, end_date)

    print(dfm)


if __name__ == '__main__':
    main()
    # TODO: BTC
