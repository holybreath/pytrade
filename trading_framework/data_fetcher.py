import requests
import time
import json
import datetime # For converting Unix timestamp to readable date in detect_abnormal_fluctuations
import logging

# Configure basic logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
log = logging.getLogger(__name__)

# --- Session and Configuration (will be set by main.py or config.py) ---
# These are placeholders; actual values should be injected or imported from config
# For now, define them here so the module can be imported without immediate error.
# In a real setup, main.py would update these from config.py before first use.
PROXIES = {}
HEADERS = {}

session = requests.Session()
# session.proxies = PROXIES # Set by main.py before use
# session.headers.update(HEADERS) # Set by main.py before use


# --- Constants ---
MIN_KLINE_FOR_FLUCTUATION_DETECT = 2 # Needs current and previous k-lines for detect_abnormal_fluctuations

# --- Function 1: Fetch Yahoo Finance Chart Data ---
def fetch_yahoo_chart_data(symbol: str, interval: str, period: str) -> dict:
    """
    Fetches K-line chart data from Yahoo Finance API.
    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
        interval (str): K-line interval, e.g., '15m', '1d'.
        period (str): Data period, e.g., '7d', '6mo'.
    Returns:
        dict: Raw chart data result from Yahoo Finance, or empty dict on failure.
    """
    # Update session with latest proxies and headers (in case they are dynamic)
    # This is important if main.py updates PROXIES and HEADERS after this module is imported.
    from .config import PROXIES as cfg_proxies, HEADERS as cfg_headers # Get latest from config
    session.proxies = cfg_proxies
    session.headers.update(cfg_headers)

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&period={period}"
    log.info(f"Fetching data for {symbol}: interval={interval}, period={period} from {url}")

    try:
        response = session.get(url, verify=True, timeout=15)
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)

        data = response.json()
        if data.get("chart") and data["chart"].get("result") and isinstance(data["chart"]["result"], list) and len(data["chart"]["result"]) > 0:
            # Ensure 'meta' exists, if not, create a basic one.
            if "meta" not in data["chart"]["result"][0]:
                data["chart"]["result"][0]["meta"] = {"symbol": symbol} # Add basic meta if missing
            elif "symbol" not in data["chart"]["result"][0]["meta"]:
                 data["chart"]["result"][0]["meta"]["symbol"] = symbol


            # Ensure necessary quote data is present, even if empty lists, to prevent KeyErrors downstream
            if "indicators" not in data["chart"]["result"][0] or \
               "quote" not in data["chart"]["result"][0]["indicators"] or \
               not isinstance(data["chart"]["result"][0]["indicators"]["quote"], list) or \
               len(data["chart"]["result"][0]["indicators"]["quote"]) == 0:
                log.warning(f"Indicators or quote data missing/malformed for {symbol}. Injecting empty structure.")
                if "indicators" not in data["chart"]["result"][0]:
                    data["chart"]["result"][0]["indicators"] = {"quote": [{}]}
                elif "quote" not in data["chart"]["result"][0]["indicators"]:
                     data["chart"]["result"][0]["indicators"]["quote"] = [{}]
                elif not isinstance(data["chart"]["result"][0]["indicators"]["quote"], list) or \
                     len(data["chart"]["result"][0]["indicators"]["quote"]) == 0:
                     data["chart"]["result"][0]["indicators"]["quote"] = [{}] # Replace if malformed

            # Ensure basic fields (open, high, low, close, volume, timestamp) exist in quote/timestamp
            # If not, downstream parsing might fail. parse_kline_data handles missing fields gracefully.
            return data["chart"]["result"][0]
        else:
            log.error(f"No chart result found in response for {symbol}. Response text (first 500 chars): {response.text[:500]}")
            return {}

    except requests.exceptions.HTTPError as e:
        log.error(f"HTTP Error {e.response.status_code} for {symbol}: {e.response.text[:200]} (URL: {url})")
        if e.response.status_code == 401 or e.response.status_code == 403:
            log.warning(f"Authentication/Authorization issue for {symbol}. Check your Cookie/Headers in config.py.")
        elif e.response.status_code == 429:
            log.warning(f"Received 429 Too Many Requests for {symbol}. Consider increasing delays or checking API limits.")
        return {}
    except requests.exceptions.ConnectionError as e:
        log.error(f"Connection Error for {symbol}: {e}. Check proxy or network. (URL: {url})")
        return {}
    except requests.exceptions.Timeout:
        log.error(f"Timeout Error for {symbol}. Server took too long to respond. (URL: {url})")
        return {}
    except json.JSONDecodeError:
        log.error(f"JSON Decode Error for {symbol}. Response was not valid JSON. (URL: {url}) Response text (first 500 chars): {response.text[:500] if 'response' in locals() else 'Response object not available'}")
        return {}
    except requests.exceptions.RequestException as e:
        log.error(f"An unexpected error occurred for {symbol}: {e} (URL: {url})")
        return {}
    except Exception as e: # Catch any other unexpected error during processing
        log.error(f"A generic exception occurred processing data for {symbol}: {e}", exc_info=True)
        return {}


# --- Function 2: Parse K-line Data ---
def parse_kline_data(chart_data: dict) -> list:
    """
    Parses K-line data from Yahoo Finance chart data.
    Args:
        chart_data (dict): The result part of fetch_yahoo_chart_data's return.
    Returns:
        list: List of K-line dicts, each with 'timestamp', 'open', 'high', 'low', 'close', 'volume'.
              Returns empty list if data is missing or malformed.
    """
    if not chart_data or "timestamp" not in chart_data:
        log.warning("parse_kline_data: chart_data is empty or missing 'timestamp' key.")
        return []

    timestamps = chart_data.get("timestamp", [])
    # Ensure quotes structure exists and is a list with at least one element
    quotes_list = chart_data.get("indicators", {}).get("quote", [{}])
    if not quotes_list or not isinstance(quotes_list, list) or not quotes_list[0]:
        log.warning("parse_kline_data: 'quote' data is missing or malformed. Using empty values.")
        quotes = {}
    else:
        quotes = quotes_list[0] # Main quote data

    opens = quotes.get("open", [])
    highs = quotes.get("high", [])
    lows = quotes.get("low", [])
    closes = quotes.get("close", [])
    volumes = quotes.get("volume", [])

    # Handle cases where indicator lists might be None or shorter than timestamps
    min_len = len(timestamps)
    for data_list in [opens, highs, lows, closes, volumes]:
        if data_list is None: # If any list is None, cannot proceed safely
            log.warning("parse_kline_data: One of the OHLCV lists is None. Returning empty kline_list.")
            return []
        min_len = min(min_len, len(data_list))

    if min_len != len(timestamps):
        log.warning(f"parse_kline_data: Mismatch in lengths of timestamp ({len(timestamps)}) and OHLCV data (min_len: {min_len}). Truncating to shortest.")

    kline_list = []
    for i in range(min_len):
        # Filter out data points where essential values might be None (Yahoo sometimes returns None for recent, incomplete candles)
        if timestamps[i] is not None and \
           (opens[i] is not None if opens else True) and \
           (highs[i] is not None if highs else True) and \
           (lows[i] is not None if lows else True) and \
           (closes[i] is not None if closes else True) and \
           (volumes[i] is not None if volumes else True):

            kline_list.append({
                "timestamp": timestamps[i],
                # Provide default 0 if list was empty or value is None (though None should be filtered by above)
                "open": opens[i] if opens and opens[i] is not None else 0,
                "high": highs[i] if highs and highs[i] is not None else 0,
                "low": lows[i] if lows and lows[i] is not None else 0,
                "close": closes[i] if closes and closes[i] is not None else 0,
                "volume": volumes[i] if volumes and volumes[i] is not None else 0
            })
        else:
            log.debug(f"parse_kline_data: Skipping data point {i} for symbol due to None values. TS: {timestamps[i]}")

    if not kline_list and timestamps: # If we had timestamps but couldn't form any valid klines
        log.warning("parse_kline_data: No valid K-lines could be constructed from the provided chart_data, possibly due to all data points having None values.")

    return kline_list


# --- Function 3: Detect Abnormal Fluctuations ---
def detect_abnormal_fluctuations(symbol: str, kline_data: list, threshold_percentage: float = 1.0) -> dict:
    """
    Detects if the latest K-line shows abnormal fluctuation compared to the previous one.
    Args:
        symbol (str): Stock symbol for logging.
        kline_data (list): List of K-line dicts from parse_kline_data.
        threshold_percentage (float): Fluctuation percentage threshold (e.g., 1.0 for 1%).
                                      Based on original user code, this is treated as an ABSOLUTE price change.
    Returns:
        dict: Details of the anomaly if found, otherwise an empty dict.
    """
    if not kline_data or len(kline_data) < MIN_KLINE_FOR_FLUCTUATION_DETECT:
        log.debug(f"Not enough K-line data ({len(kline_data)}) for {symbol} to detect fluctuations (need at least {MIN_KLINE_FOR_FLUCTUATION_DETECT}).")
        return {}

    current_kline = kline_data[-1]
    previous_kline = kline_data[-2]

    if not all(k in current_kline for k in ["close", "timestamp"]) or \
       not all(k in previous_kline for k in ["close", "timestamp"]):
        log.warning(f"Fluctuation detection for {symbol}: 'close' or 'timestamp' missing in kline data.")
        return {}

    reference_price = previous_kline["close"]
    if reference_price is None or reference_price == 0:
        log.debug(f"Fluctuation detection for {symbol}: Reference price (previous close) is 0 or None. Skipping.")
        return {}

    current_close = current_kline["close"]
    if current_close is None:
        log.debug(f"Fluctuation detection for {symbol}: Current close price is None. Skipping.")
        return {}

    price_change_actual = current_close - reference_price

    # Assuming threshold_percentage is an absolute price change threshold as per original user code's logic
    if abs(price_change_actual) >= threshold_percentage:
        fluctuation_type = "上涨" if price_change_actual > 0 else "下跌"

        percentage_for_reporting = (price_change_actual / reference_price) * 100 if reference_price else 0

        return {
            "symbol": symbol,
            "timestamp": current_kline["timestamp"],
            "type": fluctuation_type,
            "price_change_actual": f"{price_change_actual:.2f}", # Corrected key to match main.py
            "percentage_change": f"{percentage_for_reporting:.2f}%", # Corrected key to match main.py
            "current_close": current_kline["close"],
            "previous_close": previous_kline["close"], # Corrected key to match main.py
            "interval_start": datetime.datetime.fromtimestamp(previous_kline['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
            "interval_end": datetime.datetime.fromtimestamp(current_kline['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        }
    return {}


if __name__ == '__main__':
    # Basic test for data_fetcher
    log.setLevel(logging.DEBUG) # Enable debug level for testing this module

    try:
        from trading_framework.config import PROXIES as test_proxies, HEADERS as test_headers, YAHOO_FINANCE_SYMBOLS as test_symbols
        session.proxies = test_proxies
        session.headers.update(test_headers)
        log.info("Successfully loaded PROXIES and HEADERS from local config.py for testing.")

        test_symbol = "AAPL"
        if test_symbols:
            test_symbol = list(test_symbols.keys())[0]
            log.info(f"Using symbol '{test_symbol}' from config for testing.")


        log.info(f"--- Testing fetch_yahoo_chart_data for {test_symbol} ---")
        chart_data_result = fetch_yahoo_chart_data(test_symbol, "15m", "5d")

        if chart_data_result:
            log.info(f"Successfully fetched chart data for {test_symbol}. Keys: {list(chart_data_result.keys())}")
            if "meta" in chart_data_result:
                log.info(f"Meta: {chart_data_result['meta']}")

            log.info(f"\n--- Testing parse_kline_data for {test_symbol} ---")
            klines = parse_kline_data(chart_data_result)
            if klines:
                log.info(f"Successfully parsed {len(klines)} K-lines for {test_symbol}.")
                log.info(f"First K-line: {klines[0]}")
                log.info(f"Last K-line: {klines[-1]}")

                log.info(f"\n--- Testing detect_abnormal_fluctuations for {test_symbol} ---")
                test_fluctuation_threshold = 0.01
                if test_symbols and test_symbol in test_symbols:
                     test_fluctuation_threshold = test_symbols[test_symbol]
                     log.info(f"Using fluctuation threshold from config for {test_symbol}: {test_fluctuation_threshold}")
                else:
                     log.info(f"Using default small fluctuation threshold for {test_symbol}: {test_fluctuation_threshold}")

                anomaly = detect_abnormal_fluctuations(test_symbol, klines, threshold_percentage=test_fluctuation_threshold)
                if anomaly:
                    log.info(f"Abnormal fluctuation DETECTED for {test_symbol}: {anomaly}")
                else:
                    log.info(f"No abnormal fluctuation detected for {test_symbol} with threshold {test_fluctuation_threshold}.")
            else:
                log.error(f"Failed to parse K-lines for {test_symbol} from fetched data.")
        else:
            log.error(f"Failed to fetch chart data for {test_symbol}. Cannot test parsing or fluctuation detection.")

    except ImportError:
        log.warning("Could not import PROXIES/HEADERS from config.py for data_fetcher self-test. API calls may fail if not configured globally.")
        log.warning("Skipping live API tests in data_fetcher.py's __main__ block.")
    except Exception as e:
        log.error(f"An error occurred during data_fetcher self-test: {e}", exc_info=True)

    log.info("--- data_fetcher.py self-test complete ---")
