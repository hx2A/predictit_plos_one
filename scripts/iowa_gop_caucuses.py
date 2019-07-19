import pandas as pd

from research_tools import trading
from research_tools import behavior
from research_tools import storage
from research_tools import reconstruct_tob
from research_tools import dominant_contracts
from research_tools import trader_efficiency


print('load data from data directory')
orders_gop = pd.read_csv('data/gop_iowa_caucus_orders.csv', index_col=0)
trades_gop = pd.read_csv('data/gop_iowa_caucus_trades.csv', index_col=0)

orders_gop.date_created = pd.to_datetime(orders_gop.date_created).dt.tz_localize('UTC').dt.tz_convert('US/Eastern')
trades_gop.date_executed = pd.to_datetime(trades_gop.date_executed).dt.tz_localize('UTC').dt.tz_convert('US/Eastern')

print("analyze GOP trader pnl")
trader_analysis_gop = trading.trader_analysis(orders_gop, trades_gop)
print("generate GOP taq")
reconstructed_quotes_gop = reconstruct_tob.generate_quotes(trades_gop)
print("calculate GOP replicating contract prices")
replicating_contracts_gop = dominant_contracts.calculate_replicating_prices(
    trader_analysis_gop, reconstructed_quotes_gop)
print("calculate GOP trader efficiency")
trader_efficiency_gop = trader_efficiency.calculate_trader_efficiency(
    trader_analysis_gop,
    replicating_contracts_gop['yes contracts spreads and fees'],
    replicating_contracts_gop['no contracts spreads and fees'],
    10)
print("analyze GOP trader behavior")
behavior_analysis_gop = behavior.behavior_analysis(
    trader_analysis_gop, trader_efficiency_gop)

print("storing GOP data")
basename = 'gop'
storage.save_all(
    [(basename + '.orders', orders_gop),
     (basename + '.trades', trades_gop),
     (basename + '.trader_analysis', trader_analysis_gop),
     (basename + '.behavior_analysis', behavior_analysis_gop),
     (basename + '.reconstructed_quotes', reconstructed_quotes_gop),
     (basename + '.replicating_contracts', replicating_contracts_gop),
     (basename + '.trader_efficiency', trader_efficiency_gop)])
