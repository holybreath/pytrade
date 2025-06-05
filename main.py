import pandas as pd
import time
import logging
import datetime

# Assuming 'trading_framework' is a package in the same parent directory or installed
from trading_framework import data_fetcher
from trading_framework import trading_logic
from trading_framework.config import YAHOO_FINANCE_SYMBOLS, APP_CONFIG, PROXIES, HEADERS

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logging.getLogger('trading_framework.data_fetcher').setLevel(logging.INFO)
logging.getLogger('trading_framework.indicators').setLevel(logging.WARNING) # Usually verbose
logging.getLogger('trading_framework.signals').setLevel(logging.WARNING) # Can be verbose
logging.getLogger('trading_framework.trading_logic').setLevel(logging.INFO)


def run_trading_cycle():
    """
    Runs a single cycle of fetching data, analyzing, and getting signals for all symbols.
    """
    current_time_cycle = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"--- Starting Trading Cycle at {current_time_cycle} ---")

    if not YAHOO_FINANCE_SYMBOLS:
        logging.warning("No symbols configured in YAHOO_FINANCE_SYMBOLS. Exiting cycle.")
        return

    # Ensure data_fetcher's session uses the latest PROXIES and HEADERS from config
    # This is now handled within fetch_yahoo_chart_data itself by importing from .config

    for symbol, threshold_value in YAHOO_FINANCE_SYMBOLS.items():
        logging.info(f"Processing symbol: {symbol}")

        kline_interval = APP_CONFIG.get("kline_interval", "15m")
        kline_period = APP_CONFIG.get("kline_period", "30d")

        chart_api_response = data_fetcher.fetch_yahoo_chart_data(symbol, kline_interval, kline_period)

        if not chart_api_response or "timestamp" not in chart_api_response:
            logging.error(f"Failed to fetch valid chart data for {symbol}. Skipping.")
            time.sleep(APP_CONFIG.get("api_request_delay_seconds", 1))
            continue

        short_name = symbol
        try: # Safely get shortName
            short_name = chart_api_response.get('meta', {}).get('shortName', symbol)
            if not short_name: short_name = symbol # Handle empty shortName
        except Exception: pass

        kline_data_list = data_fetcher.parse_kline_data(chart_api_response)

        if not kline_data_list:
            logging.warning(f"No K-line data parsed for {symbol} ({short_name}). Skipping.")
            time.sleep(APP_CONFIG.get("api_request_delay_seconds", 1))
            continue

        ohlcv_df = pd.DataFrame(kline_data_list)
        if 'timestamp' in ohlcv_df.columns:
            ohlcv_df['timestamp'] = pd.to_datetime(ohlcv_df['timestamp'], unit='s')
            ohlcv_df.set_index('timestamp', inplace=True)
        else:
            logging.error(f"Timestamp column missing for {symbol} ({short_name}). Skipping.")
            time.sleep(APP_CONFIG.get("api_request_delay_seconds", 1))
            continue

        min_rows_for_indicators = APP_CONFIG.get("min_rows_for_indicators", 60)
        if len(ohlcv_df) < min_rows_for_indicators:
            logging.warning(f"Insufficient K-line rows for {symbol} ({short_name}): {len(ohlcv_df)} rows, need {min_rows_for_indicators}. Skipping.")
            time.sleep(APP_CONFIG.get("api_request_delay_seconds", 1))
            continue

        logging.debug(f"Fetched {len(ohlcv_df)} K-lines for {symbol} ({short_name}). Last: {ohlcv_df.index[-1]}")

        consensus_signal = trading_logic.get_consensus_signal(ohlcv_df.copy()) # Pass copy to avoid modification issues

        logging.info(f"Symbol: {symbol} ({short_name}) - Consensus Signal: {consensus_signal}")

        if APP_CONFIG.get("check_abnormal_fluctuations", False):
            if len(kline_data_list) >= data_fetcher.MIN_KLINE_FOR_FLUCTUATION_DETECT:
                # The 'threshold_value' from YAHOO_FINANCE_SYMBOLS is used here
                abnormal_details = data_fetcher.detect_abnormal_fluctuations(symbol, kline_data_list, threshold_percentage=threshold_value)
                if abnormal_details:
                    logging.warning(
                        f"[!!! ALERT - Abnormal Fluctuation !!!] {abnormal_details.get('symbol', symbol)} ({short_name}): "
                        f"Price {abnormal_details.get('type', '')} by {abnormal_details.get('price_change_actual', '')} ({abnormal_details.get('percentage_change_calculated', '')}) "
                        f"(from {abnormal_details.get('previous_close', 0.0):.2f} to {abnormal_details.get('current_close', 0.0):.2f}) " # Added default for .2f
                        f"Interval: {abnormal_details.get('interval_start','')} -> {abnormal_details.get('interval_end','')}"
                    )
            else:
                logging.debug(f"Not enough k-line data ({len(kline_data_list)}) for abnormal fluctuation check for {symbol} ({short_name}).")

        time.sleep(APP_CONFIG.get("api_request_delay_seconds", 1))

    logging.info(f"--- Trading Cycle Ended at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")


if __name__ == "__main__":
    logging.info("--- Starting Automated Trading Framework ---")

    if not PROXIES.get("http") and not PROXIES.get("https"):
        logging.info("Proxies are not configured in config.py. This is okay if not needed.")
    if not HEADERS.get("User-Agent"): # User-Agent is generally important
        logging.warning("User-Agent is not configured in config.py. Yahoo Finance requests might fail or be inconsistent.")
    if "Cookie" not in HEADERS.get("Cookie","") and "Crumb" not in HEADERS.get("Cookie",""): # Simplified cookie check
         logging.warning("Cookie might not be fully configured in HEADERS in config.py. This can lead to API issues (e.g., 401, 403, 429).")


    cycle_interval_minutes = APP_CONFIG.get("cycle_interval_minutes", 15)
    logging.info(f"Application will run trading cycle every {cycle_interval_minutes} minutes.")
    logging.info(f"Using K-line interval: {APP_CONFIG.get('kline_interval', '15m')}, period: {APP_CONFIG.get('kline_period', '30d')}")
    logging.info(f"Checking abnormal fluctuations: {APP_CONFIG.get('check_abnormal_fluctuations', False)}")
    logging.info(f"Minimum K-line rows for indicators: {APP_CONFIG.get('min_rows_for_indicators', 60)}")

    while True:
        run_trading_cycle()
        logging.info(f"Waiting for {cycle_interval_minutes} minutes until the next cycle...")
        try:
            time.sleep(cycle_interval_minutes * 60)
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received. Shutting down...")
            break
        except Exception as e:
            logging.error(f"An error occurred during sleep or main loop: {e}", exc_info=True)
            logging.info("Attempting to continue after 1 minute despite error during sleep.")
            time.sleep(60)

    logging.info("--- Automated Trading Framework Shut Down ---")
