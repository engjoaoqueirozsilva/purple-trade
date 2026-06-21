# Purple Trade

Dashboard pessoal de gestão de investimentos e automação de trading em criptomoedas.

> ⚠️ **Uso pessoal.** Não é um SaaS. Não é um produto público.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | FastAPI (Python 3.12) |
| Bot | Freqtrade (paper trading / testnet) |
| Infra | Docker + Docker Compose |
| Proxy | Traefik v3 (HTTPS + Basic Auth) |
| DB | PostgreSQL 16 (perfil `full`) |
| Cache | Redis 7 (perfil `full`) |

---

## Estrutura do Projeto

```
purple-trade/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings com pydantic
│   │   ├── routers/             # health, status, balance, trades, logs
│   │   └── services/
│   │       └── freqtrade.py     # Integração com Freqtrade API
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # MetricCard, TradesTable, LogTerminal, Header, BotStatus
│   │   ├── pages/
│   │   │   └── Dashboard.jsx    # Página principal
│   │   ├── hooks/
│   │   │   └── useApi.js        # Hook de fetch com polling
│   │   └── App.jsx
│   ├── Dockerfile               # Build de produção (nginx)
│   ├── Dockerfile.dev           # Dev com hot reload
│   └── nginx.conf
├── freqtrade/
│   ├── strategies/
│   │   └── PurpleRSIEMA.py     # Estratégia RSI + EMA
│   └── user_data/
│       └── config.json          # Config do bot (paper trading)
├── traefik/
│   ├── dynamic/
│   │   └── middlewares.yml      # Basic Auth + headers de segurança
│   └── letsencrypt/             # Certificados ACME (gerados em runtime)
├── docker-compose.yml           # Produção (VPS)
├── docker-compose.local.yml     # Desenvolvimento local
└── .env.example
```

---

## Execução Local

### Pré-requisitos

- Docker >= 24
- Docker Compose v2

### 1. Setup inicial

```bash
git clone <repo> purple-trade
cd purple-trade
cp .env.example .env
```

### 2. Subir o ambiente de desenvolvimento

```bash
docker compose -f docker-compose.local.yml up --build backend frontend -d
```

Acesso:
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Freqtrade API**: http://localhost:8080 (interno)

### 3. Verificar status da API

```bash
curl http://localhost:8000/health
curl http://localhost:8000/status
curl http://localhost:8000/balance
curl http://localhost:8000/trades
curl http://localhost:8000/logs
```

### 4. Dados mockados

No MVP, quando o Freqtrade não está acessível (bot parado), o backend retorna **dados mockados realísticos**. O dashboard exibe um aviso amarelo indicando modo mock.

Para dados reais, inicie o Freqtrade:
```bash
docker compose -f docker-compose.local.yml up freqtrade
```

---

## Deploy em VPS (Produção)

### Pré-requisitos

- VPS Linux (Ubuntu 22.04+)
- Docker + Docker Compose v2 instalados
- Domínio DNS configurado apontando para o IP da VPS
- Porta 80 e 443 abertas no firewall

### 1. Clonar e configurar

```bash
git clone <repo> /opt/purple-trade
cd /opt/purple-trade
cp .env.example .env
```

Editar `.env`:
```bash
DOMAIN=purpletrade.seudominio.com
ACME_EMAIL=voce@seudominio.com
FREQTRADE_USER=freqtrader
FREQTRADE_PASSWORD=uma_senha_forte_aqui
```

### 2. Gerar hash de senha para Basic Auth

```bash
# Instalar htpasswd
sudo apt install apache2-utils -y

# Gerar hash
htpasswd -nb admin suasenha
# Saída: admin:$apr1$xyz...
```

Substituir em `traefik/dynamic/middlewares.yml`:
```yaml
users:
  - "admin:$apr1$SEU_HASH_AQUI"
```

### 3. Permissão do arquivo de certificados

```bash
touch traefik/letsencrypt/acme.json
chmod 600 traefik/letsencrypt/acme.json
```

### 4. Configurar o Freqtrade

Editar `freqtrade/user_data/config.json`:
- Alterar `jwt_secret_key` e `ws_token` para valores únicos e seguros
- Ajustar `dry_run: true` para paper trading (manter no início)
- Para Binance Testnet: adicionar chaves de API testnet

### 5. Subir produção

```bash
docker compose up -d --build
```

Acompanhar logs:
```bash
docker compose logs -f
```

### 6. Acessos em produção

- **Dashboard**: https://purpletrade.seudominio.com (protegido por Basic Auth)
- **API**: https://api.purpletrade.seudominio.com
- **Traefik**: https://traefik.purpletrade.seudominio.com

---

## Configuração do Freqtrade

### Paper Trading (padrão)

O bot roda em modo `dry_run: true` com carteira simulada de $1000 USDT.

### Estratégia PurpleRSIEMA

| Parâmetro | Valor padrão |
|-----------|-------------|
| Timeframe | 5 minutos |
| RSI period | 14 |
| Comprar quando RSI < | 35 |
| Vender quando RSI > | 65 |
| EMA rápida | 9 |
| EMA lenta | 21 |
| Stop loss | -5% |
| Máx trades abertos | 5 |
| Stake por trade | 50 USDT |

### Backtesting

```bash
docker compose run --rm freqtrade backtesting \
  --config /freqtrade/user_data/config.json \
  --strategy PurpleRSIEMA \
  --timerange 20240101-20241231
```

---

## API Reference

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/health` | GET | Health check do serviço |
| `/status` | GET | Status do bot + métricas diárias |
| `/balance` | GET | Saldo atual (live ou mock) |
| `/trades?limit=N` | GET | Últimas N operações |
| `/logs?limit=N` | GET | Últimos N logs do bot |

---

## Ativar PostgreSQL e Redis

Para habilitar banco de dados e cache:

```bash
docker compose --profile full up -d
```

E definir no `.env`:
```bash
POSTGRES_DB=purpletrade
POSTGRES_USER=purple
POSTGRES_PASSWORD=senha_forte_aqui
```

---

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DOMAIN` | Domínio de produção | — |
| `ACME_EMAIL` | E-mail para certificado SSL | — |
| `FREQTRADE_USER` | Usuário da API Freqtrade | `freqtrader` |
| `FREQTRADE_PASSWORD` | Senha da API Freqtrade | `password` |
| `POSTGRES_DB` | Nome do banco | `purpletrade` |
| `POSTGRES_USER` | Usuário do banco | `purple` |
| `POSTGRES_PASSWORD` | Senha do banco | — |

---

## Evolução Futura

- [ ] Integração com Binance real (live trading)
- [ ] Múltiplas estratégias simultâneas
- [ ] Gestão de risco avançada (drawdown limits)
- [ ] Alertas via Telegram
- [ ] Métricas com Prometheus + Grafana
- [ ] Análise de mercado com IA
- [ ] Persistência de histórico no PostgreSQL

---

## Segurança

- Todo acesso externo protegido por Traefik Basic Auth
- HTTPS com Let's Encrypt automático
- Freqtrade não exposto diretamente (apenas via rede interna Docker)
- Nenhuma autenticação complexa no backend (protegido pelo proxy)
- Secrets via variáveis de ambiente (nunca hardcoded)

---

## Licença

Uso pessoal.
