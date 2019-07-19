"""
Calculate pnl and cash flow metrics.

James Schmitz
3/25/2017
"""
from collections import deque
import pandas as pd


def one_trader_pnl(trades):
    """calculate pnl and cash flow metrics

    trades is a df with data on one contract for one trader
    """
    # make sure it is sorted
    trades.sort_values('date_executed', inplace=True)

    # cash flow calculations
    trades['notional'] = trades['price_per_share'] * trades['quantity']
    trades['buy_sell'] = trades['trade_type'].str.startswith('Buy').apply(
        lambda b: 1 if b else -1)
    trades['cash_flow'] = -trades['buy_sell'] * trades['notional']

    # calculate pnl of each trade and fees. assume that shares are sold in the
    # same order they are purchased, ie, FIFO. also assume that a trader that
    # is long Yes contracts can't buy No contracts until they liquidate all of
    # their Yes contracts.
    positions = deque()
    pnls = []
    fees = []
    yes_no = []
    for trade in trades.itertuples():
        if trade.buy_sell == 1:
            positions.extend([trade.price_per_share] * trade.quantity)
            # no pnl or fee when opening position
            pnls.append(0)
            fees.append(0)
        elif trade.buy_sell == -1:
            # calc pnl and fee assuming oldest share traded first
            pnl = 0.0
            fee = 0
            for _ in range(trade.quantity):
                buy_price = positions.popleft()
                if buy_price < trade.price_per_share:
                    fee += 0.1 * (trade.price_per_share - buy_price)
                pnl += trade.price_per_share - buy_price
            pnls.append(pnl)
            fees.append(fee)
        if trade.trade_type in ['Buy Yes', 'Sell Yes']:
            yes_no.append('Yes')
        elif trade.trade_type in ['Buy No', 'Sell No']:
            yes_no.append('No')
        else:  # Close trade (sell back to exchange)
            yes_no.append(yes_no[-1])

    trades['yes_no'] = yes_no
    trades['gross_pnl'] = pnls
    trades['fee'] = fees

    trades['pnl_net_fee'] = trades['gross_pnl'] - trades['fee']
    trades['close_trade'] = trades['trade_type'] == 'Close'

    return trades


def trader_analysis(orders, trades):
    trader_analysis = trades.groupby(
        ['contract_id', 'user_guid']).apply(one_trader_pnl)
    trader_analysis.index = pd.MultiIndex(
        levels=trader_analysis.index.levels[:2],
        labels=trader_analysis.index.labels[:2],
        names=trader_analysis.index.names[:2])

    trader_analysis = take_provide_analysis(orders, trader_analysis)

    return trader_analysis


def take_provide_analysis(orders, trades):
    order_created_lut = orders.set_index('order_id')['date_created'].to_dict()

    def determine_take_provide(r):
        order_time = order_created_lut.get(r['placed_order_id'])
        other_order_time = order_created_lut.get(r['matched_order_id'])

        if order_time and other_order_time:
            if order_time < other_order_time:
                return 'P'
            else:
                return 'T'
        else:
            return 'C'

    trades['take_provide'] = trades.apply(determine_take_provide, axis=1)

    return trades
