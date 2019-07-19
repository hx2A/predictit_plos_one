"""
Behavior metrics

James Schmitz
8/18/2017
"""
from collections import defaultdict

from pandas import Series


def _one_trader_behavior_measurements(trades, contract_ids):
    """ calculate behavior metrics for one trader
    """
    # make sure it is sorted
    trades.sort_values('date_executed', inplace=True)

    positions = defaultdict(int)         # key: y/n, contract id
    price_histories = defaultdict(list)  # key: y/n, contract id
    opened_positions = defaultdict(int)  # key: contract id

    max_loss = 0.0
    pnl = 0.0
    max_in_pool = 0.0

    for trade in trades.itertuples():
        if not positions[(trade.yes_no, trade.contract_id)]:
            # opening a new position in this contract
            opened_positions[trade.contract_id] += 1

        positions[(trade.yes_no, trade.contract_id)] += (trade.buy_sell *
                                                         trade.quantity)

        # update price histories
        if trade.buy_sell == 1:
            price_histories[(trade.yes_no, trade.contract_id)].extend(
                [trade.price_per_share] * trade.quantity)
        elif trade.buy_sell == -1:
            # first calculate the net pnl
            oldest_shares = (
                price_histories[
                    (trade.yes_no, trade.contract_id)][:trade.quantity]
            )
            for buy_price in oldest_shares:
                if buy_price < trade.price_per_share:
                    # sold at a profit, pay a fee
                    pnl += 0.9 * (trade.price_per_share - buy_price)
                else:
                    # sold at a loss
                    pnl -= buy_price - trade.price_per_share

            price_histories[(trade.yes_no, trade.contract_id)] = (
                price_histories[
                    (trade.yes_no, trade.contract_id)][trade.quantity:]
            )

        # max loss
        for c_id in contract_ids:
            # calculate loss if contract id c_id settles is the winning
            # contract
            loss = (sum(price_histories[('No', c_id)]) +
                    sum([sum(price_histories[('Yes', c)])
                         for c in contract_ids if c != c_id]))
            max_loss = max(max_loss, loss)
            max_in_pool = max(max_in_pool, loss - pnl)

    out = Series()
    out['yes_unique_contract_count'] = len(
        trades.query("yes_no == 'Yes'")['contract_id'].unique())
    out['no_unique_contract_count'] = len(
        trades.query("yes_no == 'No'")['contract_id'].unique())

    out['max_loss'] = max_loss
    out['max_opened_pos'] = max(opened_positions.values())
    out['pnl'] = pnl
    out['max_in_pool'] = max_in_pool

    return out


def behavior_analysis(trader_analysis, trader_efficiency):
    # calculate behavior analysis from trader analysis data
    behavior_analysis = trader_analysis.groupby(['user_guid']).apply(
        _one_trader_behavior_measurements,
        contract_ids=trader_analysis.contract_id.unique()).fillna(0)

    behavior_analysis['yes_only'] = behavior_analysis[
        'no_unique_contract_count'] == 0
    behavior_analysis['no_only'] = behavior_analysis[
        'yes_unique_contract_count'] == 0
    behavior_analysis['yes_and_no'] = (
        (behavior_analysis['no_unique_contract_count'] > 0) &
        (behavior_analysis['yes_unique_contract_count'] > 0))

    behavior_analysis['efficiency'] = trader_efficiency

    return behavior_analysis


# Utility functions for analyzing specific traders


def stats_by_trader(orders, trader_analysis):
    df = orders.groupby(
        'user_guid')['order_id'].count().to_frame('orders_sent')
    df2 = trader_analysis.groupby(['user_guid'])[
        ['quantity', 'notional', 'gross_pnl', 'fee', 'pnl_net_fee']].sum()

    trader_summary = df.merge(df2, left_index=True, right_index=True)
    trader_summary.sort_values('pnl_net_fee', ascending=False, inplace=True)

    return trader_summary


def orders_for_user_guid(orders, user_guid, contract_id=None):
    query = "user_guid == '{0}'".format(user_guid)

    result = orders.query(query).copy()

    if contract_id:
        query = "contract_id == {0}".format(contract_id)

        result = result.query(query).copy()

    result.sort_values('date_created', inplace=True)

    return result


def trades_for_user_guid(trader_analysis, user_guid, contract_id=None):
    query = "user_guid == '{0}'".format(user_guid)

    result = trader_analysis.query(query).copy()

    if contract_id:
        query = "contract_id == {0}".format(contract_id)

        result = result.query(query).copy()

    result.reset_index(drop=True, inplace=True)
    result.drop(
        'user_guid market_id placed_order_id matched_order_id yes_no close_trade'.split(),
        axis=1, inplace=True)
    result.sort_values('date_executed', inplace=True)

    return result
