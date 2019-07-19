import numpy as np
import pandas as pd
from itertools import repeat
from operator import mul
from functools import reduce

idx = pd.IndexSlice

###############################################################################
# Yes Contracts: No Spreads or Fees
###############################################################################


def calculate_yes_contracts_no_spreads_or_fees(trader_analysis, contract_ids):
    """ Yes contracts but without spreads or fees """
    # function for calculating the price of the replicating set of contracts
    # for one trade (row)
    def replicate_yes_contract_no_spreads_no_fees(row):
        contract_id = row[('_trades', 'contract_id')]

        # use the midquote at the time of the trade
        Y_a = row[idx['contract_' + str(contract_id)]].mean()
        # sum of midquotes of contracts other than the one that traded
        sum_Y_i = sum([row[idx['contract_' + str(c_id)]].mean()
                       for c_id in contract_ids
                       if c_id != contract_id])

        c = (1 - Y_a) / sum_Y_i

        return c

    trader_analysis1_yes = (
        trader_analysis[trader_analysis.loc[
            idx[:, ('_trades', 'trade_type')]] == 'Buy Yes'
        ].copy()
    )

    trader_analysis1_yes.loc[:, ('replication', 'c')] = (
        trader_analysis1_yes.apply(
            replicate_yes_contract_no_spreads_no_fees, axis=1)
    )

    # function for checking the replicating contract. does it meet assumptions?
    # also calculates the max loss
    def check_replicate_yes_contract_no_spreads_no_fees(row):

        contract_id = row[('_trades', 'contract_id')]
        c = row[('replication', 'c')]
        target_pnl = 1 - row[idx['contract_' + str(contract_id)]].mean()
        losses = []

        if np.isnan(c):
            return np.nan

        for c_id_win in contract_ids:
            pnl = 0
            for c_id in contract_ids:
                if c_id == contract_id:
                    # bought zero No contracts for this one
                    continue
                else:
                    if np.isnan(row[idx['contract_' + str(c_id)]].mean()):
                        # if this is nan we don't have quote data for it. must
                        # be before trading started on this contract
                        continue
                    if c_id == c_id_win:
                        # bought c No contracts, lost money
                        pnl -= (
                            c * (1 - row[idx['contract_' + str(c_id)]].mean())
                        )
                    else:
                        # bought c No contracts, made money
                        pnl += c * row[idx['contract_' + str(c_id)]].mean()

            if c_id_win == contract_id:
                # upside must be the same
                assert abs(target_pnl - pnl) < 1e-7
            else:
                losses.append(pnl)

        # min and max losses should be the same
        assert abs(min(losses) - max(losses)) < 1e-7

        return -max(losses)

    trader_analysis1_yes.loc[:, ('replication', 'max_loss')] = (
        trader_analysis1_yes.apply(
            check_replicate_yes_contract_no_spreads_no_fees, axis=1)
    )

    # add midquote at time of trade since we need that for the plots
    def midquote_at_time_of_trade(row):
        contract_id = row[('_trades', 'contract_id')]
        return row[idx['contract_' + str(contract_id)]].mean()

    trader_analysis1_yes.loc[:, ('replication', 'Y_a')] = (
        trader_analysis1_yes.apply(midquote_at_time_of_trade, axis=1)
    )

    return trader_analysis1_yes


###############################################################################
# No Contracts: No Spreads or Fees
###############################################################################


def calculate_no_contracts_no_spreads_or_fees(trader_analysis, contract_ids):
    """ No contracts but without spreads or fees """
    # function for calculating the price of the replicating set of contracts
    # for one trade (row)
    def replicate_no_contract_no_spreads_no_fees(row):
        contract_id = row[('_trades', 'contract_id')]

        # use the midquote at the time of the trade
        Y_a = row[idx['contract_' + str(contract_id)]].mean()
        # sum of midquotes of contracts other than the one that traded
        sum_Y_i = sum([row[idx['contract_' + str(c_id)]].mean()
                       for c_id in contract_ids
                       if c_id != contract_id])

        if abs(sum_Y_i - 1) < 1e-3:
            d = np.nan
        else:
            d = Y_a / (1 - sum_Y_i)

        return d

    trader_analysis1_no = (
        trader_analysis[trader_analysis.loc[
            idx[:, ('_trades', 'trade_type')]] == 'Buy No'
        ].copy()
    )

    trader_analysis1_no.loc[:, ('replication', 'd')] = (
        trader_analysis1_no.apply(
            replicate_no_contract_no_spreads_no_fees, axis=1)
    )

    # function for checking the replicating contract. does it meet assumptions?
    # also calculates the max loss
    def check_replicate_no_contract_no_spreads_no_fees(row):

        contract_id = row[('_trades', 'contract_id')]
        d = row[('replication', 'd')]

        if np.isnan(d):
            return np.nan

        target_pnl = row[idx['contract_' + str(contract_id)]].mean()
        losses = []

        for c_id_win in contract_ids:
            pnl = 0
            for c_id in contract_ids:
                if c_id == contract_id:
                    # bought zero Yes contracts for this one
                    continue
                else:
                    if d > 0:
                        if np.isnan(row[idx['contract_' + str(c_id)]].mean()):
                            # if this is nan we don't have quote data for it.
                            # must be before trading started on this contract
                            continue
                        if c_id == c_id_win:
                            # bought d Yes contracts, made money
                            pnl += (
                                d * (1 -
                                     row[idx['contract_' + str(c_id)]].mean())
                            )
                        else:
                            # bought d Yes contracts, lost money
                            pnl -= d * row[idx['contract_' + str(c_id)]].mean()
                    else:  # d < 0
                        if np.isnan(row[idx['contract_' + str(c_id)]].mean()):
                            # if this is nan we don't have quote data for it.
                            # must be before trading started on this contract
                            continue
                        if c_id == c_id_win:
                            # bought d No contracts, lost money
                            pnl -= (
                                (-d) *
                                (1 - row[idx['contract_' + str(c_id)]].mean())
                            )
                        else:
                            # bought d No contracts, made money
                            pnl += (
                                (-d) *
                                row[idx['contract_' + str(c_id)]].mean()
                            )

            if c_id_win != contract_id:
                # upside must be the same
                assert abs(target_pnl - pnl) < 1e-7
            else:
                losses.append(pnl)

        # min and max losses should be the same
        assert abs(min(losses) - max(losses)) < 1e-7

        return -max(losses)

    trader_analysis1_no.loc[:, ('replication', 'max_loss')] = (
        trader_analysis1_no.apply(
            check_replicate_no_contract_no_spreads_no_fees, axis=1)
    )

    # add midquote at time of trade since we need that for the plots
    def midquote_at_time_of_trade(row):
        contract_id = row[('_trades', 'contract_id')]
        return row[idx['contract_' + str(contract_id)]].mean()

    trader_analysis1_no.loc[:, ('replication', 'N_a')] = (
        1 - trader_analysis1_no.apply(midquote_at_time_of_trade, axis=1)
    )

    return trader_analysis1_no


###############################################################################
# Yes Contracts: Spreads but no Fees
###############################################################################


def calculate_yes_contracts_spreads_but_no_fees(trader_analysis, contract_ids):
    """ Yes contracts with spreads but no fees """
    # function for calculating the price of the replicating set of contracts
    # for one trade (row)
    def replicate_yes_contract_spreads_no_fees(row):
        contract_id = row[('_trades', 'contract_id')]

        # use the actual price the contract traded, which will be on the bid or
        # ask
        Y_a = row[('_trades', 'price_per_share')]
        # sum of bid prices of Yes contracts, because replicating by buying
        # No contracts
        sum_Y_i = (
            sum([row[idx['contract_' + str(c_id), '_bid']]
                 for c_id in contract_ids
                 if c_id != contract_id])
        )

        if sum_Y_i == 0:
            c = np.nan
        else:
            c = (1 - Y_a) / sum_Y_i

        return c

    trader_analysis2_yes = (
        trader_analysis[
            trader_analysis.loc[idx[:, ('_trades', 'trade_type')]] == 'Buy Yes'
        ].copy()
    )

    trader_analysis2_yes.loc[:, ('replication', 'c')] = (
        trader_analysis2_yes.apply(
            replicate_yes_contract_spreads_no_fees, axis=1)
    )

    # function for checking the replicating contract. does it meet assumptions?
    # also calculates the max loss
    def check_replicate_yes_contract_spreads_no_fees(row):
        contract_id = row[('_trades', 'contract_id')]
        c = row[('replication', 'c')]
        target_pnl = 1 - row[('_trades', 'price_per_share')]
        losses = []

        if np.isnan(c):
            return np.nan

        for c_id_win in contract_ids:
            pnl = 0
            for c_id in contract_ids:
                if c_id == contract_id:
                    # bought zero No contracts for this one
                    continue
                else:
                    if np.isnan(row[idx['contract_' + str(c_id), '_bid']]):
                        # if this is nan we don't have quote data for it. must
                        # be before trading started on this contract
                        continue
                    if c_id == c_id_win:
                        # bought c No contracts, lost money
                        pnl -= (
                            c * (1 - row[idx['contract_' + str(c_id), '_bid']])
                        )
                    else:
                        # bought c No contracts, made money
                        pnl += c * row[idx['contract_' + str(c_id), '_bid']]

            if c_id_win == contract_id:
                # upside must be the same
                assert abs(target_pnl - pnl) < 1e-7
            else:
                losses.append(pnl)

        # min and max losses should be the same
        assert abs(min(losses) - max(losses)) < 1e-7

        return -max(losses)

    trader_analysis2_yes.loc[:, ('replication', 'max_loss')] = (
        trader_analysis2_yes.apply(
            check_replicate_yes_contract_spreads_no_fees, axis=1)
    )

    return trader_analysis2_yes


###############################################################################
# No Contracts: Spreads but no Fees
###############################################################################


def calculate_no_contracts_spreads_but_no_fees(trader_analysis, contract_ids):
    """ No contracts with spreads but no fees """
    # function for calculating the price of the replicating set of contracts
    # for one trade (row)
    def replicate_no_contract_spreads_no_fees(row):
        contract_id = row[('_trades', 'contract_id')]

        # use the corrected price for the contract traded, which will be on the
        # bid or ask
        Y_a = row[('_trades', 'corrected_price')]
        #  sum of ask prices of Yes contracts other than the one that traded
        sum_Y_i = (
            sum([row[idx['contract_' + str(c_id), 'ask']]
                 for c_id in contract_ids
                 if c_id != contract_id])
        )

        if sum_Y_i >= 1 - 1e-3:
            d = np.nan
        else:
            d = Y_a / (1 - sum_Y_i)

        if np.isnan(d):
            sum_Y_i = (
                sum([row[idx['contract_' + str(c_id), '_bid']]
                     for c_id in contract_ids
                     if c_id != contract_id])
            )

            if sum_Y_i <= 1 + 1e-3:
                d = np.nan
            else:
                d = -Y_a / (sum_Y_i - 1)

        return d

    trader_analysis2_no = (
        trader_analysis[
            trader_analysis.loc[idx[:, ('_trades', 'trade_type')]] == 'Buy No'
        ].copy()
    )

    trader_analysis2_no.loc[:, ('replication', 'd')] = (
        trader_analysis2_no.apply(
            replicate_no_contract_spreads_no_fees, axis=1)
    )

    # function for checking the replicating contract. does it meet assumptions?
    # also calculates the max loss
    def check_replicate_no_contract_spreads_no_fees(row):
        contract_id = row[('_trades', 'contract_id')]
        d = row[('replication', 'd')]

        if np.isnan(d):
            return np.nan

        target_pnl = 1 - row[('_trades', 'price_per_share')]
        losses = []

        for c_id_win in contract_ids:
            pnl = 0
            for c_id in contract_ids:
                if c_id == contract_id:
                    # bought zero Yes contracts for this one
                    continue
                else:
                    if d > 0:
                        if np.isnan(row[idx['contract_' + str(c_id), 'ask']]):
                            # if this is nan we don't have quote data for it.
                            # must be before trading started on this contract
                            continue
                        if c_id == c_id_win:
                            # bought d Yes contracts, made money
                            pnl += (
                                d * (1 -
                                     row[idx['contract_' + str(c_id), 'ask']])
                            )
                        else:
                            # bought d Yes contracts, lost money
                            pnl -= d * row[idx['contract_' + str(c_id), 'ask']]
                    else:  # d < 0
                        if np.isnan(row[idx['contract_' + str(c_id), '_bid']]):
                            # if this is nan we don't have quote data for it.
                            # must be before trading started on this contract
                            continue
                        if c_id == c_id_win:
                            # bought d No contracts, lost money
                            pnl -= (
                                (-d) *
                                (1 - row[idx['contract_' + str(c_id), '_bid']])
                            )
                        else:
                            # bought d No contracts, made money
                            pnl += (
                                (-d) *
                                row[idx['contract_' + str(c_id), '_bid']]
                            )

            if c_id_win != contract_id:
                # upside must be the same
                assert abs(target_pnl - pnl) < 1e-7
            else:
                losses.append(pnl)

        # min and max losses should be the same
        assert abs(min(losses) - max(losses)) < 1e-7

        return -max(losses)

    trader_analysis2_no.loc[:, ('replication', 'max_loss')] = (
        trader_analysis2_no.apply(
            check_replicate_no_contract_spreads_no_fees, axis=1)
    )

    return trader_analysis2_no


###############################################################################
# Yes Contracts: Spreads and Fees
###############################################################################


def calculate_yes_contracts_spreads_and_fees(trader_analysis, contract_ids):
    """ Yes contracts with spreads and fees """
    fee = 0.1

    # function for calculating the price of the replicating set of contracts
    # for one trade (row)
    def replicate_yes_contract_spreads_fees(row):
        contract_id = row[('_trades', 'contract_id')]

        def g(skip):
            return reduce(mul,
                          [1 - fee * row[idx['contract_' + str(k), '_bid']]
                           for k in contract_ids if k not in skip],
                          1)

        c = {}

        for c_id in contract_ids:
            if c_id == contract_id:
                c[c_id] = 0
            else:
                # use the actual price the contract traded, which will be on
                # the bid or ask
                Y_a = row[('_trades', 'price_per_share')]
                # sum of bid prices of Yes contracts, because replicating by
                # buying No contracts
                sum_Y_i = sum(
                    [row[idx['contract_' + str(i), '_bid']] *
                     g([i, contract_id])
                     for i in contract_ids if i != contract_id])

                if sum_Y_i == 0:
                    c[c_id] = np.nan
                else:
                    c[c_id] = (1 - Y_a) * g([c_id, contract_id]) / sum_Y_i

        # why do I have to do this?? Pandas should accept a dictionary as an
        # object
        return str(c)

    trader_analysis3_yes = (
        trader_analysis[
            trader_analysis.loc[idx[:, ('_trades', 'trade_type')]] == 'Buy Yes'
        ].copy()
    )

    trader_analysis3_yes.loc[:, ('replication', 'c')] = (
        trader_analysis3_yes.apply(replicate_yes_contract_spreads_fees, axis=1)
    )

    # function for checking the replicating contract. does it meet assumptions?
    # also calculates the max loss
    def check_replicate_yes_contract_spreads_fees(row):
        contract_id = row[('_trades', 'contract_id')]
        target_pnl = (1 - fee) * (1 - row[('_trades', 'price_per_share')])
        losses = []

        try:
            c_dict = eval(row[('replication', 'c')])
        except Exception as e:
            return np.nan

        for c_id_win in contract_ids:
            pnl = 0
            for c_id in contract_ids:
                c = c_dict[c_id]
                if c_id == contract_id:
                    # bought zero No contracts for this one
                    continue
                else:
                    if np.isnan(row[idx['contract_' + str(c_id), '_bid']]):
                        # if this is nan we don't have quote data for it. must
                        # be before trading started on this contract
                        continue
                    if c_id == c_id_win:
                        # bought c No contracts, lost money
                        pnl -= (
                            c * (1 - row[idx['contract_' + str(c_id), '_bid']])
                        )
                    else:
                        # bought c No contracts, made money
                        pnl += (
                            c *
                            (1 - fee) *
                            row[idx['contract_' + str(c_id), '_bid']]
                        )

            if c_id_win == contract_id:
                # upside must be the same
                assert abs(target_pnl - pnl) < 1e-7
            else:
                losses.append(pnl)

        # min and max losses should be the same
        assert abs(min(losses) - max(losses)) < 1e-7

        return -max(losses)

    trader_analysis3_yes.loc[:, ('replication', 'max_loss')] = (
        trader_analysis3_yes.apply(
            check_replicate_yes_contract_spreads_fees, axis=1)
    )

    return trader_analysis3_yes


###############################################################################
# No Contracts: Spreads and Fees
###############################################################################


def calculate_no_contracts_spreads_and_fees(trader_analysis, contract_ids):
    """ No contracts with spreads and fees """
    fee = 0.1

    # function for calculating the price of the replicating set of contracts
    # for one trade (row)
    def replicate_no_contract_spreads_fees(row):
        contract_id = row[('_trades', 'contract_id')]

        def g(skip):
            return reduce(mul,
                          [1 - fee + fee * row[idx['contract_' + str(k),
                                                   'ask']]
                           for k in contract_ids if k not in skip],
                          1)

        def g2(skip):
            return reduce(mul,
                          [1 - fee * row[idx['contract_' + str(k), '_bid']]
                           for k in contract_ids if k not in skip],
                          1)

        d = {'contracts': 'YES'}

        for c_id in contract_ids:
            if c_id == contract_id:
                d[c_id] = 0
            else:
                # use the corrected price of the contract traded, which will be
                # on the bid or ask
                Y_a = row[('_trades', 'corrected_price')]
                #  sum of ask prices of Yes contracts other than the one that
                # traded
                numer1 = (
                    (1 - fee) *
                    (1 -
                     row[idx['contract_' + str(c_id), 'ask']]) *
                    g([c_id, contract_id])
                )
                numer2 = (
                    sum([row[idx['contract_' + str(i), 'ask']] *
                         g([i, contract_id])
                         for i in contract_ids
                         if i not in [c_id, contract_id]]))

                if abs(numer1 - numer2) <= 1e-3:
                    d[c_id] = np.nan
                else:
                    d[c_id] = (
                        (1 - fee) *
                        Y_a *
                        g([c_id, contract_id]) / (numer1 - numer2)
                    )

                if np.isnan(d[c_id]) or d[c_id] < 0:
                    d['contracts'] = 'NO'

                    numer1 = ((1 - fee) *
                              row[('_trades', 'corrected_price')] *
                              g2([c_id, contract_id]))
                    denom1 = (
                        -(1 - row[idx['contract_' + str(c_id), '_bid']]) *
                        g2([c_id, contract_id])
                    )
                    denom2 = ((1 - fee) *
                              sum([row[idx['contract_' + str(i), '_bid']] *
                                   g2([i, contract_id])
                                   for i in contract_ids
                                   if i not in [c_id, contract_id]]))

                    if abs(denom1 + denom2) <= 1e-3:
                        d[c_id] = np.nan
                    else:
                        d[c_id] = numer1 / (denom1 + denom2)

                    if d[c_id] < 0:
                        d[c_id] = np.nan

        # why do I need to do this? Must be a Pandas bug?
        return str(d)

    trader_analysis3_no = (
        trader_analysis[
            trader_analysis.loc[idx[:, ('_trades', 'trade_type')]] == 'Buy No'
        ].copy()
    )

    trader_analysis3_no.loc[:, ('replication', 'd')] = (
        trader_analysis3_no.apply(
            replicate_no_contract_spreads_fees, axis=1)
    )

    # function for checking the replicating contract. does it meet assumptions?
    # also calculates the max loss
    def check_replicate_no_contract_spreads_fees(row):
        contract_id = row[('_trades', 'contract_id')]
        target_pnl = (1 - fee) * (1 - row[('_trades', 'price_per_share')])
        losses = []

        try:
            d_dict = eval(row[('replication', 'd')])
        except Exception as e:
            return np.nan

        # are we replicating with yes or no contracts?
        replicate_with_yes_contracts = d_dict['contracts'] == 'YES'

        if replicate_with_yes_contracts:
            for c_id_win in contract_ids:
                pnl = 0
                for c_id in contract_ids:
                    d = d_dict[c_id]
                    if c_id == contract_id:
                        # bought zero Yes contracts for this one
                        continue
                    else:
                        if np.isnan(row[idx['contract_' + str(c_id), 'ask']]):
                            # if this is nan we don't have quote data for it.
                            # must be before trading started on this contract
                            continue
                        if c_id == c_id_win:
                            # bought d Yes contracts, made money
                            pnl += (
                                (1 - fee) *
                                d *
                                (1 - row[idx['contract_' + str(c_id), 'ask']])
                            )
                        else:
                            # bought d Yes contracts, lost money
                            pnl -= d * row[idx['contract_' + str(c_id), 'ask']]

                if c_id_win != contract_id:
                    # upside must be the same
                    assert abs(target_pnl - pnl) < 1e-7
                else:
                    losses.append(pnl)
        else:  # No contracts
            for c_id_win in contract_ids:
                pnl = 0
                for c_id in contract_ids:
                    d = d_dict[c_id]
                    if c_id == contract_id:
                        # bought zero No contracts for this one
                        continue
                    else:
                        if np.isnan(row[idx['contract_' + str(c_id), '_bid']]):
                            # if this is nan we don't have quote data for it.
                            # must be before trading started on this contract
                            continue
                        if c_id == c_id_win:
                            # bought d No contracts, lost money
                            pnl -= (
                                d *
                                (1 - row[idx['contract_' + str(c_id), '_bid']])
                            )
                        else:
                            # bought d No contracts, made money
                            pnl += (
                                d *
                                (1 - fee) *
                                row[idx['contract_' + str(c_id), '_bid']]
                            )

                if c_id_win != contract_id:
                    # upside must be the same
                    assert abs(target_pnl - pnl) < 1e-7
                else:
                    losses.append(pnl)

        # min and max losses should be the same
        assert abs(min(losses) - max(losses)) < 1e-7

        return -max(losses)

    trader_analysis3_no.loc[:, ('replication', 'max_loss')] = (
        trader_analysis3_no.apply(
            check_replicate_no_contract_spreads_fees, axis=1)
    )

    return trader_analysis3_no


###############################################################################
# Main Calculation function
###############################################################################


def calculate_replicating_prices(trader_analysis, quotes_dict):
    """ calculate the replicating backet of contracts

    For each trade recorded in the trader_analysis DataFrame calculate the
    set of Yes or No contracts that could have given the same payoff.
    """
    # make the column names a MultiIndex
    # after making a copy so we don't mess with the original
    trader_analysis = trader_analysis.copy()
    trader_analysis.columns = (
        pd.MultiIndex.from_tuples(
            list(zip(repeat('_trades'), trader_analysis.columns)))
    )

    def add_contract_id(df, contract_id):
        df = df.drop('timestamp', axis=1).copy()
        contract_id_str = 'contract_' + str(contract_id)
        df.columns = pd.MultiIndex.from_tuples(
            [(contract_id_str, '_bid'), (contract_id_str, 'ask')])

        return df

    # prepare the quote data and get the contract ids for this market
    quotes = (
        pd.concat([add_contract_id(df, c_id)
                   for c_id, df in quotes_dict.items()]
                  ).sort_index().ffill()
    )
    contract_ids = list(quotes_dict.keys())

    # merge the quote data with the trade data
    trader_analysis = pd.merge_asof(
        trader_analysis.sort_values([('_trades', 'seq')]),
        quotes,
        left_on=[('_trades', 'seq')],
        right_index=True,
        allow_exact_matches=True).sort_index()

    out = dict()

    out['yes contracts no spreads or fees'] = (
        calculate_yes_contracts_no_spreads_or_fees(
            trader_analysis, contract_ids)
    )

    out['no contracts no spreads or fees'] = (
        calculate_no_contracts_no_spreads_or_fees(
            trader_analysis, contract_ids)
    )

    out['yes contracts spreads but no fees'] = (
        calculate_yes_contracts_spreads_but_no_fees(
            trader_analysis, contract_ids)
    )

    out['no contracts spreads but no fees'] = (
        calculate_no_contracts_spreads_but_no_fees(
            trader_analysis, contract_ids)
    )

    out['yes contracts spreads and fees'] = (
        calculate_yes_contracts_spreads_and_fees(
            trader_analysis, contract_ids)
    )

    out['no contracts spreads and fees'] = (
        calculate_no_contracts_spreads_and_fees(
            trader_analysis, contract_ids)
    )

    return out
