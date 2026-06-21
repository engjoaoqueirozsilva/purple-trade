FROM freqtradeorg/freqtrade:stable

# Instala dependências extras
RUN pip install --no-cache-dir --upgrade ccxt

# Copia todo o user_data (incluindo config.json e estratégias)
# para dentro da imagem — garante que o config esteja disponível
# mesmo sem volume externo
COPY user_data /freqtrade/user_data