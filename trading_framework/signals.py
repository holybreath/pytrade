import pandas as pd
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Signal Constants ---
REVERSAL_UP = "REVERSAL_UP"
REVERSAL_DOWN = "REVERSAL_DOWN"
NEUTRAL = "NEUTRAL"

# --- SMA Signal ---
def get_sma_signal(df: pd.DataFrame, short_sma_col: str, long_sma_col: str) -> str:
    """
    Generates a signal based on SMA crossover.
    REVERSAL_UP: Short SMA crosses above Long SMA.
    REVERSAL_DOWN: Short SMA crosses below Long SMA.
    Assumes df is sorted with the latest data at the end.
    """
    if not all(col in df.columns for col in [short_sma_col, long_sma_col]):
        logging.warning(f"SMA signal: Missing one or both columns: {short_sma_col}, {long_sma_col}")
        return NEUTRAL
    if len(df) < 2:
        return NEUTRAL

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    if pd.isna(latest[short_sma_col]) or pd.isna(latest[long_sma_col]) or \
       pd.isna(previous[short_sma_col]) or pd.isna(previous[long_sma_col]):
        logging.debug(f"SMA signal: NaN values detected for {short_sma_col} or {long_sma_col} in last two periods.")
        return NEUTRAL

    if previous[short_sma_col] <= previous[long_sma_col] and latest[short_sma_col] > latest[long_sma_col]:
        logging.debug(f"SMA REVERSAL_UP: {short_sma_col} ({latest[short_sma_col]:.2f}) crossed above {long_sma_col} ({latest[long_sma_col]:.2f})")
        return REVERSAL_UP
    elif previous[short_sma_col] >= previous[long_sma_col] and latest[short_sma_col] < latest[long_sma_col]:
        logging.debug(f"SMA REVERSAL_DOWN: {short_sma_col} ({latest[short_sma_col]:.2f}) crossed below {long_sma_col} ({latest[long_sma_col]:.2f})")
        return REVERSAL_DOWN
    return NEUTRAL

# --- EMA Signal (similar to SMA) ---
def get_ema_signal(df: pd.DataFrame, short_ema_col: str, long_ema_col: str) -> str:
    """
    Generates a signal based on EMA crossover.
    REVERSAL_UP: Short EMA crosses above Long EMA.
    REVERSAL_DOWN: Short EMA crosses below Long EMA.
    """
    if not all(col in df.columns for col in [short_ema_col, long_ema_col]):
        logging.warning(f"EMA signal: Missing one or both columns: {short_ema_col}, {long_ema_col}")
        return NEUTRAL
    if len(df) < 2:
        return NEUTRAL

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    if pd.isna(latest[short_ema_col]) or pd.isna(latest[long_ema_col]) or \
       pd.isna(previous[short_ema_col]) or pd.isna(previous[long_ema_col]):
        logging.debug(f"EMA signal: NaN values detected for {short_ema_col} or {long_ema_col} in last two periods.")
        return NEUTRAL

    if previous[short_ema_col] <= previous[long_ema_col] and latest[short_ema_col] > latest[long_ema_col]:
        logging.debug(f"EMA REVERSAL_UP: {short_ema_col} ({latest[short_ema_col]:.2f}) crossed above {long_ema_col} ({latest[long_ema_col]:.2f})")
        return REVERSAL_UP
    elif previous[short_ema_col] >= previous[long_ema_col] and latest[short_ema_col] < latest[long_ema_col]:
        logging.debug(f"EMA REVERSAL_DOWN: {short_ema_col} ({latest[short_ema_col]:.2f}) crossed below {long_ema_col} ({latest[long_ema_col]:.2f})")
        return REVERSAL_DOWN
    return NEUTRAL

# --- RSI Signal ---
def get_rsi_signal(df: pd.DataFrame, rsi_col: str, rsi_oversold: int = 30, rsi_overbought: int = 70) -> str:
    """
    Generates a signal based on RSI.
    REVERSAL_UP: RSI was below oversold and crosses back above it.
    REVERSAL_DOWN: RSI was above overbought and crosses back below it.
    """
    if rsi_col not in df.columns:
        logging.warning(f"RSI signal: Missing column: {rsi_col}")
        return NEUTRAL
    if len(df) < 2:
        return NEUTRAL

    latest_rsi = df[rsi_col].iloc[-1]
    previous_rsi = df[rsi_col].iloc[-2]

    if pd.isna(latest_rsi) or pd.isna(previous_rsi):
        logging.debug(f"RSI signal: NaN values detected for {rsi_col} in last two periods.")
        return NEUTRAL

    if previous_rsi <= rsi_oversold and latest_rsi > rsi_oversold:
        logging.debug(f"RSI REVERSAL_UP: {rsi_col} ({latest_rsi:.2f}) crossed above oversold ({rsi_oversold}) from {previous_rsi:.2f}")
        return REVERSAL_UP
    elif previous_rsi >= rsi_overbought and latest_rsi < rsi_overbought:
        logging.debug(f"RSI REVERSAL_DOWN: {rsi_col} ({latest_rsi:.2f}) crossed below overbought ({rsi_overbought}) from {previous_rsi:.2f}")
        return REVERSAL_DOWN
    return NEUTRAL

# --- MACD Signal ---
def get_macd_signal(df: pd.DataFrame, macd_line_col: str, signal_line_col: str) -> str:
    """
    Generates a signal based on MACD line crossing the Signal line.
    REVERSAL_UP: MACD line crosses above Signal line.
    REVERSAL_DOWN: MACD line crosses below Signal line.
    """
    if not all(col in df.columns for col in [macd_line_col, signal_line_col]):
        logging.warning(f"MACD signal: Missing one or both columns: {macd_line_col}, {signal_line_col}")
        return NEUTRAL
    if len(df) < 2:
        return NEUTRAL

    latest_macd = df[macd_line_col].iloc[-1]
    latest_signal = df[signal_line_col].iloc[-1]
    previous_macd = df[macd_line_col].iloc[-2]
    previous_signal = df[signal_line_col].iloc[-2]

    if pd.isna(latest_macd) or pd.isna(latest_signal) or pd.isna(previous_macd) or pd.isna(previous_signal):
        logging.debug(f"MACD signal: NaN values detected for {macd_line_col} or {signal_line_col} in last two periods.")
        return NEUTRAL

    if previous_macd <= previous_signal and latest_macd > latest_signal:
        logging.debug(f"MACD REVERSAL_UP: {macd_line_col} ({latest_macd:.2f}) crossed above {signal_line_col} ({latest_signal:.2f})")
        return REVERSAL_UP
    elif previous_macd >= previous_signal and latest_macd < latest_signal:
        logging.debug(f"MACD REVERSAL_DOWN: {macd_line_col} ({latest_macd:.2f}) crossed below {signal_line_col} ({latest_signal:.2f})")
        return REVERSAL_DOWN
    return NEUTRAL

# --- Bollinger Bands Signal ---
def get_bollinger_bands_signal(df: pd.DataFrame, close_col: str, lower_band_col: str, upper_band_col: str, middle_band_col: str) -> str:
    """
    Generates a signal based on Bollinger Bands.
    REVERSAL_UP: Price crosses below lower band then back above it OR price crosses above middle band from below.
    REVERSAL_DOWN: Price crosses above upper band then back below it OR price crosses below middle band from above.
    """
    if not all(col in df.columns for col in [close_col, lower_band_col, upper_band_col, middle_band_col]):
        logging.warning(f"Bollinger signal: Missing one or more columns: {close_col}, {lower_band_col}, {upper_band_col}, {middle_band_col}")
        return NEUTRAL
    if len(df) < 2:
        return NEUTRAL

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    if pd.isna(latest[close_col]) or pd.isna(latest[lower_band_col]) or pd.isna(latest[upper_band_col]) or \
       pd.isna(previous[close_col]) or pd.isna(previous[lower_band_col]) or pd.isna(previous[upper_band_col]) or \
       pd.isna(latest[middle_band_col]) or pd.isna(previous[middle_band_col]):
        logging.debug("Bollinger signal: NaN values detected in relevant columns for the last two periods.")
        return NEUTRAL

    if previous[close_col] <= previous[lower_band_col] and latest[close_col] > latest[lower_band_col]:
        logging.debug(f"BB REVERSAL_UP: {close_col} ({latest[close_col]:.2f}) crossed above {lower_band_col} ({latest[lower_band_col]:.2f})")
        return REVERSAL_UP
    elif previous[close_col] <= previous[middle_band_col] and latest[close_col] > latest[middle_band_col]:
         logging.debug(f"BB REVERSAL_UP (Mid): {close_col} ({latest[close_col]:.2f}) crossed above {middle_band_col} ({latest[middle_band_col]:.2f})")
         return REVERSAL_UP

    if previous[close_col] >= previous[upper_band_col] and latest[close_col] < latest[upper_band_col]:
        logging.debug(f"BB REVERSAL_DOWN: {close_col} ({latest[close_col]:.2f}) crossed below {upper_band_col} ({latest[upper_band_col]:.2f})")
        return REVERSAL_DOWN
    elif previous[close_col] >= previous[middle_band_col] and latest[close_col] < latest[middle_band_col]:
        logging.debug(f"BB REVERSAL_DOWN (Mid): {close_col} ({latest[close_col]:.2f}) crossed below {middle_band_col} ({latest[middle_band_col]:.2f})")
        return REVERSAL_DOWN

    return NEUTRAL

# --- Stochastic Oscillator Signal ---
def get_stochastic_signal(df: pd.DataFrame, k_col: str, d_col: str, oversold_k: int = 20, overbought_k: int = 80) -> str:
    """
    Generates a signal based on Stochastic Oscillator.
    REVERSAL_UP: %K crosses above %D when %K is in oversold territory OR %K crosses above oversold level.
    REVERSAL_DOWN: %K crosses below %D when %K is in overbought territory OR %K crosses below overbought level.
    """
    if not all(col in df.columns for col in [k_col, d_col]):
        logging.warning(f"Stochastic signal: Missing one or both columns: {k_col}, {d_col}")
        return NEUTRAL
    if len(df) < 2:
        return NEUTRAL

    latest_k = df[k_col].iloc[-1]
    latest_d = df[d_col].iloc[-1]
    previous_k = df[k_col].iloc[-2]
    previous_d = df[d_col].iloc[-2]

    if pd.isna(latest_k) or pd.isna(latest_d) or pd.isna(previous_k) or pd.isna(previous_d):
        logging.debug(f"Stochastic signal: NaN values detected for {k_col} or {d_col} in last two periods.")
        return NEUTRAL

    if (previous_k <= previous_d and latest_k > latest_d and previous_k <= oversold_k) or \
       (previous_k <= oversold_k and latest_k > oversold_k):
        logging.debug(f"Stochastic REVERSAL_UP: %K({latest_k:.2f}) crossed above %D({latest_d:.2f}) or exited oversold({oversold_k})")
        return REVERSAL_UP
    elif (previous_k >= previous_d and latest_k < latest_d and previous_k >= overbought_k) or \
          (previous_k >= overbought_k and latest_k < overbought_k):
        logging.debug(f"Stochastic REVERSAL_DOWN: %K({latest_k:.2f}) crossed below %D({latest_d:.2f}) or exited overbought({overbought_k})")
        return REVERSAL_DOWN
    return NEUTRAL

# --- CCI Signal ---
def get_cci_signal(df: pd.DataFrame, cci_col: str, cci_oversold: int = -100, cci_overbought: int = 100) -> str:
    """
    Generates a signal based on CCI.
    REVERSAL_UP: CCI was below oversold and crosses back above it.
    REVERSAL_DOWN: CCI was above overbought and crosses back below it.
    """
    if cci_col not in df.columns:
        logging.warning(f"CCI signal: Missing column: {cci_col}")
        return NEUTRAL
    if len(df) < 2:
        return NEUTRAL

    latest_cci = df[cci_col].iloc[-1]
    previous_cci = df[cci_col].iloc[-2]

    if pd.isna(latest_cci) or pd.isna(previous_cci):
        logging.debug(f"CCI signal: NaN values detected for {cci_col} in last two periods.")
        return NEUTRAL

    if previous_cci <= cci_oversold and latest_cci > cci_oversold:
        logging.debug(f"CCI REVERSAL_UP: {cci_col} ({latest_cci:.2f}) crossed above oversold ({cci_oversold}) from {previous_cci:.2f}")
        return REVERSAL_UP
    elif previous_cci >= cci_overbought and latest_cci < cci_overbought:
        logging.debug(f"CCI REVERSAL_DOWN: {cci_col} ({latest_cci:.2f}) crossed below overbought ({cci_overbought}) from {previous_cci:.2f}")
        return REVERSAL_DOWN
    return NEUTRAL

# --- OBV Signal ---
def get_obv_signal(df: pd.DataFrame, obv_col: str, obv_sma_len: int = 10) -> str:
    """
    Generates a signal based on OBV crossing its own SMA.
    REVERSAL_UP: OBV crosses above its SMA.
    REVERSAL_DOWN: OBV crosses below its SMA.
    """
    if obv_col not in df.columns:
        logging.warning(f"OBV signal: Missing column: {obv_col}")
        return NEUTRAL

    obv_sma_col = f"{obv_col}_SMA_{obv_sma_len}"
    try:
        # Ensure pandas Series for rolling operation compatibility
        df[obv_sma_col] = pd.Series(df[obv_col]).rolling(window=obv_sma_len, min_periods=obv_sma_len).mean()
    except Exception as e:
        logging.error(f"Error calculating SMA for OBV: {e}")
        return NEUTRAL

    if len(df) < obv_sma_len + 1:
         logging.debug(f"OBV signal: Not enough data for OBV SMA {obv_sma_len}")
         return NEUTRAL

    latest_obv = df[obv_col].iloc[-1]
    latest_obv_sma = df[obv_sma_col].iloc[-1]
    previous_obv = df[obv_col].iloc[-2]
    previous_obv_sma = df[obv_sma_col].iloc[-2]

    if pd.isna(latest_obv) or pd.isna(latest_obv_sma) or pd.isna(previous_obv) or pd.isna(previous_obv_sma):
        logging.debug(f"OBV signal: NaN values in OBV or its SMA for last two periods.")
        return NEUTRAL

    if previous_obv <= previous_obv_sma and latest_obv > latest_obv_sma:
        logging.debug(f"OBV REVERSAL_UP: {obv_col} ({latest_obv:.2f}) crossed above its SMA ({latest_obv_sma:.2f})")
        return REVERSAL_UP
    elif previous_obv >= previous_obv_sma and latest_obv < latest_obv_sma:
        logging.debug(f"OBV REVERSAL_DOWN: {obv_col} ({latest_obv:.2f}) crossed below its SMA ({latest_obv_sma:.2f})")
        return REVERSAL_DOWN

    logging.debug(f"OBV Check: prev_obv={previous_obv:.2f}, prev_sma={previous_obv_sma:.2f}, latest_obv={latest_obv:.2f}, latest_sma={latest_obv_sma:.2f}")
    logging.debug(f"Condition1 (prev_obv <= prev_sma): {previous_obv <= previous_obv_sma}")
    logging.debug(f"Condition2 (latest_obv > latest_sma): {latest_obv > latest_obv_sma}")
    return NEUTRAL

# --- VWAP Signal ---
def get_vwap_signal(df: pd.DataFrame, close_col: str, vwap_col: str) -> str:
    """
    Generates a signal based on Price (Close) crossing VWAP.
    REVERSAL_UP: Close crosses above VWAP.
    REVERSAL_DOWN: Close crosses below VWAP.
    """
    if not all(col in df.columns for col in [close_col, vwap_col]):
        logging.warning(f"VWAP signal: Missing one or both columns: {close_col}, {vwap_col}")
        return NEUTRAL
    if len(df) < 2:
        return NEUTRAL

    latest_close = df[close_col].iloc[-1]
    latest_vwap = df[vwap_col].iloc[-1]
    previous_close = df[close_col].iloc[-2]
    previous_vwap = df[vwap_col].iloc[-2]

    if pd.isna(latest_close) or pd.isna(latest_vwap) or pd.isna(previous_close) or pd.isna(previous_vwap):
        logging.debug(f"VWAP signal: NaN values detected for {close_col} or {vwap_col} in last two periods.")
        return NEUTRAL

    if previous_close <= previous_vwap and latest_close > latest_vwap:
        logging.debug(f"VWAP REVERSAL_UP: {close_col} ({latest_close:.2f}) crossed above {vwap_col} ({latest_vwap:.2f})")
        return REVERSAL_UP
    elif previous_close >= previous_vwap and latest_close < latest_vwap:
        logging.debug(f"VWAP REVERSAL_DOWN: {close_col} ({latest_close:.2f}) crossed below {vwap_col} ({latest_vwap:.2f})")
        return REVERSAL_DOWN
    return NEUTRAL

# --- ATR Signal ---
def get_atr_signal(df: pd.DataFrame, atr_col: str) -> str:
    """ATR is a volatility measure, not a directional reversal signal."""
    if atr_col not in df.columns:
        logging.warning(f"ATR signal: Missing column: {atr_col}")
    return NEUTRAL


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)

    timestamps = pd.to_datetime([f'2023-01-{i:02d}' for i in range(1, 31)] +
                                [f'2023-02-{i:02d}' for i in range(1, 29)] +
                                [f'2023-03-{i:02d}' for i in range(1, 31)])
    data_len = len(timestamps)
    sample_data = {
        'timestamp': timestamps,
        'open': [100 + i*0.1 + 5* (i//30) for i in range(data_len)],
        'high': [105 + i*0.15 + 5* (i//30) for i in range(data_len)],
        'low': [98 + i*0.05 + 5* (i//30) for i in range(data_len)],
        'close': [102 + i*0.12 + 5* (i//30) for i in range(data_len)],
        'volume': [10000 + (i%10)*1000 for i in range(data_len)]
    }
    test_df = pd.DataFrame(sample_data)
    for col_name in ['open', 'high', 'low', 'close', 'volume']: # Renamed 'col' to 'col_name'
        test_df[col_name] = test_df[col_name].astype(float)

    # SMA Crossover
    test_df['SMA_20'] = test_df['close'].rolling(window=20, min_periods=20).mean()
    test_df['SMA_50'] = test_df['close'].rolling(window=50, min_periods=50).mean()
    if data_len > 50:
        # Force a REVERSAL_UP condition
        test_df.loc[test_df.index[-2], 'SMA_20'] = test_df['SMA_50'].iloc[-2] - 0.1 # prev short < prev long
        test_df.loc[test_df.index[-1], 'SMA_20'] = test_df['SMA_50'].iloc[-1] + 0.1 # current short > current long
        # Ensure SMA_50 is not NaN for these points
        test_df.loc[test_df.index[-2], 'SMA_50'] = test_df['SMA_50'].iloc[-3] if pd.isna(test_df['SMA_50'].iloc[-2]) else test_df['SMA_50'].iloc[-2]
        test_df.loc[test_df.index[-1], 'SMA_50'] = test_df['SMA_50'].iloc[-2] if pd.isna(test_df['SMA_50'].iloc[-1]) else test_df['SMA_50'].iloc[-1]


    # RSI
    test_df['RSI_14'] = 0.0 # Default to float
    if data_len > 2:
        test_df.loc[test_df.index[-2], 'RSI_14'] = 28.0 # Was oversold
        test_df.loc[test_df.index[-1], 'RSI_14'] = 32.0 # Crossed back above

    # MACD
    test_df['MACD_12_26_9'] = 0.0
    test_df['MACDs_12_26_9'] = 0.0
    if data_len > 2:
        test_df.loc[test_df.index[-2], 'MACD_12_26_9'] = -0.5
        test_df.loc[test_df.index[-2], 'MACDs_12_26_9'] = -0.4
        test_df.loc[test_df.index[-1], 'MACD_12_26_9'] = 0.1
        test_df.loc[test_df.index[-1], 'MACDs_12_26_9'] = 0.0

    # Bollinger Bands
    test_df['BBL_20_2.0'] = test_df['close'] - 5
    test_df['BBU_20_2.0'] = test_df['close'] + 5
    test_df['BBM_20_2.0'] = test_df['close']
    if data_len > 2:
        # Force close to be a new Series for this manipulation to avoid SettingWithCopyWarning
        close_copy = test_df['close'].copy()
        close_copy.iloc[-2] = test_df['BBL_20_2.0'].iloc[-2] - 1
        close_copy.iloc[-1] = test_df['BBL_20_2.0'].iloc[-1] + 1
        test_df['close_BB_test'] = close_copy # Use a distinct column for this specific test scenario

    # Stochastic
    test_df['STOCHk_14_3_3'] = 0.0
    test_df['STOCHd_14_3_3'] = 0.0
    if data_len > 2:
        test_df.loc[test_df.index[-2], 'STOCHk_14_3_3'] = 18.0
        test_df.loc[test_df.index[-2], 'STOCHd_14_3_3'] = 20.0
        test_df.loc[test_df.index[-1], 'STOCHk_14_3_3'] = 22.0
        test_df.loc[test_df.index[-1], 'STOCHd_14_3_3'] = 21.0

    # CCI
    test_df['CCI_20'] = 0.0
    if data_len > 2:
        test_df.loc[test_df.index[-2], 'CCI_20'] = -110.0
        test_df.loc[test_df.index[-1], 'CCI_20'] = -95.0

    # OBV (and its SMA)
        # OBV (and its SMA)
        # Create a clear pattern for OBV crossover for the last 10 data points + 1 for previous comparison point for SMA
        # Total 11 points needed for SMA(10) comparison at point -2 and -1.
        if data_len > 11:
            base_obv_val = 1000.0
            # Set last 11 OBV values to a controlled sequence
            for i in range(1, 12): # from iloc[-11] to iloc[-1]
                idx = test_df.index[-i]
                if i == 2: # This will be previous_obv (iloc[-2])
                    test_df.loc[idx, 'OBV'] = base_obv_val - 5.0 # e.g. 995
                elif i == 1: # This will be latest_obv (iloc[-1])
                    test_df.loc[idx, 'OBV'] = base_obv_val + 10.0 # e.g. 1010
                else: # Other points in the SMA window
                    test_df.loc[idx, 'OBV'] = base_obv_val
            # Example for sma_len=10:
            # OBV series for previous_obv_sma (window ends at index -2):
            # [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 995] (10 points)
            # previous_obv = 995
            # previous_obv_sma = mean of above = (9*1000 + 995)/10 = 999.5
            # Condition: 995 <= 999.5 (TRUE)

            # OBV series for latest_obv_sma (window ends at index -1):
            # [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 995, 1010] (10 points)
            # latest_obv = 1010
            # latest_obv_sma = mean of above = (8*1000 + 995 + 1010)/10 = (8000 + 2005)/10 = 1000.5
            # Condition: 1010 > 1000.5 (TRUE)
        elif data_len > 2: # Fallback for shorter data
            test_df.loc[test_df.index[-2], 'OBV'] = 100.0
            test_df.loc[test_df.index[-1], 'OBV'] = 200.0
        else: # Not enough data to test OBV
            pass


    # VWAP
    test_df['VWAP'] = test_df['close'] - 0.5
    if data_len > 2:
        # Use a copy for close manipulation for VWAP test
        close_vwap_test = test_df['close'].copy()
        close_vwap_test.iloc[-2] = test_df['VWAP'].iloc[-2] - 0.1
        close_vwap_test.iloc[-1] = test_df['VWAP'].iloc[-1] + 0.1
        test_df['close_VWAP_test'] = close_vwap_test

    test_df['ATR_14'] = 1.0

    logging.info("--- Testing Signal Generation ---")

    # Fill NaNs in key indicator columns with a value that won't trigger signals, BEFORE signal generation
    # This is important because test data manipulation might not cover all NaNs from rolling means
    cols_to_fill = ['SMA_20', 'SMA_50', 'RSI_14', 'MACD_12_26_9', 'MACDs_12_26_9',
                    'BBL_20_2.0', 'BBU_20_2.0', 'BBM_20_2.0',
                    'STOCHk_14_3_3', 'STOCHd_14_3_3', 'CCI_20', 'OBV_SMA_10', 'VWAP', 'OBV']
    for col_fill in cols_to_fill: # Renamed 'col' to 'col_fill'
        if col_fill in test_df.columns:
             # Fill with a value far from typical signal thresholds or a previous valid value
            test_df[col_fill].fillna(method='bfill', inplace=True) # Backfill first
            test_df[col_fill].fillna(method='ffill', inplace=True) # Then ffill for any remaining at start
            if test_df[col_fill].isnull().any(): # If still NaN (e.g. all data was NaN)
                if "SMA" in col_fill or "BBM" in col_fill or "VWAP" in col_fill : test_df[col_fill].fillna(100, inplace=True)
                elif "RSI" in col_fill: test_df[col_fill].fillna(50, inplace=True)
                else: test_df[col_fill].fillna(0, inplace=True)


    sma_signal = get_sma_signal(test_df, 'SMA_20', 'SMA_50')
    logging.info(f"SMA Signal: {sma_signal} (Expected REVERSAL_UP)")

    ema_signal = get_ema_signal(test_df, 'SMA_20', 'SMA_50')
    logging.info(f"EMA Signal (using SMA cols for test): {ema_signal} (Expected REVERSAL_UP)")

    rsi_signal = get_rsi_signal(test_df, 'RSI_14', rsi_oversold=30, rsi_overbought=70)
    logging.info(f"RSI Signal: {rsi_signal} (Expected REVERSAL_UP)")

    macd_signal = get_macd_signal(test_df, 'MACD_12_26_9', 'MACDs_12_26_9')
    logging.info(f"MACD Signal: {macd_signal} (Expected REVERSAL_UP)")

    # Use the dedicated test column for BB signal
    bb_signal = get_bollinger_bands_signal(test_df, 'close_BB_test', 'BBL_20_2.0', 'BBU_20_2.0', 'BBM_20_2.0')
    logging.info(f"Bollinger Bands Signal: {bb_signal} (Expected REVERSAL_UP)")

    stoch_signal = get_stochastic_signal(test_df, 'STOCHk_14_3_3', 'STOCHd_14_3_3', oversold_k=20, overbought_k=80)
    logging.info(f"Stochastic Signal: {stoch_signal} (Expected REVERSAL_UP)")

    cci_signal = get_cci_signal(test_df, 'CCI_20', cci_oversold=-100, cci_overbought=100)
    logging.info(f"CCI Signal: {cci_signal} (Expected REVERSAL_UP)")

    obv_signal = get_obv_signal(test_df, 'OBV', obv_sma_len=10)
    logging.info(f"OBV Signal: {obv_signal} (Expected REVERSAL_UP)")

    # Use the dedicated test column for VWAP signal
    vwap_signal = get_vwap_signal(test_df, 'close_VWAP_test', 'VWAP')
    logging.info(f"VWAP Signal: {vwap_signal} (Expected REVERSAL_UP)")

    atr_signal = get_atr_signal(test_df, 'ATR_14')
    logging.info(f"ATR Signal: {atr_signal} (Expected NEUTRAL)")

    # Test REVERSAL_DOWN for RSI
    test_df_down = test_df.copy() # Create a fresh copy for this specific test
    if data_len > 2:
        test_df_down.loc[test_df_down.index[-2], 'RSI_14'] = 72.0
        test_df_down.loc[test_df_down.index[-1], 'RSI_14'] = 68.0
        rsi_down_signal = get_rsi_signal(test_df_down, 'RSI_14', rsi_oversold=30, rsi_overbought=70)
        logging.info(f"RSI Signal (Down Test): {rsi_down_signal} (Expected REVERSAL_DOWN)")

    logging.info("--- Signal Generation Test Complete ---")
