"""
PurpleMomentumScalp — Estratégia agressiva para testes A/B

Objetivo:
- Estratégia mais agressiva
- Maior frequência de trades
- Capturar movimentos curtos
- Mais exposição ao mercado
- Ideal para comparação com PurpleRSIEMAv2

Características:
- Timeframe rápido
- Entradas mais permissivas
- ROI mais agressivo
- Stop menor
- Mais trades
- Maior risco

ATENÇÃO:
Essa estratégia tende a:
- operar muito mais
- sofrer mais em lateralização
- aumentar drawdown
- exigir monitoramento maior

USAR APENAS:
- paper trading
- testnet
- valores pequenos inicialmente
"""

from freqtrade.strategy import (
    IStrategy,
    DecimalParameter,
    IntParameter,
)

from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class PurpleMomentumScalp(IStrategy):

    INTERFACE_VERSION = 3

    # =========================================================
    # TIMEFRAME
    # =========================================================
    timeframe = "3m"

    can_short = False

    startup_candle_count = 200

    process_only_new_candles = True

    # =========================================================
    # RISCO
    # =========================================================
    stoploss = -0.03

    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.015
    trailing_only_offset_is_reached = True

    # =========================================================
    # ROI (mais agressivo)
    # =========================================================
    minimal_roi = {
        "0": 0.03,
        "15": 0.02,
        "30": 0.01,
        "60": 0
    }

    # =========================================================
    # HYPEROPT
    # =========================================================
    rsi_period = IntParameter(
        low=7,
        high=14,
        default=9,
        space="buy"
    )

    rsi_buy_threshold = DecimalParameter(
        30.0,
        50.0,
        default=42.0,
        decimals=1,
        space="buy"
    )

    rsi_sell_threshold = DecimalParameter(
        55.0,
        80.0,
        default=68.0,
        decimals=1,
        space="sell"
    )

    ema_fast = IntParameter(
        low=3,
        high=10,
        default=5,
        space="buy"
    )

    ema_slow = IntParameter(
        low=10,
        high=20,
        default=13,
        space="buy"
    )

    # =========================================================
    # ORDERS
    # =========================================================
    order_types = {
        "entry": "market",
        "exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # =========================================================
    # INDICATORS
    # =========================================================
    def populate_indicators(
        self,
        dataframe: DataFrame,
        metadata: dict
    ) -> DataFrame:

        dataframe["rsi"] = ta.RSI(
            dataframe,
            timeperiod=self.rsi_period.value
        )

        dataframe["ema_fast"] = ta.EMA(
            dataframe,
            timeperiod=self.ema_fast.value
        )

        dataframe["ema_slow"] = ta.EMA(
            dataframe,
            timeperiod=self.ema_slow.value
        )

        dataframe["macd"] = ta.MACD(dataframe)["macd"]
        dataframe["macdsignal"] = ta.MACD(dataframe)["macdsignal"]

        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)

        dataframe["volume_mean"] = (
            dataframe["volume"]
            .rolling(10)
            .mean()
        )

        return dataframe

    # =========================================================
    # ENTRY
    # =========================================================
    def populate_entry_trend(
        self,
        dataframe: DataFrame,
        metadata: dict
    ) -> DataFrame:

        dataframe.loc[
            (
                # RSI momentum
                (
                    dataframe["rsi"]
                    < self.rsi_buy_threshold.value
                )

                &

                # EMA bullish
                (
                    dataframe["ema_fast"]
                    > dataframe["ema_slow"]
                )

                &

                # MACD bullish
                (
                    dataframe["macd"]
                    > dataframe["macdsignal"]
                )

                &

                # Mercado com força
                (
                    dataframe["adx"] > 20
                )

                &

                # Volume acima da média
                (
                    dataframe["volume"]
                    > dataframe["volume_mean"]
                )

                &

                (
                    dataframe["volume"] > 0
                )
            ),
            "enter_long",
        ] = 1

        return dataframe

    # =========================================================
    # EXIT
    # =========================================================
    def populate_exit_trend(
        self,
        dataframe: DataFrame,
        metadata: dict
    ) -> DataFrame:

        dataframe.loc[
            (
                # RSI sobrecomprado
                (
                    dataframe["rsi"]
                    > self.rsi_sell_threshold.value
                )

                |

                # Perda de momentum
                (
                    dataframe["macd"]
                    < dataframe["macdsignal"]
                )

                |

                # EMA bearish
                (
                    dataframe["ema_fast"]
                    < dataframe["ema_slow"]
                )
            ),
            "exit_long",
        ] = 1

        return dataframe

    # =========================================================
    # PROTECTIONS
    # =========================================================
    @property
    def protections(self):
        return [

            # Cooldown curto
            {
                "method": "CooldownPeriod",
                "stop_duration_candles": 1
            },

            # Stoploss guard agressivo
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 12,
                "trade_limit": 5,
                "stop_duration_candles": 6,
                "only_per_pair": False
            },

            # Evita avalanche de trades ruins
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 48,
                "trade_limit": 20,
                "stop_duration_candles": 12,
                "max_allowed_drawdown": 0.20
            }
        ]
