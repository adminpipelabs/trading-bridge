"""
Spot Trading Routes
Manual spot trading UI and API endpoints for BitMart and Coinstore.
Self-contained — does not modify any existing bot logic.
"""
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.database import get_db_session
from app.security import decrypt_credential
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spot", tags=["Spot Trading"])

# ── Simple auth ──────────────────────────────────────────────────────────────

SPOT_PASSWORD = os.getenv("SPOT_TRADING_PASSWORD", "sharp2026")


def _check_auth(request: Request):
    """Simple token auth for spot trading endpoints."""
    auth = request.headers.get("X-Spot-Token", "")
    if auth != SPOT_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── Trade history table (auto-created) ───────────────────────────────────────

def _ensure_history_table():
    """Create spot_trades table if it doesn't exist."""
    db = get_db_session()
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS spot_trades (
                id SERIAL PRIMARY KEY,
                ts TIMESTAMPTZ DEFAULT NOW(),
                exchange VARCHAR(32),
                symbol VARCHAR(32),
                side VARCHAR(8),
                order_type VARCHAR(16),
                amount DOUBLE PRECISION,
                price DOUBLE PRECISION,
                cost DOUBLE PRECISION,
                order_id VARCHAR(64),
                status VARCHAR(16) DEFAULT 'ok',
                error TEXT
            )
        """))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

_ensure_history_table()


def _save_trade(exchange: str, symbol: str, side: str, order_type: str,
                amount: float, price: float, cost: float,
                order_id: str = "", status: str = "ok", error: str = ""):
    """Save a trade to the history table."""
    db = get_db_session()
    try:
        db.execute(text("""
            INSERT INTO spot_trades (exchange, symbol, side, order_type, amount, price, cost, order_id, status, error)
            VALUES (:exchange, :symbol, :side, :order_type, :amount, :price, :cost, :order_id, :status, :error)
        """), {
            "exchange": exchange, "symbol": symbol, "side": side, "order_type": order_type,
            "amount": amount, "price": price, "cost": cost,
            "order_id": order_id, "status": status, "error": error,
        })
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to save trade history: {e}")
    finally:
        db.close()


# ── Helpers: create exchange adapters on-the-fly ─────────────────────────────

async def _get_exchange(exchange_name: str):
    """Create a temporary exchange adapter using DB credentials."""
    db = get_db_session()
    try:
        row = db.execute(text("""
            SELECT ec.api_key_encrypted, ec.api_secret_encrypted, ec.passphrase_encrypted
            FROM exchange_credentials ec
            JOIN clients cl ON cl.id = ec.client_id
            WHERE LOWER(ec.exchange) = :exch
            LIMIT 1
        """), {"exch": exchange_name.lower()}).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"No credentials for {exchange_name}")

        api_key = decrypt_credential(row[0])
        api_secret = decrypt_credential(row[1])
        memo = decrypt_credential(row[2]) if row[2] else ""
    finally:
        db.close()

    proxy_url = os.getenv("QUOTAGUARDSTATIC_URL") or os.getenv("QUOTAGUARD_PROXY_URL")
    if proxy_url and proxy_url.startswith("https://"):
        proxy_url = "http://" + proxy_url[8:]

    if exchange_name.lower() == "bitmart":
        from app.bitmart_adapter import create_bitmart_exchange
        return await create_bitmart_exchange(api_key=api_key, api_secret=api_secret, memo=memo, proxy_url=proxy_url)
    elif exchange_name.lower() == "coinstore":
        from app.coinstore_adapter import create_coinstore_exchange
        return await create_coinstore_exchange(api_key=api_key, api_secret=api_secret, proxy_url=proxy_url)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported exchange: {exchange_name}")


# ── API endpoints ────────────────────────────────────────────────────────────

@router.post("/auth")
async def spot_auth(request: Request):
    """Validate password and return token."""
    body = await request.json()
    pw = body.get("password", "")
    if pw == SPOT_PASSWORD:
        return {"ok": True, "token": SPOT_PASSWORD}
    raise HTTPException(status_code=401, detail="Wrong password")


@router.get("/price")
async def spot_price(exchange: str, symbol: str = "SHARP/USDT", request: Request = None):
    """Get current ticker price."""
    _check_auth(request)
    ex = await _get_exchange(exchange)
    try:
        ticker = await ex.fetch_ticker(symbol)
        return {
            "exchange": exchange,
            "symbol": symbol,
            "last": ticker.get("last", 0),
            "bid": ticker.get("bid", 0),
            "ask": ticker.get("ask", 0),
        }
    finally:
        if hasattr(ex, "close"):
            await ex.close()


@router.get("/balance")
async def spot_balance(exchange: str, request: Request = None):
    """Get spot wallet balances."""
    _check_auth(request)
    ex = await _get_exchange(exchange)
    try:
        bal = await ex.fetch_balance()
        # Return only non-zero balances
        free = {k: v for k, v in bal.get("free", {}).items() if v and float(v) > 0}
        return {"exchange": exchange, "balances": free}
    finally:
        if hasattr(ex, "close"):
            await ex.close()


class SpotOrder(BaseModel):
    exchange: str
    symbol: str = "SHARP/USDT"
    side: str  # buy / sell
    amount: float
    order_type: str = "market"  # market / limit
    price: Optional[float] = None


@router.post("/order")
async def spot_order(order: SpotOrder, request: Request):
    """Place a spot order."""
    _check_auth(request)
    ex = await _get_exchange(order.exchange)
    try:
        if order.order_type == "market":
            if order.side.lower() == "buy":
                result = await ex.create_market_buy_order(order.symbol, order.amount)
            else:
                result = await ex.create_market_sell_order(order.symbol, order.amount)
        else:
            if not order.price:
                raise HTTPException(status_code=400, detail="Price required for limit orders")
            result = await ex.create_limit_order(order.symbol, order.side.lower(), order.amount, order.price)

        logger.info(f"SPOT ORDER: {order.side} {order.amount} {order.symbol} on {order.exchange} → {result.get('id', 'unknown')}")
        _save_trade(
            exchange=order.exchange, symbol=order.symbol, side=order.side,
            order_type=order.order_type, amount=order.amount,
            price=result.get("price", result.get("average", 0)),
            cost=result.get("cost", order.amount * result.get("price", 0)),
            order_id=str(result.get("id", "")), status="ok",
        )
        return {"ok": True, "order": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Spot order failed: {e}")
        _save_trade(
            exchange=order.exchange, symbol=order.symbol, side=order.side,
            order_type=order.order_type, amount=order.amount,
            price=order.price or 0, cost=0, status="error", error=str(e)[:200],
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if hasattr(ex, "close"):
            await ex.close()


@router.get("/history")
async def spot_history(limit: int = 50, request: Request = None):
    """Get recent spot trade history."""
    _check_auth(request)
    db = get_db_session()
    try:
        rows = db.execute(text(
            "SELECT ts, exchange, symbol, side, order_type, amount, price, cost, order_id, status, error "
            "FROM spot_trades ORDER BY ts DESC LIMIT :lim"
        ), {"lim": limit}).fetchall()
        trades = []
        for r in rows:
            trades.append({
                "ts": r[0].isoformat() if r[0] else "",
                "exchange": r[1], "symbol": r[2], "side": r[3],
                "order_type": r[4], "amount": r[5], "price": r[6],
                "cost": r[7], "order_id": r[8], "status": r[9], "error": r[10],
            })
        return {"trades": trades}
    finally:
        db.close()


@router.get("/orderbook")
async def spot_orderbook(exchange: str, symbol: str = "SHARP/USDT", limit: int = 15, request: Request = None):
    """Get orderbook depth."""
    _check_auth(request)
    ex = await _get_exchange(exchange)
    try:
        ob = await ex.fetch_order_book(symbol, limit)
        return {
            "exchange": exchange,
            "symbol": symbol,
            "bids": ob.get("bids", [])[:limit],
            "asks": ob.get("asks", [])[:limit],
        }
    finally:
        if hasattr(ex, "close"):
            await ex.close()


# ── HTML page ────────────────────────────────────────────────────────────────

TRADE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Spot Trading</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: 'Inter', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; }
  .btn { transition: all .15s; }
  .btn:active { transform: scale(0.97); }
  .buy-btn { background: #10b981; }
  .buy-btn:hover { background: #059669; }
  .sell-btn { background: #ef4444; }
  .sell-btn:hover { background: #dc2626; }
  input, select { background: #0f172a; border: 1px solid #334155; color: #e2e8f0; }
  input:focus, select:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,.25); }
  .flash { animation: flash .5s ease-out; }
  @keyframes flash { 0% { background: rgba(59,130,246,.3); } 100% { background: transparent; } }
  #log { scrollbar-width: thin; scrollbar-color: #334155 transparent; }
</style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">

<!-- Login Screen -->
<div id="login-screen" class="card p-8 w-full max-w-sm text-center">
  <h1 class="text-2xl font-bold mb-1">Spot Trading</h1>
  <p class="text-slate-400 text-sm mb-6">Enter password to continue</p>
  <input id="pw" type="password" placeholder="Password" class="w-full px-4 py-3 rounded-xl mb-4 text-center text-lg" onkeydown="if(event.key==='Enter')doLogin()">
  <button onclick="doLogin()" class="btn w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 font-semibold text-white">Log In</button>
  <p id="login-err" class="text-red-400 text-sm mt-3 hidden">Wrong password</p>
</div>

<!-- Trading Screen -->
<div id="trade-screen" class="hidden w-full max-w-lg space-y-4">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <h1 class="text-xl font-bold">Spot Trading</h1>
    <button onclick="doLogout()" class="text-sm text-slate-400 hover:text-white">Logout</button>
  </div>

  <!-- Exchange + Pair -->
  <div class="card p-4 flex gap-3">
    <div class="flex-1">
      <label class="text-xs text-slate-400 block mb-1">Exchange</label>
      <select id="exchange" class="w-full px-3 py-2.5 rounded-xl" onchange="onExchangeChange()">
        <option value="bitmart">BitMart</option>
        <option value="coinstore">Coinstore</option>
      </select>
    </div>
    <div class="flex-1">
      <label class="text-xs text-slate-400 block mb-1">Pair</label>
      <select id="pair" class="w-full px-3 py-2.5 rounded-xl">
        <option value="SHARP/USDT">SHARP / USDT</option>
      </select>
    </div>
  </div>

  <!-- Price + Balance -->
  <div class="card p-4 grid grid-cols-2 gap-4">
    <div>
      <label class="text-xs text-slate-400 block mb-1">Last Price</label>
      <div id="price" class="text-2xl font-bold tabular-nums">--</div>
    </div>
    <div>
      <label class="text-xs text-slate-400 block mb-1">Balance</label>
      <div id="bal-base" class="text-sm font-medium tabular-nums">-- SHARP</div>
      <div id="bal-quote" class="text-sm font-medium tabular-nums text-slate-400">-- USDT</div>
    </div>
  </div>

  <!-- Orderbook -->
  <div class="card p-4">
    <label class="text-xs text-slate-400 block mb-2">Order Book</label>
    <div class="grid grid-cols-2 gap-3 text-xs font-mono">
      <!-- Asks (sells) — reversed so lowest ask is at bottom -->
      <div>
        <div class="flex justify-between text-slate-500 mb-1 px-1"><span>Price</span><span>Amount</span></div>
        <div id="ob-asks" class="space-y-px"></div>
      </div>
      <!-- Bids (buys) -->
      <div>
        <div class="flex justify-between text-slate-500 mb-1 px-1"><span>Price</span><span>Amount</span></div>
        <div id="ob-bids" class="space-y-px"></div>
      </div>
    </div>
  </div>

  <!-- Order Form -->
  <div class="card p-4 space-y-4">
    <!-- Side tabs -->
    <div class="flex gap-2">
      <button id="tab-buy" onclick="setSide('buy')" class="btn flex-1 py-2.5 rounded-xl font-semibold buy-btn text-white">Buy</button>
      <button id="tab-sell" onclick="setSide('sell')" class="btn flex-1 py-2.5 rounded-xl font-semibold bg-slate-700 text-slate-300">Sell</button>
    </div>

    <!-- Order type -->
    <div>
      <label class="text-xs text-slate-400 block mb-1">Order Type</label>
      <select id="order-type" class="w-full px-3 py-2.5 rounded-xl" onchange="onTypeChange()">
        <option value="market">Market</option>
        <option value="limit">Limit</option>
      </select>
    </div>

    <!-- Amount -->
    <div>
      <label class="text-xs text-slate-400 block mb-1">Amount (SHARP)</label>
      <input id="amount" type="number" placeholder="0" class="w-full px-3 py-2.5 rounded-xl tabular-nums" step="1" min="1">
      <div class="flex gap-2 mt-2">
        <button onclick="setPercent(25)" class="text-xs px-3 py-1 rounded-lg bg-slate-700 hover:bg-slate-600">25%</button>
        <button onclick="setPercent(50)" class="text-xs px-3 py-1 rounded-lg bg-slate-700 hover:bg-slate-600">50%</button>
        <button onclick="setPercent(75)" class="text-xs px-3 py-1 rounded-lg bg-slate-700 hover:bg-slate-600">75%</button>
        <button onclick="setPercent(100)" class="text-xs px-3 py-1 rounded-lg bg-slate-700 hover:bg-slate-600">100%</button>
      </div>
    </div>

    <!-- Price (limit only) -->
    <div id="price-row" class="hidden">
      <label class="text-xs text-slate-400 block mb-1">Price (USDT)</label>
      <input id="limit-price" type="number" placeholder="0.000000" class="w-full px-3 py-2.5 rounded-xl tabular-nums" step="0.000001">
    </div>

    <!-- Estimated total -->
    <div class="flex justify-between text-sm text-slate-400">
      <span>Estimated total</span>
      <span id="est-total" class="tabular-nums">-- USDT</span>
    </div>

    <!-- Submit -->
    <button id="submit-btn" onclick="placeOrder()" class="btn w-full py-3.5 rounded-xl font-bold text-lg buy-btn text-white">Buy SHARP</button>
  </div>

  <!-- Activity Log -->
  <div class="card p-4">
    <div class="flex items-center justify-between mb-2">
      <label class="text-xs text-slate-400">Trade History</label>
      <button onclick="loadHistory()" class="text-xs text-blue-400 hover:text-blue-300">Refresh</button>
    </div>
    <div id="log" class="space-y-1 max-h-64 overflow-y-auto text-xs font-mono"></div>
  </div>
</div>

<script>
let TOKEN = localStorage.getItem('spot-token') || '';
let currentSide = 'buy';
let lastPrice = 0;
let balBase = 0;
let balQuote = 0;
let priceInterval = null;
let balInterval = null;

const $ = id => document.getElementById(id);

// ── Auth ──
function doLogin() {
  const pw = $('pw').value;
  fetch('/spot/auth', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({password: pw}) })
    .then(r => r.json().then(d => ({ok: r.ok, data: d})))
    .then(({ok, data}) => {
      if (ok) {
        TOKEN = data.token;
        localStorage.setItem('spot-token', TOKEN);
        showTradeScreen();
      } else {
        $('login-err').classList.remove('hidden');
      }
    })
    .catch(() => $('login-err').classList.remove('hidden'));
}

function doLogout() {
  TOKEN = '';
  localStorage.removeItem('spot-token');
  clearInterval(priceInterval);
  clearInterval(balInterval);
  $('login-screen').classList.remove('hidden');
  $('trade-screen').classList.add('hidden');
}

function showTradeScreen() {
  $('login-screen').classList.add('hidden');
  $('trade-screen').classList.remove('hidden');
  refreshPrice();
  refreshBalance();
  refreshOrderbook();
  loadHistory();
  priceInterval = setInterval(refreshPrice, 5000);
  balInterval = setInterval(refreshBalance, 15000);
  setInterval(refreshOrderbook, 5000);
}

// ── API helpers ──
function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json', 'X-Spot-Token': TOKEN } };
  if (body) opts.body = JSON.stringify(body);
  return fetch(path, opts).then(r => {
    if (r.status === 401) { doLogout(); throw new Error('Session expired'); }
    return r.json().then(d => { if (!r.ok) throw new Error(d.detail || 'Error'); return d; });
  });
}

function getExchange() { return $('exchange').value; }
function getPair() { return $('pair').value; }

// ── Price ──
function refreshPrice() {
  api('GET', '/spot/price?exchange=' + getExchange() + '&symbol=' + encodeURIComponent(getPair()))
    .then(d => {
      lastPrice = d.last;
      const el = $('price');
      el.textContent = '$' + Number(d.last).toFixed(6);
      el.classList.add('flash');
      setTimeout(() => el.classList.remove('flash'), 600);
      updateTotal();
    })
    .catch(() => {});
}

// ── Balance ──
function refreshBalance() {
  api('GET', '/spot/balance?exchange=' + getExchange())
    .then(d => {
      const b = d.balances || {};
      balBase = b['SHARP'] || 0;
      balQuote = b['USDT'] || 0;
      $('bal-base').textContent = Number(balBase).toLocaleString(undefined, {maximumFractionDigits:0}) + ' SHARP';
      $('bal-quote').textContent = Number(balQuote).toFixed(2) + ' USDT';
    })
    .catch(() => {});
}

// ── Orderbook ──
function refreshOrderbook() {
  api('GET', '/spot/orderbook?exchange=' + getExchange() + '&symbol=' + encodeURIComponent(getPair()) + '&limit=10')
    .then(d => {
      const askEl = $('ob-asks');
      const bidEl = $('ob-bids');
      askEl.innerHTML = '';
      bidEl.innerHTML = '';
      // Asks: show lowest first (reversed), colored red
      const asks = (d.asks || []).slice(0, 10).reverse();
      const maxAsk = Math.max(...asks.map(a => a[1]), 1);
      asks.forEach(([p, a]) => {
        const pct = (a / maxAsk * 100).toFixed(0);
        askEl.innerHTML += '<div class="flex justify-between px-1 py-0.5 rounded relative overflow-hidden">' +
          '<div class="absolute inset-0 bg-red-500/10" style="width:' + pct + '%"></div>' +
          '<span class="text-red-400 relative z-10">' + Number(p).toFixed(6) + '</span>' +
          '<span class="text-slate-400 relative z-10">' + Number(a).toLocaleString(undefined,{maximumFractionDigits:0}) + '</span></div>';
      });
      // Bids: highest first, colored green
      const bids = (d.bids || []).slice(0, 10);
      const maxBid = Math.max(...bids.map(b => b[1]), 1);
      bids.forEach(([p, a]) => {
        const pct = (a / maxBid * 100).toFixed(0);
        bidEl.innerHTML += '<div class="flex justify-between px-1 py-0.5 rounded relative overflow-hidden">' +
          '<div class="absolute inset-0 bg-emerald-500/10" style="width:' + pct + '%"></div>' +
          '<span class="text-emerald-400 relative z-10">' + Number(p).toFixed(6) + '</span>' +
          '<span class="text-slate-400 relative z-10">' + Number(a).toLocaleString(undefined,{maximumFractionDigits:0}) + '</span></div>';
      });
    })
    .catch(() => {});
}

// ── Side tabs ──
function setSide(s) {
  currentSide = s;
  $('tab-buy').className = 'btn flex-1 py-2.5 rounded-xl font-semibold ' + (s==='buy' ? 'buy-btn text-white' : 'bg-slate-700 text-slate-300');
  $('tab-sell').className = 'btn flex-1 py-2.5 rounded-xl font-semibold ' + (s==='sell' ? 'sell-btn text-white' : 'bg-slate-700 text-slate-300');
  $('submit-btn').textContent = (s==='buy' ? 'Buy' : 'Sell') + ' SHARP';
  $('submit-btn').className = 'btn w-full py-3.5 rounded-xl font-bold text-lg text-white ' + (s==='buy' ? 'buy-btn' : 'sell-btn');
  updateTotal();
}

function onTypeChange() {
  $('price-row').classList.toggle('hidden', $('order-type').value === 'market');
  updateTotal();
}

function onExchangeChange() {
  refreshPrice();
  refreshBalance();
  refreshOrderbook();
}

function setPercent(pct) {
  if (currentSide === 'sell') {
    $('amount').value = Math.floor(balBase * pct / 100);
  } else {
    // Buy: calculate how many tokens we can buy with pct of USDT
    if (lastPrice > 0) {
      $('amount').value = Math.floor((balQuote * pct / 100) / lastPrice);
    }
  }
  updateTotal();
}

function updateTotal() {
  const amt = parseFloat($('amount').value) || 0;
  const p = $('order-type').value === 'limit' ? (parseFloat($('limit-price').value) || lastPrice) : lastPrice;
  $('est-total').textContent = (amt * p).toFixed(2) + ' USDT';
}

$('amount').addEventListener('input', updateTotal);
$('limit-price')?.addEventListener('input', updateTotal);

// ── Place order ──
function placeOrder() {
  const btn = $('submit-btn');
  const origText = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Placing...';

  const body = {
    exchange: getExchange(),
    symbol: getPair(),
    side: currentSide,
    amount: parseFloat($('amount').value),
    order_type: $('order-type').value,
  };
  if (body.order_type === 'limit') body.price = parseFloat($('limit-price').value);

  if (!body.amount || body.amount <= 0) {
    addLog('error', 'Enter a valid amount');
    btn.disabled = false;
    btn.textContent = origText;
    return;
  }

  api('POST', '/spot/order', body)
    .then(d => {
      const o = d.order || {};
      addLog('success', currentSide.toUpperCase() + ' ' + body.amount + ' SHARP @ ' + (o.price || lastPrice).toFixed(6) + ' on ' + body.exchange + ' — ID: ' + (o.id || 'ok'));
      refreshBalance();
      setTimeout(loadHistory, 1000);
    })
    .catch(e => addLog('error', e.message))
    .finally(() => { btn.disabled = false; btn.textContent = origText; });
}

function addLog(type, msg, time) {
  const el = document.createElement('div');
  const t = time || new Date().toLocaleTimeString();
  const color = type === 'success' ? 'text-emerald-400' : type === 'error' ? 'text-red-400' : 'text-slate-400';
  el.className = color;
  el.textContent = t + '  ' + msg;
  $('log').prepend(el);
  while ($('log').children.length > 100) $('log').lastChild.remove();
}

function loadHistory() {
  api('GET', '/spot/history?limit=50')
    .then(d => {
      $('log').innerHTML = '';
      (d.trades || []).reverse().forEach(t => {
        const time = new Date(t.ts).toLocaleString(undefined, {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'});
        const type = t.status === 'ok' ? 'success' : 'error';
        const msg = t.status === 'ok'
          ? t.side.toUpperCase() + ' ' + Number(t.amount).toLocaleString(undefined,{maximumFractionDigits:0}) + ' ' + t.symbol.split('/')[0] + ' @ ' + Number(t.price).toFixed(6) + ' on ' + t.exchange + ' — ID: ' + (t.order_id || '-')
          : t.side.toUpperCase() + ' FAILED: ' + (t.error || 'unknown');
        addLog(type, msg, time);
      });
    })
    .catch(() => {});
}

// ── Init ──
if (TOKEN) {
  // Validate token
  api('GET', '/spot/price?exchange=bitmart&symbol=SHARP/USDT')
    .then(() => showTradeScreen())
    .catch(() => { TOKEN = ''; localStorage.removeItem('spot-token'); });
} 
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
async def trade_page():
    """Serve the spot trading UI."""
    return TRADE_HTML
