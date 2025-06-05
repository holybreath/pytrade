# trading_framework/config.py
import logging # Added for context logging in case of direct execution or import issues

log = logging.getLogger(__name__)

# --- API Access Configuration ---
# It is CRUCIAL to configure HEADERS correctly, especially User-Agent and Cookie,
# for reliable access to Yahoo Finance API.
# Cookie is particularly important and tends to expire. If you encounter 401/403/429 errors,
# refresh your Cookie from a browser session with Yahoo Finance.

PROXIES = {
    # Example: If you are using a proxy that requires authentication.
    # "http": "http://user:pass@host:port/",
    # "https": "http://user:pass@host:port/",
    # If your proxy is local and needs no auth (like Clash default):
    # "http": "http://127.0.0.1:7890",
    # "https": "socks5://127.0.0.1:7890", # Or http://127.0.0.1:7890 if it handles HTTPS too
}
if not PROXIES: # Add a log if empty, as user might need it.
    log.debug("PROXIES dictionary is empty. Ensure this is intended if a proxy is required.")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", # Example User-Agent
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br", # Removed zstd as it can sometimes cause issues if not handled well by requests/server
    "Accept-Language": "en-US,en;q=0.9", # Simplified
    "Cache-Control": "max-age=0",
    # "Cookie": "YOUR_COOKIE_STRING_HERE", # Replace with your actual, valid Cookie from Yahoo Finance. This is ESSENTIAL.
                                            # Example: "A1=d=...; A3=...; A1S=...;"
    "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', # Example
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"', # Example
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}
if not HEADERS.get("Cookie") or "YOUR_COOKIE_STRING_HERE" in HEADERS.get("Cookie",""):
    log.warning("IMPORTANT: Yahoo Finance 'Cookie' in HEADERS is missing or using placeholder. API calls will likely fail or be unreliable. Please update it from your browser.")


# Symbols to monitor and their abnormal fluctuation thresholds (absolute price change)
# Format: "SYMBOL": threshold_for_abnormal_fluctuation (in currency units, e.g., USD)
YAHOO_FINANCE_SYMBOLS = {
    "AAPL": 2.00,       # Apple Inc. - Threshold: $2.00 price change in kline_interval
    # "MSFT": 3.00,     # Microsoft Corp.
    # "GOOG": 10.00,    # Alphabet Inc.
    # "BTC-USD": 500.00,# Bitcoin USD
    # "^GSPC": 20.00    # S&P 500 Index
}
if not YAHOO_FINANCE_SYMBOLS:
    log.warning("YAHOO_FINANCE_SYMBOLS is empty. The main application will not process any symbols.")


# --- Application Behavior Configuration ---
APP_CONFIG = {
    "cycle_interval_minutes": 15,       # How often to run the full trading cycle
    "api_request_delay_seconds": 3,     # Delay BETWEEN API calls for different symbols (to be polite to API)
    "kline_interval": "15m",            # K-line interval to fetch (e.g., "1m", "5m", "15m", "1h", "1d")
    "kline_period": "30d",              # Period of K-line data to fetch (e.g., "7d", "30d", "6mo", "1y")
                                        # Ensure this is long enough for all indicators (e.g., SMA50 needs >50 periods for daily)
    "check_abnormal_fluctuations": True,# Whether to run the fluctuation check (using thresholds from YAHOO_FINANCE_SYMBOLS)
    "min_rows_for_indicators": 60,      # Minimum number of data rows required to attempt signal generation (e.g., for SMA50 + buffer)
}

# --- Technical Indicator Parameters ---
# Define parameters for each indicator type. These are used by `indicators.py` and `trading_logic.py`.
INDICATOR_PARAMS = {
    # Moving Averages
    "sma_short": {"length": 20, "close_col": "close", "col_prefix": "SMA"},
    "sma_long": {"length": 50, "close_col": "close", "col_prefix": "SMA"},
    "ema_short": {"length": 12, "close_col": "close", "col_prefix": "EMA"},
    "ema_long": {"length": 26, "close_col": "close", "col_prefix": "EMA"},

    # Oscillators & Momentum
    "rsi": {"length": 14, "close_col": "close", "col_prefix": "RSI", "rsi_oversold": 30, "rsi_overbought": 70}, # Added thresholds
    "macd": {"fast": 12, "slow": 26, "signal": 9, "close_col": "close", "col_prefix": "MACD"},
    "stochastic_oscillator": {
        "k": 14, "d": 3, "smooth_k": 3,
        "high_col": "high", "low_col": "low", "close_col": "close", "col_prefix": "STOCH",
        "oversold_k": 20, "overbought_k": 80 # Added thresholds
    },
    "cci": {"length": 20, "high_col": "high", "low_col": "low", "close_col": "close", "col_prefix": "CCI", "cci_oversold": -100, "cci_overbought": 100}, # Added thresholds

    # Volume Based
    "obv": {"close_col": "close", "volume_col": "volume", "col_prefix": "OBV", "obv_sma_len": 10}, # Added SMA len for OBV signal
    "vwap": {"high_col": "high", "low_col": "low", "close_col": "close", "volume_col": "volume", "col_prefix": "VWAP"},

    # Volatility
    "bollinger_bands": {"length": 20, "std": 2.0, "close_col": "close", "col_prefix": "BB"},
    "atr": {"length": 14, "high_col": "high", "low_col": "low", "close_col": "close", "col_prefix": "ATR"},
}

# --- Active Indicators for Consensus Vote ---
# List of indicators to be used in the voting mechanism.
# 'name' refers to the suffix of the 'add_<name>' function in `indicators.py` and 'get_<name>_signal' in `signals.py`.
# 'params_key' refers to a key in `INDICATOR_PARAMS` dictionary above.
# SMA and EMA crossovers are handled specially in `trading_logic.py` and contribute one vote each,
# so individual 'sma' or 'ema' entries here are typically skipped by the main voting loop in `trading_logic.py`
# if their purpose is only for crossover.
ACTIVE_INDICATORS = [
    # These entries are for indicators that generate a signal on their own.
    # Crossover signals (SMA, EMA) are derived in trading_logic.py from their respective short/long params.
    {"name": "rsi", "params_key": "rsi"},
    {"name": "macd", "params_key": "macd"},
    {"name": "bollinger_bands", "params_key": "bollinger_bands"},
    {"name": "stochastic_oscillator", "params_key": "stochastic_oscillator"},
    {"name": "cci", "params_key": "cci"},
    {"name": "obv", "params_key": "obv"},
    {"name": "vwap", "params_key": "vwap"},
    {"name": "atr", "params_key": "atr"}, # ATR signal function returns NEUTRAL but is included for completeness

    # The following 'sma' and 'ema' entries are technically not needed here if `trading_logic.py`
    # *only* uses them for crossovers. However, `trading_logic.py` currently iterates `ACTIVE_INDICATORS`
    # to apply indicators (add columns to DataFrame) if they are not already present.
    # So, they are kept here to ensure their data columns are generated by the `add_indicator_func` call
    # if not generated by a prior process. The signal generation part of `trading_logic` then
    # explicitly handles the crossover signals.
    {"name": "sma", "params_key": "sma_short"}, # Ensures SMA_20 column is calculated
    {"name": "sma", "params_key": "sma_long"},  # Ensures SMA_50 column is calculated
    {"name": "ema", "params_key": "ema_short"}, # Ensures EMA_12 column is calculated
    {"name": "ema", "params_key": "ema_long"},  # Ensures EMA_26 column is calculated
]
# Total effective votes in current trading_logic.py:
# 1 (RSI) + 1 (MACD) + 1 (BB) + 1 (Stoch) + 1 (CCI) + 1 (OBV) + 1 (VWAP) + 1 (ATR=Neutral)
# + 1 (SMA Crossover) + 1 (EMA Crossover) = 10 votes.
