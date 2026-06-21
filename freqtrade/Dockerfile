FROM freqtradeorg/freqtrade:stable

# Atualiza o CCXT para a última versão disponível, pois versões
# anteriores têm um bug conhecido no roteamento de URLs autenticadas
# para a Binance Spot Testnet (sandbox mode), causando
# "AuthenticationError: Invalid Api-Key ID" mesmo com credenciais válidas.
# Ref: https://github.com/ccxt/ccxt/issues/27266
USER root
RUN pip install --no-cache-dir --upgrade ccxt
USER ftuser