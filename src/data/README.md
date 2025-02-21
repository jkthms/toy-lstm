# toy-lstm-data

This script is a one-shot script that fetches the last 5000 candles for each perpetual future which trades on the Hyperliquid exchange. The resulting output data is stored in the `files/futures.csv` file and has the structure:
```
open_timestamp,close_timestamp,close,high,low,open,volume,transactions,symbol
1735658100000,1735658999999,95635.0,95721.0,95349.0,95480.0,129.13684,2229,BTC
1735659000000,1735659899999,95793.0,96040.0,95500.0,95640.0,171.87256,2061,BTC
```

## Usage

```
python run.py
```

## Console Output

```
2025-02-21 17:26:01,866 - INFO - Fetched 186 contracts for batch query.
2025-02-21 17:26:01,866 - INFO - Fetching data for all contracts in batches...
2025-02-21 17:26:01,866 - INFO - Fetching data for BTC from 1735658100000 to 1740158100000.
2025-02-21 17:26:01,866 - INFO - Fetching data for ETH from 1735658100000 to 1740158100000.
2025-02-21 17:26:01,867 - INFO - Fetching data for ATOM from 1735658100000 to 1740158100000.
2025-02-21 17:26:01,867 - INFO - Fetching data for MATIC from 1735658100000 to 1740158100000.
2025-02-21 17:26:01,867 - INFO - Fetching data for DYDX from 1735658100000 to 1740158100000.
2025-02-21 17:26:04,199 - INFO - Scraped 20004 data points so far.
...
```
