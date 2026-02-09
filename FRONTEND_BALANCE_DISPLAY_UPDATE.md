# Frontend Balance Display Update

## Current Issue
The dashboard shows only a total balance (e.g., "$0") instead of listing individual token balances like:
- 8,000,000 SHARP
- 1,500 USDT
- 30 USDC

## Backend Response Format

The backend already returns individual token balances in this format:

```json
{
  "balances": [
    {
      "exchange": "bitmart",
      "asset": "SHARP",
      "free": 8000000.0,
      "total": 8000000.0,
      "used": 0.0,
      "usd_value": 0
    },
    {
      "exchange": "bitmart",
      "asset": "USDT",
      "free": 1500.0,
      "total": 1500.0,
      "used": 0.0,
      "usd_value": 1500.0
    }
  ],
  "total_usd": 1500.0
}
```

## Frontend Changes Needed

### 1. Update Balance Display Component

Instead of showing only `totalBalance`, display a list of individual tokens:

```jsx
// Current (shows only total):
<div>Balance: ${totalBalance}</div>

// New (shows individual tokens):
<div>
  <h3>Balance</h3>
  {balances.length > 0 ? (
    <ul>
      {balances.map((balance) => (
        <li key={`${balance.exchange}-${balance.asset}`}>
          {balance.total.toLocaleString()} {balance.asset}
          {balance.used > 0 && (
            <span className="text-gray-500">
              ({balance.free.toLocaleString()} available)
            </span>
          )}
        </li>
      ))}
    </ul>
  ) : (
    <p>No balances found</p>
  )}
  <div className="mt-2 text-sm text-gray-600">
    Total USD: ${totalUsd.toFixed(2)}
  </div>
</div>
```

### 2. Format Numbers Properly

Use `toLocaleString()` to format large numbers:
- `8000000` → `8,000,000`
- `1500.5` → `1,500.5`

### 3. Filter Zero Balances

The backend already filters out zero balances, but frontend should also handle this:

```jsx
const nonZeroBalances = balances.filter(b => b.total > 0);
```

### 4. Group by Exchange (Optional)

If multiple exchanges, group tokens by exchange:

```jsx
const balancesByExchange = balances.reduce((acc, balance) => {
  if (!acc[balance.exchange]) {
    acc[balance.exchange] = [];
  }
  acc[balance.exchange].push(balance);
  return acc;
}, {});

// Then render:
{Object.entries(balancesByExchange).map(([exchange, tokens]) => (
  <div key={exchange}>
    <h4>{exchange.toUpperCase()}</h4>
    <ul>
      {tokens.map(token => (
        <li>{token.total.toLocaleString()} {token.asset}</li>
      ))}
    </ul>
  </div>
))}
```

## API Endpoints

The frontend should call:
- `GET /api/clients/portfolio?wallet_address=0x...` - Returns `balances` array
- `GET /api/clients/balances?wallet_address=0x...` - Returns `balances` array directly
- `GET /api/exchange/dashboard/{account}` - Returns `balance.balances` array

## Example Response

```json
{
  "balances": [
    {"exchange": "bitmart", "asset": "SHARP", "total": 8000000, "free": 8000000, "used": 0, "usd_value": 0},
    {"exchange": "bitmart", "asset": "USDT", "total": 1500, "free": 1500, "used": 0, "usd_value": 1500},
    {"exchange": "bitmart", "asset": "USDC", "total": 30, "free": 30, "used": 0, "usd_value": 30}
  ],
  "total_usd": 1530.0
}
```

## Implementation Priority

1. **High**: Display individual token balances instead of just total
2. **Medium**: Format numbers with commas (8,000,000 instead of 8000000)
3. **Low**: Group by exchange if multiple exchanges
4. **Low**: Show "available" vs "total" if tokens are in orders
