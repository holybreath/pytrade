import pandas as pd
import pandas_ta as ta
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def add_sma(df: pd.DataFrame, length: int = 20, close_col: str = "close", col_prefix: str = "SMA") -> pd.DataFrame:
    """Adds Simple Moving Average (SMA) to the DataFrame."""
    try:
        df[f'{col_prefix}_{length}'] = ta.sma(df[close_col], length=length)
        logging.debug(f"Calculated {col_prefix}_{length}")
    except Exception as e:
        logging.error(f"Error calculating {col_prefix}_{length}: {e}")
    return df

def add_ema(df: pd.DataFrame, length: int = 20, close_col: str = "close", col_prefix: str = "EMA") -> pd.DataFrame:
    """Adds Exponential Moving Average (EMA) to the DataFrame."""
    try:
        df[f'{col_prefix}_{length}'] = ta.ema(df[close_col], length=length)
        logging.debug(f"Calculated {col_prefix}_{length}")
    except Exception as e:
        logging.error(f"Error calculating {col_prefix}_{length}: {e}")
    return df

def add_rsi(df: pd.DataFrame, length: int = 14, close_col: str = "close", col_prefix: str = "RSI") -> pd.DataFrame:
    """Adds Relative Strength Index (RSI) to the DataFrame."""
    try:
        df[f'{col_prefix}_{length}'] = ta.rsi(df[close_col], length=length)
        logging.debug(f"Calculated {col_prefix}_{length}")
    except Exception as e:
        logging.error(f"Error calculating {col_prefix}_{length}: {e}")
    return df

def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, close_col: str = "close", col_prefix: str = "MACD") -> pd.DataFrame:
    """Adds Moving Average Convergence Divergence (MACD) to the DataFrame."""
    try:
        macd_df = ta.macd(df[close_col], fast=fast, slow=slow, signal=signal)
        if macd_df is not None and not macd_df.empty:
            df[f'{col_prefix}_{fast}_{slow}_{signal}'] = macd_df[f'MACD_{fast}_{slow}_{signal}']
            df[f'{col_prefix}h_{fast}_{slow}_{signal}'] = macd_df[f'MACDh_{fast}_{slow}_{signal}'] # Histogram
            df[f'{col_prefix}s_{fast}_{slow}_{signal}'] = macd_df[f'MACDs_{fast}_{slow}_{signal}'] # Signal Line
            logging.debug(f"Calculated {col_prefix}_{fast}_{slow}_{signal}")
        else:
            logging.warning(f"MACD calculation returned None or empty DataFrame for {col_prefix}_{fast}_{slow}_{signal}")
    except Exception as e:
        logging.error(f"Error calculating {col_prefix}_{fast}_{slow}_{signal}: {e}")
    return df

def add_bollinger_bands(df: pd.DataFrame, length: int = 20, std: float = 2.0, close_col: str = "close", col_prefix: str = "BB") -> pd.DataFrame:
    """Adds Bollinger Bands (BBL, BBM, BBU) to the DataFrame."""
    try:
        bbands_df = ta.bbands(df[close_col], length=length, std=std)
        if bbands_df is not None and not bbands_df.empty:
            df[f'{col_prefix}L_{length}_{std:.1f}'] = bbands_df[f'BBL_{length}_{std:.1f}'] # Lower Band
            df[f'{col_prefix}M_{length}_{std:.1f}'] = bbands_df[f'BBM_{length}_{std:.1f}'] # Middle Band
            df[f'{col_prefix}U_{length}_{std:.1f}'] = bbands_df[f'BBU_{length}_{std:.1f}'] # Upper Band
            logging.debug(f"Calculated Bollinger Bands {length}_{std:.1f}")
        else:
            logging.warning(f"Bollinger Bands calculation returned None or empty DataFrame for {col_prefix}_{length}_{std:.1f}")
    except Exception as e:
        logging.error(f"Error calculating Bollinger Bands {length}_{std:.1f}: {e}")
    return df

def add_stochastic_oscillator(df: pd.DataFrame, k: int = 14, d: int = 3, smooth_k: int = 3, high_col: str = "high", low_col: str = "low", close_col: str = "close", col_prefix: str = "STOCH") -> pd.DataFrame:
    """Adds Stochastic Oscillator (%K, %D) to the DataFrame."""
    try:
        stoch_df = ta.stoch(df[high_col], df[low_col], df[close_col], k=k, d=d, smooth_k=smooth_k)
        if stoch_df is not None and not stoch_df.empty:
            df[f'{col_prefix}k_{k}_{d}_{smooth_k}'] = stoch_df[f'STOCHk_{k}_{d}_{smooth_k}'] # %K
            df[f'{col_prefix}d_{k}_{d}_{smooth_k}'] = stoch_df[f'STOCHd_{k}_{d}_{smooth_k}'] # %D (signal)
            logging.debug(f"Calculated Stochastic Oscillator {k}_{d}_{smooth_k}")
        else:
            logging.warning(f"Stochastic Oscillator calculation returned None or empty DataFrame for {col_prefix}k_{k}_{d}_{smooth_k}")
    except Exception as e:
        logging.error(f"Error calculating Stochastic Oscillator {k}_{d}_{smooth_k}: {e}")
    return df

def add_atr(df: pd.DataFrame, length: int = 14, high_col: str = "high", low_col: str = "low", close_col: str = "close", col_prefix: str = "ATR") -> pd.DataFrame:
    """Adds Average True Range (ATR) to the DataFrame."""
    try:
        df[f'{col_prefix}_{length}'] = ta.atr(df[high_col], df[low_col], df[close_col], length=length)
        logging.debug(f"Calculated {col_prefix}_{length}")
    except Exception as e:
        logging.error(f"Error calculating {col_prefix}_{length}: {e}")
    return df

def add_obv(df: pd.DataFrame, close_col: str = "close", volume_col: str = "volume", col_prefix: str = "OBV") -> pd.DataFrame:
    """Adds On-Balance Volume (OBV) to the DataFrame."""
    try:
        df[col_prefix] = ta.obv(df[close_col], df[volume_col])
        logging.debug(f"Calculated {col_prefix}")
    except Exception as e:
        logging.error(f"Error calculating {col_prefix}: {e}")
    return df

def add_cci(df: pd.DataFrame, length: int = 20, high_col: str = "high", low_col: str = "low", close_col: str = "close", col_prefix: str = "CCI") -> pd.DataFrame:
    """Adds Commodity Channel Index (CCI) to the DataFrame."""
    try:
        df[f'{col_prefix}_{length}'] = ta.cci(df[high_col], df[low_col], df[close_col], length=length)
        logging.debug(f"Calculated {col_prefix}_{length}")
    except Exception as e:
        logging.error(f"Error calculating {col_prefix}_{length}: {e}")
    return df

def add_vwap(df: pd.DataFrame, high_col: str = "high", low_col: str = "low", close_col: str = "close", volume_col: str = "volume", col_prefix: str = "VWAP") -> pd.DataFrame:
    """Adds Volume Weighted Average Price (VWAP) to the DataFrame."""
    try:
        df[col_prefix] = ta.vwap(df[high_col], df[low_col], df[close_col], df[volume_col])
        logging.debug(f"Calculated {col_prefix}")
    except Exception as e:
        logging.error(f"Error calculating {col_prefix}: {e}")
    return df

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG) # Ensure debug logs are visible for testing
    sample_data = {
        'timestamp': pd.to_datetime([f'2023-01-{i:02d}' for i in range(1, 31)] + [f'2023-02-{i:02d}' for i in range(1, 21)]), # 50 days
        'open': [i + 100 + (i*0.1) for i in range(50)],
        'high': [i + 105 + (i*0.15) for i in range(50)],
        'low': [i + 98 + (i*0.05) for i in range(50)],
        'close': [i + 102 + (i*0.12) for i in range(50)],
        'volume': [1000 * (i % 10 + 1) * 100 for i in range(50)]
    }
    ohlcv_df = pd.DataFrame(sample_data)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        ohlcv_df[col] = ohlcv_df[col].astype(float)
    ohlcv_df.set_index('timestamp', inplace=True)

    logging.info("Original DataFrame head:\n%s", ohlcv_df.head().to_string())

    ohlcv_df = add_sma(ohlcv_df, length=5)
    ohlcv_df = add_sma(ohlcv_df, length=10, col_prefix="SMA_alt")
    ohlcv_df = add_ema(ohlcv_df, length=5)
    ohlcv_df = add_rsi(ohlcv_df, length=14)
    ohlcv_df = add_macd(ohlcv_df, fast=8, slow=21, signal=5)
    ohlcv_df = add_bollinger_bands(ohlcv_df, length=10, std=2.0)
    ohlcv_df = add_stochastic_oscillator(ohlcv_df, k=14, d=3, smooth_k=3)
    ohlcv_df = add_atr(ohlcv_df, length=14)
    ohlcv_df = add_obv(ohlcv_df)
    ohlcv_df = add_cci(ohlcv_df, length=10)
    ohlcv_df = add_vwap(ohlcv_df)

    logging.info("\nDataFrame with all indicators (tail):\n%s", ohlcv_df.tail().to_string())

    expected_cols = [
        'SMA_5', 'SMA_alt_10', 'EMA_5', 'RSI_14',
        'MACD_8_21_5', 'MACDh_8_21_5', 'MACDs_8_21_5',
        'BBL_10_2.0', 'BBM_10_2.0', 'BBU_10_2.0',
        'STOCHk_14_3_3', 'STOCHd_14_3_3',
        'ATR_14', 'OBV', 'CCI_10', 'VWAP'
    ]
    all_cols_present = True
    logging.info("\nVerifying column creation and data presence...")
    for col in expected_cols:
        if col not in ohlcv_df.columns:
            logging.error(f"Column '{col}' WAS NOT created.")
            all_cols_present = False
        else:
            # Check for NaNs. Most indicators will have NaNs at the start.
            if ohlcv_df[col].isnull().all():
                logging.warning(f"Column '{col}' created, but ALL values are NaN.")
            else:
                logging.debug(f"Column '{col}' created successfully and contains non-NaN data.")
                # Example: logging.debug(f"Column '{col}' head (non-NaN):\n{ohlcv_df[col].dropna().head().to_string()}")


    if all_cols_present:
        logging.info("All expected indicator columns were created successfully.")
    else:
        logging.error("One or more expected indicator columns were NOT created or are all NaN. Check logs above.")

    logging.info(f"Final DataFrame columns: {ohlcv_df.columns.tolist()}")
