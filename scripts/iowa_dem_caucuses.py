import pandas as pd

from research_tools import trading
from research_tools import behavior
from research_tools import storage
from research_tools import reconstruct_tob
from research_tools import dominant_contracts
from research_tools import trader_efficiency


print('load data from data directory')
orders_dem = pd.read_csv('data/dem_iowa_caucus_orders.csv', index_col=0)
trades_dem = pd.read_csv('data/dem_iowa_caucus_trades.csv', index_col=0)

orders_dem.date_created = pd.to_datetime(orders_dem.date_created).dt.tz_localize('UTC').dt.tz_convert('US/Eastern')
trades_dem.date_executed = pd.to_datetime(trades_dem.date_executed).dt.tz_localize('UTC').dt.tz_convert('US/Eastern')

print("analyze DEM trader pnl")
trader_analysis_dem = trading.trader_analysis(orders_dem, trades_dem)
print("generate DEM taq")
reconstructed_quotes_dem = reconstruct_tob.generate_quotes(trades_dem)
print("calculate DEM replicating contract prices")
replicating_contracts_dem = dominant_contracts.calculate_replicating_prices(
    trader_analysis_dem, reconstructed_quotes_dem)
print("calculate DEM trader efficiency")
trader_efficiency_dem = trader_efficiency.calculate_trader_efficiency(
    trader_analysis_dem,
    replicating_contracts_dem['yes contracts spreads and fees'],
    replicating_contracts_dem['no contracts spreads and fees'],
    10)
print("analyze DEM trader behavior")
behavior_analysis_dem = behavior.behavior_analysis(
    trader_analysis_dem, trader_efficiency_dem)

print("storing DEM data")
basename = 'dem'
storage.save_all(
    [(basename + '.orders', orders_dem),
     (basename + '.trades', trades_dem),
     (basename + '.trader_analysis', trader_analysis_dem),
     (basename + '.behavior_analysis', behavior_analysis_dem),
     (basename + '.reconstructed_quotes', reconstructed_quotes_dem),
     (basename + '.replicating_contracts', replicating_contracts_dem),
     (basename + '.trader_efficiency', trader_efficiency_dem)])
