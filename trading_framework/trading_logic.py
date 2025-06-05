import pandas as pd
import logging
from typing import List, Dict, Any

# Assuming these modules are in the same directory or installed package
from . import indicators as ind # Use relative import if part of a package
from . import signals # Use relative import
from .config import INDICATOR_PARAMS, ACTIVE_INDICATORS # Use relative import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Trading Constants ---
ENTER_LONG = "ENTER_LONG"
ENTER_SHORT = "ENTER_SHORT"
HOLD = "HOLD"

def get_consensus_signal(ohlcv_df: pd.DataFrame) -> str:
    """
    Calculates all active indicators, generates signals for each,
    and then determines a consensus signal based on a majority vote.

    Args:
        ohlcv_df (pd.DataFrame): DataFrame with OHLCV data.
                                 It's expected to be modified in place
                                 by adding indicator columns.

    Returns:
        str: The consensus trading signal (ENTER_LONG, ENTER_SHORT, HOLD).
    """
    if ohlcv_df.empty:
        logging.warning("Consensus: OHLCV DataFrame is empty.")
        return HOLD

    # Make a copy to avoid modifying the original DataFrame passed to this function
    # if it's used elsewhere, though indicators.py functions modify in-place.
    # For safety, let's work with a copy for indicator calculations if they are not already present.
    # However, the design expects indicators to be added *before* calling signal functions.
    # Let's ensure indicators are present first.

    processed_df = ohlcv_df.copy()

    # 1. Add all active indicators to the DataFrame IF NOT ALREADY PRESENT
    # This loop ensures all necessary indicator columns are present.
    # It avoids recalculating if columns (e.g. from test setup or previous step) already exist.
    for indicator_config in ACTIVE_INDICATORS:
        indicator_name = indicator_config["name"]
        params_key = indicator_config["params_key"]
        params = INDICATOR_PARAMS.get(params_key, {})

        # Determine expected column name(s) to check if they exist
        # This needs to be consistent with how indicators.py names them.
        # This is a simplified check; some indicators create multiple columns.
        # For now, check a primary column. A more robust check would list all expected columns.
        expected_col_name = ""
        col_prefix_cfg = params.get("col_prefix", indicator_name.upper()) # Default prefix from config
        length_cfg = params.get("length")

        if indicator_name == "macd":
            expected_col_name = f"{col_prefix_cfg}_{params.get('fast')}_{params.get('slow')}_{params.get('signal')}"
        elif indicator_name == "bollinger_bands":
            expected_col_name = f"{col_prefix_cfg}M_{length_cfg}_{params.get('std', 2.0):.1f}" # Middle band
        elif indicator_name == "stochastic_oscillator":
            expected_col_name = f"{col_prefix_cfg}k_{params.get('k')}_{params.get('d')}_{params.get('smooth_k')}"
        elif indicator_name in ["obv", "vwap"]: # These often use just the prefix or a direct name
            expected_col_name = col_prefix_cfg
        elif length_cfg is not None: # Common case for SMA, EMA, RSI, CCI, ATR
            expected_col_name = f"{col_prefix_cfg}_{length_cfg}"
        else: # Default for indicators without length, or simple names (should be rare with current set)
            expected_col_name = col_prefix_cfg

        # If the primary expected column for this indicator is NOT in the DataFrame, then calculate it.
        if expected_col_name not in processed_df.columns:
            add_indicator_func_name = f"add_{indicator_name}"
            if hasattr(ind, add_indicator_func_name):
                add_indicator_func = getattr(ind, add_indicator_func_name)
                logging.debug(f"Consensus: Column {expected_col_name} not found. Applying indicator {add_indicator_func_name} with params {params}")
                try:
                    processed_df = add_indicator_func(processed_df, **params)
                except Exception as e:
                    logging.error(f"Consensus: Error applying indicator {add_indicator_func_name}: {e}", exc_info=True)
            else:
                logging.warning(f"Consensus: Indicator function {add_indicator_func_name} not found in indicators module.")
        else:
            logging.debug(f"Consensus: Indicator column {expected_col_name} (for {indicator_name}) already present. Skipping recalculation.")

    # 2. Generate individual signals
    individual_signals: List[str] = []
    for indicator_config in ACTIVE_INDICATORS:
        indicator_name = indicator_config["name"]
        params_key = indicator_config["params_key"]
        params = INDICATOR_PARAMS.get(params_key, {})

        # Skip SMA and EMA here as they are handled by explicit crossover logic later
        if indicator_name == "sma" or indicator_name == "ema":
            continue

        get_signal_func_name = f"get_{indicator_name}_signal"
        # Correcting typo for stochastic_oscillator
        if indicator_name == "stochastic_oscillator":
            get_signal_func_name = "get_stochastic_signal" # Actual function name in signals.py

        signal_function = None
        if hasattr(signals, get_signal_func_name):
            signal_function = getattr(signals, get_signal_func_name)
        else:
            logging.warning(f"Consensus: Signal function {get_signal_func_name} not found in signals module.")
            individual_signals.append(signals.NEUTRAL) # Count as neutral if function missing
            continue

        signal_args = [processed_df] # First arg is always the DataFrame

        col_prefix = params.get("col_prefix", indicator_name.upper())
        length = params.get("length") # For RSI, CCI, ATR etc.

        if indicator_name == "rsi":
            rsi_col = f"{col_prefix}_{length}"
            signal_args.extend([rsi_col, params.get("rsi_oversold", 30), params.get("rsi_overbought", 70)])
        elif indicator_name == "macd":
            fast = params.get("fast", 12)
            slow = params.get("slow", 26)
            signal = params.get("signal", 9)
            macd_line_col = f"{col_prefix}_{fast}_{slow}_{signal}"
            signal_line_col = f"{col_prefix}s_{fast}_{slow}_{signal}" # Signal line suffix 's'
            signal_args.extend([macd_line_col, signal_line_col])
        elif indicator_name == "bollinger_bands":
            std = params.get("std", 2.0)
            # Ensure length is present for BB
            length_bb = params.get("length", 20) # Default length if not in params, consistent with indicators.py
            lower_col = f"{col_prefix}L_{length_bb}_{std:.1f}"
            upper_col = f"{col_prefix}U_{length_bb}_{std:.1f}"
            middle_col = f"{col_prefix}M_{length_bb}_{std:.1f}"
            signal_args.extend([params.get("close_col", "close"), lower_col, upper_col, middle_col])
        elif indicator_name == "stochastic_oscillator":
            k = params.get("k", 14)
            d = params.get("d", 3)
            smooth_k = params.get("smooth_k",3)
            k_col = f"{col_prefix}k_{k}_{d}_{smooth_k}"
            d_col = f"{col_prefix}d_{k}_{d}_{smooth_k}"
            signal_args.extend([k_col, d_col, params.get("oversold_k", 20), params.get("overbought_k", 80)])
        elif indicator_name == "cci":
            cci_col = f"{col_prefix}_{length}"
            signal_args.extend([cci_col, params.get("cci_oversold", -100), params.get("cci_overbought", 100)])
        elif indicator_name == "obv":
            obv_col = col_prefix # OBV default name is just 'OBV'
            signal_args.extend([obv_col, params.get("obv_sma_len", 10)])
        elif indicator_name == "vwap":
            vwap_col = col_prefix # VWAP default name is 'VWAP'
            signal_args.extend([params.get("close_col", "close"), vwap_col])
        elif indicator_name == "atr":
            atr_col = f"{col_prefix}_{length}"
            signal_args.append(atr_col)
        else:
            pass

        try:
            current_signal = signal_function(*signal_args)
            individual_signals.append(current_signal)
            logging.debug(f"Consensus: Indicator {indicator_name} ({params_key}) -> Signal: {current_signal}")
        except Exception as e:
            logging.error(f"Consensus: Error generating signal for {indicator_name} ({params_key}): {e}", exc_info=True)
            individual_signals.append(signals.NEUTRAL)


    # Handle SMA Crossover explicitly
    if "sma_short" in INDICATOR_PARAMS and "sma_long" in INDICATOR_PARAMS:
        short_params = INDICATOR_PARAMS["sma_short"]
        long_params = INDICATOR_PARAMS["sma_long"]
        short_sma_col = f"{short_params.get('col_prefix', 'SMA')}_{short_params.get('length')}"
        long_sma_col = f"{long_params.get('col_prefix', 'SMA')}_{long_params.get('length')}"

        # Ensure these columns are actually in processed_df. If not, add them.
        # This check is important if the main indicator loop above was modified or if DF comes externally.
        if short_sma_col not in processed_df.columns and hasattr(ind, "add_sma"):
             logging.debug(f"SMA Crossover: Short SMA column '{short_sma_col}' not found. Applying SMA indicator.")
             processed_df = ind.add_sma(processed_df, **short_params)
        if long_sma_col not in processed_df.columns and hasattr(ind, "add_sma"):
             logging.debug(f"SMA Crossover: Long SMA column '{long_sma_col}' not found. Applying SMA indicator.")
             processed_df = ind.add_sma(processed_df, **long_params)

        if hasattr(signals, "get_sma_signal"): # This is the correct signal function name
            sma_crossover_signal_func = getattr(signals, "get_sma_signal")
            try:
                sma_cross_sig = sma_crossover_signal_func(processed_df, short_sma_col, long_sma_col)
                individual_signals.append(sma_cross_sig)
                logging.debug(f"Consensus: SMA Crossover ({short_sma_col} vs {long_sma_col}) -> Signal: {sma_cross_sig}")
            except Exception as e:
                logging.error(f"Consensus: Error generating SMA Crossover signal: {e}", exc_info=True)
                individual_signals.append(signals.NEUTRAL)
        else:
             individual_signals.append(signals.NEUTRAL)

    # Handle EMA Crossover explicitly
    if "ema_short" in INDICATOR_PARAMS and "ema_long" in INDICATOR_PARAMS:
        short_params = INDICATOR_PARAMS["ema_short"]
        long_params = INDICATOR_PARAMS["ema_long"]
        short_ema_col = f"{short_params.get('col_prefix', 'EMA')}_{short_params.get('length')}"
        long_ema_col = f"{long_params.get('col_prefix', 'EMA')}_{long_params.get('length')}"

        if short_ema_col not in processed_df.columns and hasattr(ind, "add_ema"):
             logging.debug(f"EMA Crossover: Short EMA column '{short_ema_col}' not found. Applying EMA indicator.")
             processed_df = ind.add_ema(processed_df, **short_params)
        if long_ema_col not in processed_df.columns and hasattr(ind, "add_ema"):
             logging.debug(f"EMA Crossover: Long EMA column '{long_ema_col}' not found. Applying EMA indicator.")
             processed_df = ind.add_ema(processed_df, **long_params)

        if hasattr(signals, "get_ema_signal"): # Correct signal function name
            ema_crossover_signal_func = getattr(signals, "get_ema_signal")
            try:
                ema_cross_sig = ema_crossover_signal_func(processed_df, short_ema_col, long_ema_col)
                individual_signals.append(ema_cross_sig)
                logging.debug(f"Consensus: EMA Crossover ({short_ema_col} vs {long_ema_col}) -> Signal: {ema_cross_sig}")
            except Exception as e:
                logging.error(f"Consensus: Error generating EMA Crossover signal: {e}", exc_info=True)
                individual_signals.append(signals.NEUTRAL)
        else:
            individual_signals.append(signals.NEUTRAL)


    # 3. Tally signals
    reversal_up_votes = individual_signals.count(signals.REVERSAL_UP)
    reversal_down_votes = individual_signals.count(signals.REVERSAL_DOWN)
    neutral_votes = individual_signals.count(signals.NEUTRAL)

    total_potential_votes = len(individual_signals)

    logging.info(f"Consensus Voting: UP={reversal_up_votes}, DOWN={reversal_down_votes}, NEUTRAL={neutral_votes} (out of {total_potential_votes} potential signals)")

    if total_potential_votes == 0:
        logging.warning("Consensus: No signals were generated to vote on.")
        return HOLD

    # Majority vote logic (more than half)
    if reversal_up_votes > total_potential_votes / 2:
        logging.info(f"Consensus: ENTER_LONG signal based on {reversal_up_votes}/{total_potential_votes} UP votes.")
        return ENTER_LONG
    elif reversal_down_votes > total_potential_votes / 2:
        logging.info(f"Consensus: ENTER_SHORT signal based on {reversal_down_votes}/{total_potential_votes} DOWN votes.")
        return ENTER_SHORT
    else:
        logging.info(f"Consensus: HOLD signal. UP votes: {reversal_up_votes}, DOWN votes: {reversal_down_votes}. Threshold not met for {total_potential_votes} signals.")
        return HOLD

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)

    timestamps = pd.to_datetime([f'2023-01-{i:02d}' for i in range(1, 31)] +
                                [f'2023-02-{i:02d}' for i in range(1, 29)] +
                                [f'2023-03-{i:02d}' for i in range(1, 31)])
    data_len = len(timestamps)
    sample_data = {
        'timestamp': timestamps,
        'open': [100 + i*0.1 for i in range(data_len)],
        'high': [105 + i*0.15 for i in range(data_len)],
        'low': [98 + i*0.05 for i in range(data_len)],
        'close': [102 + i*0.12 for i in range(data_len)],
        'volume': [10000 + (i%10)*1000 for i in range(data_len)]
    }
    test_ohlcv_df = pd.DataFrame(sample_data)
    for col_name in ['open', 'high', 'low', 'close', 'volume']:
        test_ohlcv_df[col_name] = test_ohlcv_df[col_name].astype(float)
    test_ohlcv_df.set_index('timestamp', inplace=True)

    # --- Manually add all columns that would be created by indicators.py based on config ---
    # This ensures get_consensus_signal doesn't rely on its internal add_indicator loop for the test's known state.

    # SMA Crossover (SMA_20 > SMA_50 at end)
    sma_short_p = INDICATOR_PARAMS["sma_short"]
    sma_long_p = INDICATOR_PARAMS["sma_long"]
    test_ohlcv_df[f"{sma_short_p['col_prefix']}_{sma_short_p['length']}"] = ind.ta.sma(test_ohlcv_df['close'], length=sma_short_p['length'])
    test_ohlcv_df[f"{sma_long_p['col_prefix']}_{sma_long_p['length']}"] = ind.ta.sma(test_ohlcv_df['close'], length=sma_long_p['length'])
    if data_len > sma_long_p['length']:
        test_ohlcv_df.loc[test_ohlcv_df.index[-2], f"{sma_short_p['col_prefix']}_{sma_short_p['length']}"] = test_ohlcv_df[f"{sma_long_p['col_prefix']}_{sma_long_p['length']}"].iloc[-2] - 0.1
        test_ohlcv_df.loc[test_ohlcv_df.index[-1], f"{sma_short_p['col_prefix']}_{sma_short_p['length']}"] = test_ohlcv_df[f"{sma_long_p['col_prefix']}_{sma_long_p['length']}"].iloc[-1] + 0.1

    # EMA Crossover (EMA_12 > EMA_26 at end)
    ema_short_p = INDICATOR_PARAMS["ema_short"]
    ema_long_p = INDICATOR_PARAMS["ema_long"]
    test_ohlcv_df[f"{ema_short_p['col_prefix']}_{ema_short_p['length']}"] = ind.ta.ema(test_ohlcv_df['close'], length=ema_short_p['length'])
    test_ohlcv_df[f"{ema_long_p['col_prefix']}_{ema_long_p['length']}"] = ind.ta.ema(test_ohlcv_df['close'], length=ema_long_p['length'])
    if data_len > ema_long_p['length']:
        test_ohlcv_df.loc[test_ohlcv_df.index[-2], f"{ema_short_p['col_prefix']}_{ema_short_p['length']}"] = test_ohlcv_df[f"{ema_long_p['col_prefix']}_{ema_long_p['length']}"].iloc[-2] - 0.1
        test_ohlcv_df.loc[test_ohlcv_df.index[-1], f"{ema_short_p['col_prefix']}_{ema_short_p['length']}"] = test_ohlcv_df[f"{ema_long_p['col_prefix']}_{ema_long_p['length']}"].iloc[-1] + 0.1

    # RSI
    rsi_p = INDICATOR_PARAMS['rsi']
    rsi_col = f"{rsi_p['col_prefix']}_{rsi_p['length']}"
    test_ohlcv_df[rsi_col] = ind.ta.rsi(test_ohlcv_df['close'], length=rsi_p['length'])
    if data_len > rsi_p['length']:
        test_ohlcv_df.loc[test_ohlcv_df.index[-2], rsi_col] = 28.0
        test_ohlcv_df.loc[test_ohlcv_df.index[-1], rsi_col] = 32.0

    # MACD
    macd_p = INDICATOR_PARAMS['macd']
    macd_full_df = ind.ta.macd(test_ohlcv_df['close'], fast=macd_p['fast'], slow=macd_p['slow'], signal=macd_p['signal'])
    if macd_full_df is not None:
        test_ohlcv_df[f"{macd_p['col_prefix']}_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = macd_full_df[f"MACD_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"]
        test_ohlcv_df[f"{macd_p['col_prefix']}s_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = macd_full_df[f"MACDs_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"]
        if data_len > macd_p['slow']:
            test_ohlcv_df.loc[test_ohlcv_df.index[-2], f"{macd_p['col_prefix']}_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = -0.05
            test_ohlcv_df.loc[test_ohlcv_df.index[-2], f"{macd_p['col_prefix']}s_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = -0.04
            test_ohlcv_df.loc[test_ohlcv_df.index[-1], f"{macd_p['col_prefix']}_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = 0.01
            test_ohlcv_df.loc[test_ohlcv_df.index[-1], f"{macd_p['col_prefix']}s_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = 0.00

    # Bollinger Bands
    bb_p = INDICATOR_PARAMS['bollinger_bands']
    bb_df = ind.ta.bbands(test_ohlcv_df['close'], length=bb_p['length'], std=bb_p['std'])
    if bb_df is not None:
        for col in bb_df.columns: test_ohlcv_df[col] = bb_df[col]
        if data_len > bb_p['length']:
            # Use a separate column for BB close test to avoid affecting other indicators
            test_ohlcv_df['close_for_bb_test'] = test_ohlcv_df['close'].copy()
            test_ohlcv_df.loc[test_ohlcv_df.index[-2], 'close_for_bb_test'] = test_ohlcv_df[f"BBL_{bb_p['length']}_{bb_p['std']:.1f}"].iloc[-2] - 0.1
            test_ohlcv_df.loc[test_ohlcv_df.index[-1], 'close_for_bb_test'] = test_ohlcv_df[f"BBL_{bb_p['length']}_{bb_p['std']:.1f}"].iloc[-1] + 0.1
            # The signal function needs to be told to use this column.
            # For this test, we manipulate 'close' directly. Ensure BBL is not NaN first.
            bbl_col = f"BBL_{bb_p['length']}_{bb_p['std']:.1f}"
            if bbl_col in test_ohlcv_df.columns: # Check if BBL column exists
                test_ohlcv_df[bbl_col].fillna(method='bfill', inplace=True)
                test_ohlcv_df[bbl_col].fillna(method='ffill', inplace=True)
                if test_ohlcv_df[bbl_col].isnull().all(): # If all are NaN (e.g. length > data_len)
                     test_ohlcv_df[bbl_col].fillna(test_ohlcv_df['close'].iloc[-1] - 1, inplace=True) # Arbitrary valid fallback

                # Check if iloc[-1], iloc[-2] are valid after fill
                if len(test_ohlcv_df) > 1 and pd.notna(test_ohlcv_df[bbl_col].iloc[-1]) and pd.notna(test_ohlcv_df[bbl_col].iloc[-2]):
                    test_ohlcv_df.loc[test_ohlcv_df.index[-2], 'close'] = test_ohlcv_df[bbl_col].iloc[-2] - 0.1
                    test_ohlcv_df.loc[test_ohlcv_df.index[-1], 'close'] = test_ohlcv_df[bbl_col].iloc[-1] + 0.1
                else:
                    logging.debug("BB Test: Not enough data or BBL still NaN at -1,-2 after fill for close manipulation.")
            else:
                logging.warning(f"BB Test: Column {bbl_col} not found in DataFrame for manipulation.")


    # Stochastic
    stoch_p = INDICATOR_PARAMS['stochastic_oscillator']
    stoch_df = ind.ta.stoch(test_ohlcv_df['high'], test_ohlcv_df['low'], test_ohlcv_df['close'], k=stoch_p['k'], d=stoch_p['d'], smooth_k=stoch_p['smooth_k'])
    if stoch_df is not None:
        k_col_test = f"{stoch_p['col_prefix']}k_{stoch_p['k']}_{stoch_p['d']}_{stoch_p['smooth_k']}"
        d_col_test = f"{stoch_p['col_prefix']}d_{stoch_p['k']}_{stoch_p['d']}_{stoch_p['smooth_k']}"
        test_ohlcv_df[k_col_test] = stoch_df.iloc[:,0]
        test_ohlcv_df[d_col_test] = stoch_df.iloc[:,1]
        if data_len > stoch_p['k']:
            test_ohlcv_df.loc[test_ohlcv_df.index[-2], k_col_test] = 18.0
            test_ohlcv_df.loc[test_ohlcv_df.index[-1], k_col_test] = 22.0
            test_ohlcv_df.loc[test_ohlcv_df.index[-2], d_col_test] = 20.0
            test_ohlcv_df.loc[test_ohlcv_df.index[-1], d_col_test] = 21.0

    # CCI
    cci_p = INDICATOR_PARAMS['cci']
    cci_col_name = f"{cci_p['col_prefix']}_{cci_p['length']}"
    test_ohlcv_df[cci_col_name] = ind.ta.cci(test_ohlcv_df['high'], test_ohlcv_df['low'], test_ohlcv_df['close'], length=cci_p['length'])
    if data_len > cci_p['length']:
        test_ohlcv_df.loc[test_ohlcv_df.index[-2], cci_col_name] = -110.0
        test_ohlcv_df.loc[test_ohlcv_df.index[-1], cci_col_name] = -90.0

    # OBV
    obv_p = INDICATOR_PARAMS['obv']
    obv_col_name = obv_p['col_prefix']
    test_ohlcv_df[obv_col_name] = ind.ta.obv(test_ohlcv_df['close'], test_ohlcv_df['volume'])
    # Test setup for OBV signal (from signals.py test)
    if data_len > 11:
        base_obv_val = test_ohlcv_df[obv_col_name].iloc[-12] if data_len >11 else 1000.0 # base on a real prior value
        for i in range(1, 12):
            idx = test_ohlcv_df.index[-i]
            if i == 2: test_ohlcv_df.loc[idx, obv_col_name] = base_obv_val - 5.0
            elif i == 1: test_ohlcv_df.loc[idx, obv_col_name] = base_obv_val + 10.0
            else: test_ohlcv_df.loc[idx, obv_col_name] = base_obv_val

    # VWAP
    vwap_p = INDICATOR_PARAMS['vwap']
    vwap_col_name = vwap_p['col_prefix']
    # Ensure VWAP column exists, fill with a baseline
    # VWAP calculation itself depends on 'close', 'high', 'low', 'volume'.
    # For the test, we first ensure the VWAP column from config is populated (e.g. by indicators.py)
    # Then, we will directly manipulate its values and 'close' for the last two points for a clear test.
    if vwap_col_name not in test_ohlcv_df.columns:
        # If indicators.py didn't add it (e.g. if VWAP wasn't in ACTIVE_INDICATORS for a pre-population step)
        # we add it here with actual calculation, then fill, then override for test.
        test_ohlcv_df[vwap_col_name] = ind.ta.vwap(test_ohlcv_df['high'], test_ohlcv_df['low'], test_ohlcv_df['close'], test_ohlcv_df['volume'])

    # Fill any NaNs in VWAP column that might have occurred from calculation on partial data
    test_ohlcv_df[vwap_col_name].fillna(method='bfill', inplace=True)
    test_ohlcv_df[vwap_col_name].fillna(method='ffill', inplace=True)
    test_ohlcv_df[vwap_col_name].fillna(100.0, inplace=True) # Fill any remaining NaNs with a baseline

    if data_len > 1:
        # Direct manipulation for REVERSAL_UP for VWAP signal
        # This overwrites any previous 'close' column manipulations for the last two rows.
        test_ohlcv_df.loc[test_ohlcv_df.index[-2], 'close'] = 99.9
        test_ohlcv_df.loc[test_ohlcv_df.index[-2], vwap_col_name] = 100.0

        test_ohlcv_df.loc[test_ohlcv_df.index[-1], 'close'] = 100.1
        test_ohlcv_df.loc[test_ohlcv_df.index[-1], vwap_col_name] = 100.0
        # Expected: previous_close (99.9) <= previous_vwap (100.0) -> TRUE
        #           latest_close (100.1) > latest_vwap (100.0) -> TRUE
        # Result: REVERSAL_UP for VWAP
    else:
        logging.debug("VWAP Test: Not enough data for direct manipulation.")


    # ATR (neutral)
    atr_p = INDICATOR_PARAMS['atr']
    test_ohlcv_df[f"{atr_p['col_prefix']}_{atr_p['length']}"] = 1.0


    # Clean up any NaNs from indicator calculations before passing to consensus
    for col in test_ohlcv_df.columns:
        if test_ohlcv_df[col].dtype == 'float64':
            test_ohlcv_df[col].fillna(method='bfill', inplace=True)
            test_ohlcv_df[col].fillna(method='ffill', inplace=True)
            if test_ohlcv_df[col].isnull().any():
                 test_ohlcv_df[col].fillna(0, inplace=True) # Fill remaining with 0


    logging.info("--- Test 1: REVERSAL_UP majority ---")
    # Create a deep copy for the first test to prevent modifications from affecting the second test
    test_df_up_scenario = test_ohlcv_df.copy(deep=True)
    consensus_signal_up = get_consensus_signal(test_df_up_scenario)
    logging.info(f"Consensus Signal (UP test): {consensus_signal_up} (Expected ENTER_LONG or many UP votes)")

    # --- Simulate conditions for REVERSAL_DOWN for some indicators on a fresh copy ---
    test_df_down_scenario = test_ohlcv_df.copy(deep=True) # Use original base + indicators but before UP mods

    # Reverse SMA Crossover
    if data_len > sma_long_p['length']:
        test_df_down_scenario.loc[test_df_down_scenario.index[-2], f"{sma_short_p['col_prefix']}_{sma_short_p['length']}"] = test_df_down_scenario[f"{sma_long_p['col_prefix']}_{sma_long_p['length']}"].iloc[-2] + 0.1
        test_df_down_scenario.loc[test_df_down_scenario.index[-1], f"{sma_short_p['col_prefix']}_{sma_short_p['length']}"] = test_df_down_scenario[f"{sma_long_p['col_prefix']}_{sma_long_p['length']}"].iloc[-1] - 0.1
    # Reverse RSI
    if data_len > rsi_p['length']:
        test_df_down_scenario.loc[test_df_down_scenario.index[-2], rsi_col] = 72.0
        test_df_down_scenario.loc[test_df_down_scenario.index[-1], rsi_col] = 68.0
    # Reverse MACD
    if macd_full_df is not None and data_len > macd_p['slow']:
        test_df_down_scenario.loc[test_df_down_scenario.index[-2], f"{macd_p['col_prefix']}_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = 0.05
        test_df_down_scenario.loc[test_df_down_scenario.index[-2], f"{macd_p['col_prefix']}s_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = 0.04
        test_df_down_scenario.loc[test_df_down_scenario.index[-1], f"{macd_p['col_prefix']}_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = -0.01
        test_df_down_scenario.loc[test_df_down_scenario.index[-1], f"{macd_p['col_prefix']}s_{macd_p['fast']}_{macd_p['slow']}_{macd_p['signal']}"] = 0.00

    # Re-fill NaNs that might have been introduced by .loc assignments if source was NaN
    for col in test_df_down_scenario.columns:
        if test_df_down_scenario[col].dtype == 'float64':
            test_df_down_scenario[col].fillna(method='bfill', inplace=True)
            test_df_down_scenario[col].fillna(method='ffill', inplace=True)
            if test_df_down_scenario[col].isnull().any():
                 test_df_down_scenario[col].fillna(0, inplace=True)


    logging.info("--- Test 2: REVERSAL_DOWN majority (partial reversal for test) ---")
    consensus_signal_down = get_consensus_signal(test_df_down_scenario)
    logging.info(f"Consensus Signal (DOWN test): {consensus_signal_down} (Expect ENTER_SHORT if enough are reversed, or different vote counts)")

    logging.info("--- Trading Logic Test Complete ---")
