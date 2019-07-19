import numpy as np
import pandas as pd
idx = pd.IndexSlice


def calculate_trader_efficiency(trader_analysis,
                                trader_analysis3_yes,
                                trader_analysis3_no,
                                replication_share_qty_cutoff):
    """ Calculate individual trader trading efficiency """
    # first modify the replication values if the number of contracts that
    # would need to be purchased is above the cutoff. this is only relevant
    # for No contracts.
    def get_max_value(d_dict):
        try:
            d_dict = eval(d_dict)
            d_dict.pop('contracts')
            return max(d_dict.values())
        except Exception as e:
            return np.nan

    indx = (
        trader_analysis3_no[('replication', 'd')].apply(get_max_value) >
        replication_share_qty_cutoff
    )
    trader_analysis3_no.loc[indx, ('replication', 'max_loss')] = np.nan

    trader_analysis_buy_yes = (
        trader_analysis3_yes.loc[idx[:, '_trades']].copy()
    )
    trader_analysis_buy_yes['replicating_price'] = (
        trader_analysis3_yes.loc[idx[:, ('replication', 'max_loss')]]
    )

    trader_analysis_buy_no = trader_analysis3_no.loc[idx[:, '_trades']].copy()
    trader_analysis_buy_no['replicating_price'] = (
        trader_analysis3_no.loc[idx[:, ('replication', 'max_loss')]]
    )

    trader_analysis_sell_and_close = (
        trader_analysis.query("trade_type in ('Sell Yes', 'Sell No', 'Close')")
    )

    trader_analysis2 = pd.concat(
        [trader_analysis_buy_yes,
         trader_analysis_buy_no,
         trader_analysis_sell_and_close]).sort_index()

    # all buy trades
    all_buy_trades = (
        trader_analysis2.query("trade_type in ('Buy Yes', 'Buy No')")
    )

    # all buy volume by trader
    all_buys = all_buy_trades.groupby('user_guid')['quantity'].sum()

    # inefficient buy volume by trader
    # note some trades don't have a replicating price. they need to be labeled
    # as efficient trades
    inefficient_buys = (
        all_buy_trades.query("price_per_share > replicating_price")
        .groupby('user_guid')['quantity'].sum().loc[all_buys.index].fillna(0)
    )

    # this is % of a trader's trading volume that was traded efficiently, ie
    # with the dominant contract
    trader_trading_efficiency = 1 - inefficient_buys / all_buys

    return trader_trading_efficiency
