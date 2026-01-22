# Trading Bridge

A bridge service that connects Pipe Labs Dashboard to cryptocurrency exchanges via the ccxt library.

## Features

- **Multi-exchange support**: BitMart, Binance, KuCoin, Gate.io, MEXC, Bybit, OKX, and more
- **Account management**: Create and manage multiple trading accounts
- **Real trading**: Place and cancel orders on real exchanges
- **Portfolio tracking**: Get balances across all connected exchanges
- **Market data**: Real-time prices and order books

## API Endpoints

### Accounts
- `POST /accounts/create` - Create a new trading account
- `GET /accounts` - List all accounts
- `GET /accounts/{name}` - Get account details

### Connectors
- `POST /connectors/add` - Add exchange API keys to an account
- `GET /connectors/supported` - List supported exchanges

### Portfolio
- `GET /portfolio?account=xxx` - Get account balances
- `GET /history?account=xxx` - Get trade history

### Orders
- `GET /orders?account=xxx` - Get open orders
- `POST /orders/place` - Place a new order
- `POST /orders/cancel` - Cancel an order

### Market Data
- `GET /market/price?connector=xxx&pair=xxx` - Get current price
- `GET /market/orderbook?connector=xxx&pair=xxx` - Get order book

## Deployment to Railway

1. Create a new GitHub repository and push this code
2. In Railway, create a new project from the GitHub repo
3. Railway will auto-detect the Dockerfile and deploy
4. Copy the deployment URL (e.g., `https://trading-bridge-xxx.up.railway.app`)
5. Update your backend's `HUMMINGBOT_API_URL` env var to this URL

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | Optional API key for securing the bridge | (none) |
| `DEBUG` | Enable debug mode | false |

## Local Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

## Supported Exchanges

- BitMart
- Binance
- KuCoin
- Gate.io
- MEXC
- Bybit
- OKX
- HTX (Huobi)
- Coinbase
- Kraken

## Security Notes

- This service handles sensitive API keys - deploy in a secure environment
- Consider adding API key authentication for production
- Use internal Railway networking when possible
- Never expose exchange API keys in logs
