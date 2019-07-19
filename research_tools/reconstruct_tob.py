"""
Reconstruct TOB data from the trades

Useful for markets where the TOB cannot be derived from the order messages

James Schmitz
4/29/2017
"""
import pandas as pd


def generate_quotes_one_contract(contract_trades):
    contract_trades = contract_trades.sort_values('seq')

    provide_bids = contract_trades.query(
        ("(trade_type == 'Buy Yes' or trade_type == 'Sell No')"
         " and take_provide == 'P'"))
    provide_bids = provide_bids[['seq', 'corrected_price']]
    provide_bids.set_index('seq', inplace=True)
    provide_bids.columns = ['provide_bid']

    provide_asks = contract_trades.query(
        ("(trade_type == 'Sell Yes' or trade_type == 'Buy No')"
         " and take_provide == 'P'"))
    provide_asks = provide_asks[['seq', 'corrected_price']]
    provide_asks.set_index('seq', inplace=True)
    provide_asks.columns = ['provide_ask']

    quotes = pd.concat([provide_bids, provide_asks]).sort_index()
    quotes.index.name = None
    quotes = quotes[['provide_bid', 'provide_ask']]

    quotes['timestamp'] = pd.to_datetime(
        quotes.index * 1e6).tz_localize('UTC').tz_convert('US/Eastern')

    quotes['provide_bid_ff'] = quotes['provide_bid'].ffill().bfill()
    quotes['provide_ask_ff'] = quotes['provide_ask'].ffill().bfill()

    quotes['provide_bid_p1'] = quotes['provide_bid'] + 0.01
    quotes['provide_ask_m1'] = quotes['provide_ask'] - 0.01

    quotes['bid_price'] = quotes[
        ['provide_bid_ff', 'provide_ask_m1']].min(axis=1)
    quotes['ask_price'] = quotes[
        ['provide_ask_ff', 'provide_bid_p1']].max(axis=1)

    # return quotes
    return quotes[['timestamp', 'bid_price', 'ask_price']].round(2)


def generate_quotes(trades):
    contract_ids = trades['contract_id'].unique()

    quotes = {}
    for c_id in contract_ids:
        quotes[c_id] = generate_quotes_one_contract(
            trades.query('contract_id == @c_id'))

    return quotes
