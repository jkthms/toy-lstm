import asyncio
import aiohttp
import logging
import csv
import os
import sys
from datetime import datetime, timezone
import tqdm
from typing import Optional

# Basic logging configuration
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Upstream constants
API_ENDPOINT = "https://api.hyperliquid.xyz/info"
INTERVAL = 15  # in minutes
OUTPUT_CSV = "files/futures.csv"

# Key mappings for the API response
KEY_MAP = {
    "t": "open_timestamp",
    "T": "close_timestamp",
    "c": "close",
    "h": "high",
    "l": "low",
    "o": "open",
    "v": "volume",
    "n": "transactions",
    "s": "symbol",
}
OUTPUT_KEYS = list(KEY_MAP.values())
TYPE_MAP = {
    "t": int,
    "T": int,
    "c": float,
    "h": float,
    "l": float,
    "o": float,
    "v": float,
    "n": int,
    "s": str,
}


def cast_value(key: str, value: str):
    return TYPE_MAP[key](value)


def compute_payload(
    asset_id: str, interval: int, start_time: int, end_time: int
) -> dict:
    """
    Helper function to return the payload for an API request to the Hyperliquid API for a given asset, interval, and time range.
    """
    return {
        "type": "candleSnapshot",
        "req": {
            "coin": asset_id,
            "interval": f"{interval}m",
            "startTime": start_time,
            "endTime": end_time,
        },
    }


async def fetch_data(
    session: aiohttp.ClientSession,
    asset_id: str,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
) -> dict:
    """
    Async coroutine to fetch the contract history for a given asset, represented by an asset_id.
    """
    # Calculate the current timestamp in UNIX milliseconds
    current_time = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    # Normalise the interval to a period in milliseconds
    delta = 60 * 1000 * INTERVAL

    if end_time is None:
        # Calculate the end time for the final candle in the query as the most recent candle
        end_time = (current_time // delta) * delta

    if start_time is None:
        # Default to fetching the prior 5000 candles if no start time is provided
        start_time = end_time - delta * 5000

    payload = compute_payload(asset_id, INTERVAL, start_time, end_time)

    # Make an async POST request to the API for the given payload
    logging.info(f"Fetching data for {asset_id} from {start_time} to {end_time}.")

    async with session.post(API_ENDPOINT, json=payload) as response:
        if response.status != 200:
            logging.error(
                f"Failed to fetch data for {asset_id} from {start_time} to {end_time}. Status: {response.status}."
            )
            response.raise_for_status()
        data = await response.json()

    # Map the API response to the key mapping
    output = []

    for item in data:
        row = {
            KEY_MAP[key]: cast_value(key, value)
            for key, value in item.items()
            if key in KEY_MAP
        }
        output.append(row)

    return output


async def fetch_all_contracts(session: aiohttp.ClientSession):
    """ """
    payload = {"type": "metaAndAssetCtxs"}

    async with session.post(API_ENDPOINT, json=payload) as response:
        if response.status != 200:
            logging.error(
                f"Failed to fetch universe from API. Status: {response.status}."
            )
            response.raise_for_status()
        metadata = await response.json()

    if not metadata:
        logging.error("Metadata request result was empty or invalid. Aborting.")
        return []

    output = []
    for asset in metadata[0]["universe"]:
        if asset.get("name"):
            output.append(asset["name"])

    return output


async def main():
    async with aiohttp.ClientSession() as session:
        contracts = await fetch_all_contracts(session)
        logging.info(f"Fetched {len(contracts)} contracts for batch query.")

        # Create batches of ~9 requests per minute to stay under rate limit
        batch_size = 5
        batches = [
            contracts[i : i + batch_size] for i in range(0, len(contracts), batch_size)
        ]

        logging.info("Fetching data for all contracts in batches...")

        results = []
        for batch in batches:
            coroutines = [fetch_data(session, contract) for contract in batch]
            batch_results = await asyncio.gather(*coroutines)

            for item in batch_results:
                results.extend(item)

            logging.info(f"Scraped {len(results)} data points so far.")

            # Create the output file if it does not exist
            os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

            with open(OUTPUT_CSV, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=OUTPUT_KEYS)
                writer.writeheader()
                writer.writerows(results)

            if batch != batches[-1]:
                logging.info(
                    f"Completed batch of {len(batch)} contracts. Waiting before next batch..."
                )
                await asyncio.sleep(60)

        logging.info(
            f"Completed fetching data for all contracts. {len(results)} results found."
        )

    return


if __name__ == "__main__":
    try:
        # Fixes clean-up errors with ProactorEventLoop on Windows
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Ctrl+C detected. Exiting gracefully.")
        pass
    finally:
        pass


# TODO: Add support to batch fetch all historical funding rates: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-historical-funding-rates
