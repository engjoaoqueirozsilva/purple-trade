"""
PurpleRSIEMA — Estratégia inicial do Purple Trade

Sinais:
  BUY:  RSI(14) < 35  E  EMA(9) > EMA(21)
  SELL: RSI(14) > 65  OU EMA(9) < EMA(21)

Paper trading / Testnet apenas.
"""

from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from pandas import DataFrame
import talib.abstract as ta


class PurpleRSIEMA(IStrategy):
    """Estratégia RSI + EMA cruzamento — MVP Purple Trade."""

    INTERFACE_VERSION = 3

    # ── Configuração de risco ──────────────────────────────
    stoploss = -0.05          # Stop loss de 5%
    trailing_stop = False
    trailing_stop_positive = 0.02

    timeframe = "5m"

    # ── ROI mínimo ────────────────────────────────────────
    minimal_roi = {
        "0": 0.04,     # Alvo: +4% imediato
        "30": 0.025,   # +2.5% após 30 min
        "60": 0.01,    # +1% após 60 min
        "120": 0,      # Qualquer lucro após 2h
    }

    # ── Parâmetros otimizáveis ────────────────────────────
    rsi_period = IntParameter(low=10, high=20, default=14, space="buy")
    rsi_buy_threshold = DecimalParameter(25.0, 40.0, default=35.0, decimals=1, space="buy")
    rsi_sell_threshold = DecimalParameter(60.0, 75.0, default=65.0, decimals=1, space="sell")
    ema_fast = IntParameter(low=5, high=15, default=9, space="buy")
    ema_slow = IntParameter(low=15, high=30, default=21, space="buy")

    # ── Configuração de ordem ─────────────────────────────
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    can_short = False

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=self.rsi_period.value)
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=self.ema_fast.value)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=self.ema_slow.value)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] < self.rsi_buy_threshold.value) &
                (dataframe["ema_fast"] > dataframe["ema_slow"]) &
                (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] > self.rsi_sell_threshold.value) |
                (dataframe["ema_fast"] < dataframe["ema_slow"])
            ),
            "exit_long",
        ] = 1
        return dataframe
