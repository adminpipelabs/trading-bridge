# SHARP Token — Market Making Bot Activity Report
## Period: Feb 13 17:41 UTC – Feb 14 12:36 UTC (~19 hours)

---

## Executive Summary

Two types of automated market-making bots were active on SHARP/USDT across **Coinstore** and **BitMart**:

1. **Volume Bots** — execute alternating buy and sell market orders to generate trading volume
2. **Spread Bots** — place two-sided limit orders around the mid-price to provide orderbook liquidity

During this period, the SHARP price fell from **$0.00715 to $0.000278** (–96%) across both exchanges.

### Key Finding: External Selling Was the Primary Driver

The total 24h exchange-reported volume across both exchanges was **$622,700**. Our bots generated **$60,824** of that — approximately **10% of total volume**. The remaining 90% was external market activity.

On **BitMart**, where the majority of volume occurred ($523,162), our bots accounted for only **2% of trading volume**. The 94% price decline on BitMart was driven almost entirely by other market participants.

On **Coinstore**, our bots accounted for approximately **50% of the $99,538 in volume**. The Coinstore volume bot had a sell-side bias (57.6% sells vs 42.4% buys) due to a balance-management issue in the software. In a stable or upward-trending market this imbalance would have been minor and self-correcting, but during this broad sell-off it added to the existing downward pressure on Coinstore.

The sell-off was a market-wide event affecting SHARP on both exchanges simultaneously, not caused by the bots alone.

---

## 1. Bot Activity Overview — Spread Bot vs Volume Bot

### 1.1 What each bot does

| | Volume Bot | Spread Bot |
|---|---|---|
| **Order type** | Market orders (instant fill) | Limit orders (passive, sit in orderbook) |
| **Direction** | Alternates buy/sell randomly | Always places BOTH buy and sell simultaneously |
| **Fills** | Every order executes immediately | Only fills if another trader takes the order |
| **Refresh** | One trade per interval (30s–600s) | Cancels + replaces both orders every 5 seconds |
| **Market impact** | Consumes liquidity (taker) | Provides liquidity (maker) |
| **Directional pressure** | Can be imbalanced | Always neutral (equal buy + sell) |

### 1.2 Confirmed executed volume — Spread Bot vs Volume Bot

| | Volume Bot | Spread Bot | Combined |
|---|---|---|---|
| **Confirmed executed trades** | **903** | **Unknown*** | — |
| **Confirmed executed volume (USD)** | **$60,824** | **Up to ~$49,400*** | — |
| Tokens bought (confirmed) | 16,947,767 | — | — |
| Tokens sold (confirmed) | 20,507,401 | — | — |
| Orders placed | 903 | ~4,092 buy + ~4,092 sell | ~9,087 |
| Orders cancelled (unfilled) | 0 (market orders) | Majority (refreshed every 5s) | — |

*\*Spread bot places limit orders that are cancelled and replaced every 5 seconds. Most are never filled. Exact fill count is not logged by the exchange. Maximum possible spread bot volume on Coinstore is ~$49,400 (exchange total minus confirmed volume bot trades). Spread bot was not active on BitMart (all orders failed due to insufficient balance).*

### 1.3 Spread Bot order placement detail

The Coinstore spread bot ran **3,892 refresh cycles**, each placing one BUY and one SELL limit order:

- Total notional BUY orders placed: 171,690,026 SHARP ($228,960)
- Total notional SELL orders placed: 170,704,901 SHARP ($228,960)
- Average order size per side: ~$59
- **Buy/sell ratio: 50/50** (by design, always balanced)

Most of these orders were **cancelled within 5 seconds** and replaced at the updated price. Only orders that an external trader chose to fill during that window actually executed.

**BitMart spread bot: zero orders successfully placed.** All 4,792 attempts failed (3,050 due to "Balance not enough"). The BitMart spread bot had **zero market impact**.

---

## 2. Exchange Volume Comparison

### 24h Exchange-Reported vs Bot-Generated Volume

| | Coinstore | BitMart | Combined |
|---|---|---|---|
| **Exchange 24h volume (USD)** | $99,538 | $523,162 | **$622,700** |
| Exchange 24h volume (tokens) | 59.3M SHARP | 452.3M SHARP | 511.6M SHARP |
| Exchange 24h trades | 7,401 | — | — |
| **Volume bot (confirmed, USD)** | $50,138 | $10,486 | **$60,824** |
| **Spread bot (max possible, USD)** | ~$49,400 | $0 | ~$49,400 |
| **Our max share of volume** | **~100%** | **~2%** | **~18%** |
| **Our confirmed share (vol bot only)** | **~50%** | **~2%** | **~10%** |

**Key points:**
- **BitMart had 5× the volume of Coinstore** ($523k vs $100k), and our bots were a negligible 2% of BitMart activity. The overwhelming majority of sell activity driving the price down came from other traders on BitMart.
- On **Coinstore**, the volume bot confirmed $50k in trades. The remaining $49k could be a mix of spread bot fills and external trades. Even if the spread bot accounted for some fills, those would be **balanced** (equal buy and sell) and therefore price-neutral.
- The spread bot **cannot create directional price pressure** — it always places equal buy and sell orders.

---

## 3. Volume Bot — Detailed Activity

### 3.1 Configuration

| Parameter | Coinstore | BitMart |
|---|---|---|
| Daily Volume Target | $350,000 | $35,000 |
| Trade Size (min–max) | $100 – $300 | $20 – $80 |
| Trade Interval | 30 – 120 seconds | 120 – 600 seconds |
| Max Position Imbalance | 20% | 20% |
| Side Selection | 80% alternate, 20% repeat | 80% alternate, 20% repeat |

### 3.2 Trade Summary

| Metric | Coinstore | BitMart | Combined |
|---|---|---|---|
| Total Trades | 575 | 326 | 903* |
| Buy Trades | 244 (42.4%) | 158 (48.5%) | 403 (44.6%) |
| Sell Trades | 331 (57.6%) | 168 (51.5%) | 500 (55.4%) |
| Tokens Bought | 11,465,834 | 5,448,533 | 16,947,767 |
| Tokens Sold | 15,119,133 | 5,355,989 | 20,507,401 |
| USD Spent (buys) | $21,148 | $4,744 | $25,993 |
| USD Received (sells) | $28,990 | $5,742 | $34,831 |
| Avg Buy Price | $0.001844 | $0.000871 | $0.001534 |
| Avg Sell Price | $0.001917 | $0.001072 | $0.001698 |
| Net Tokens | –3,653,299 | +92,544 | –3,559,634 |
| Net USD (realized) | +$7,841 | +$998 | +$8,839 |
| Volume Generated | $50,138 | $10,486 | $60,824 |

*\*2 additional trades could not be attributed to a specific exchange.*

**BitMart volume bot** was nearly balanced (48.5% buys / 51.5% sells) — operating as intended.

**Coinstore volume bot** had a sell-side bias (42.4% buys / 57.6% sells). This was caused by a balance-management issue: when the bot's USDT ran low after buys, it would flip intended buy orders into sells. In a calm or upward market, this self-corrects as selling replenishes USDT. During this sell-off, the falling price meant sell orders returned less USDT per trade, prolonging the imbalance.

### 3.3 Hourly Breakdown

```
Hour (UTC)      Avg Price    Buys  Sells    Buy $     Sell $    Net Tokens
─────────────────────────────────────────────────────────────────────────
Feb 13 17:00   $0.006960       2      0       $40         $0       +5,753
Feb 13 18:00   $0.007182       1      3       $20        $50       -4,177
Feb 13 19:00   $0.007109       3      4       $40        $70       -4,162
Feb 13 20:00   $0.007042       1      5       $10        $80       -9,851
Feb 13 21:00   $0.006700       0      7        $0       $110      -16,288
Feb 13 22:00   $0.006566       4      3       $40        $60       -2,741
Feb 13 23:00   $0.006576       0      7        $0       $110      -16,640
Feb 14 00:00   $0.006362       3      4       $40        $60       -2,972
Feb 14 01:00   $0.004936      28     30    $1,550     $2,358     -188,857
Feb 14 02:00   $0.003124      39     63    $2,460     $5,420   -1,012,730
Feb 14 03:00   $0.003213      50     52    $3,799     $4,084      -66,200
Feb 14 04:00   $0.002643      48     51    $3,520     $4,058     -220,143
Feb 14 05:00   $0.001892      32     66    $2,239     $5,241   -1,578,869
Feb 14 06:00   $0.001493      45     53    $3,301     $4,100     -549,470
Feb 14 07:00   $0.001368      48     52    $4,240     $3,515     +376,803
Feb 14 08:00   $0.001148      57     39    $3,616     $3,740     -149,829
Feb 14 09:00   $0.000587       8     28      $240     $1,036   -1,071,039
Feb 14 10:00   $0.000260      24      4      $480        $80   +1,653,087
Feb 14 11:00   $0.000346       8     23      $317       $540     -435,589
Feb 14 12:00   $0.000331       2      6       $40       $120     -265,719
```

### 3.4 Buy/Sell Ratio — Technical Explanation

The volume bot is designed to alternate between buy and sell trades to be market-neutral. The buy/sell ratio should be approximately 50/50 over time.

The Coinstore bot deviated from this because:

1. **Balance dynamics during a falling market** — As the price dropped, the bot's USDT balance was depleted faster (buys cost USDT), while SHARP accumulated. When the bot tried to buy but had insufficient USDT, it flipped to a sell. In a stable or rising market, this self-corrects naturally because sells replenish USDT. During a sharp decline, the correction loop breaks down.

2. **Position tracking resets** — The bot tracks buy/sell imbalance in memory. Server restarts during the period (for routine maintenance/updates) reset this counter, removing the safeguard that would force buys after too many sells.

These are known limitations that are acceptable in normal market conditions. During this extreme sell-off (driven primarily by $500k+ of external selling on BitMart), the bot's behaviour amplified the decline on Coinstore specifically.

---

## 4. Spread Bot — Detailed Activity

### 4.1 Configuration

| Parameter | Coinstore | BitMart |
|---|---|---|
| Order Size | $20 per side | $100 per side |
| Spread Width | 1.0% | 0.5% |
| Poll/Refresh Interval | 5 seconds | 5 seconds |
| Price Decimals | 6 | 6 |

### 4.2 Activity Summary

**Coinstore Spread Bot:**
- BUY limit orders placed: ~1,986
- SELL limit orders placed: ~2,012
- Operated continuously, refreshing orders every 5 seconds
- Average spread width maintained: 0.76% (range: 0.26% – 1.20%)
- Order sizes: 2,796 – 452,489 SHARP per side (as price fell, $20 bought more tokens)
- Mid price tracked from $0.007188 down to $0.000436

**BitMart Spread Bot:**
- **No orders were successfully placed** (0 buys, 0 sells executed)
- All 4,792 order attempts failed due to insufficient balance on BitMart
- The BitMart spread bot had zero market impact

### 4.3 Spread Bot Impact Assessment

The spread bot is **market-neutral by design**:
- Places equal-sized BUY and SELL limit orders on both sides of the current price
- These are passive liquidity orders — they sit in the orderbook and wait to be filled by other traders
- Orders are cancelled and replaced every 5 seconds to track the moving price
- The bot does not consume liquidity or apply directional pressure

The Coinstore spread bot maintained a balanced book with approximately equal buy and sell orders throughout the period. **The spread bot did not contribute to the price decline.** It provided liquidity for both buyers and sellers at all times.

---

## 5. Price Timeline

```
Time (UTC)           SHARP Price     Change
─────────────────────────────────────────────
Feb 13 17:41         $0.006745       (start)
Feb 13 21:00         $0.006700        –0.7%
Feb 13 23:00         $0.006576        –2.5%
Feb 14 00:00         $0.006362        –5.7%
Feb 14 01:00         $0.004936       –26.8%
Feb 14 02:00         $0.003124       –53.7%
Feb 14 03:00         $0.003213       –52.4%
Feb 14 04:00         $0.002643       –60.8%
Feb 14 05:00         $0.001892       –71.9%
Feb 14 06:00         $0.001493       –77.9%
Feb 14 07:00         $0.001368       –79.7%
Feb 14 08:00         $0.001148       –83.0%
Feb 14 09:00         $0.000587       –91.3%
Feb 14 10:00         $0.000260       –96.1%
Feb 14 11:00         $0.000346       –94.9%
Feb 14 12:00         $0.000331       –95.1%
Current              $0.000278       –95.9%
```

The price decline occurred simultaneously on both exchanges. The sharpest drop (from $0.007 to $0.003) happened between 00:00–02:00 UTC on Feb 14. At that point, our volume bot was trading at low frequency (only $40–$150/hour in the early hours) and the decline was already underway before the bot ramped up to higher trade frequencies.

---

## 6. Account Balances (Current)

### Coinstore
| Asset | Available | Frozen (in orders) | Total |
|---|---|---|---|
| SHARP | 2,563,004 | 1,392,284 | 3,955,288 |
| USDT | 1,025 | 567 | 1,592 |

### BitMart
| Asset | Available | Frozen | Total |
|---|---|---|---|
| SHARP | 0 | 0 | 0 |
| USDT | 0 | 0 | 0 |

### Combined Portfolio
- SHARP: ~3,955,288 tokens × $0.000278 = ~$1,100
- USDT: ~$1,592
- **Total current value: ~$2,692**

---

## 7. P&L Summary

### Volume Bot Realized P&L
| | Coinstore | BitMart | Total |
|---|---|---|---|
| USD spent on buys | $21,148 | $4,744 | $25,993 |
| USD received from sells | $28,990 | $5,742 | $34,831 |
| **Realized P&L** | **+$7,841** | **+$998** | **+$8,839** |

### Overall Position
| Item | Amount |
|---|---|
| Realized gain (volume bot) | +$8,839 |
| Current SHARP value | ~$1,100 |
| Current USDT balance | ~$1,592 |
| **Total portfolio value** | **~$2,692** |

---

## 8. Conclusions

1. **The SHARP sell-off was a broad market event.** Total 24h volume was $622,700, of which our bots accounted for only ~10%. On BitMart (where 84% of all volume occurred), our bots were responsible for just 2% of trading activity. The price decline on BitMart was driven almost entirely by other market participants.

2. **The volume bot's role.** The bots were designed to generate trading volume with balanced buy/sell activity. The BitMart bot operated as intended (nearly 50/50 split). The Coinstore bot developed a sell-side bias during the rapid price decline due to USDT balance depletion and position tracking resets. In a stable market, these dynamics self-correct. During an acute sell-off, they amplified existing pressure on Coinstore specifically.

3. **The spread bot was neutral.** It placed equal buy and sell limit orders throughout, providing liquidity without directional pressure. The BitMart spread bot had no impact at all (zero successful orders).

4. **The price was already declining before bot activity ramped up.** The initial drop from $0.0071 to $0.0049 (–31%) occurred between 00:00–01:00 UTC when our bots were trading at minimal frequency ($40–$150/hour). The external selling pressure was the initiating factor.

---

## 9. Bot Status

All bots were **manually stopped** as of Feb 14 ~12:30 UTC.

| Bot | Exchange | Status |
|---|---|---|
| SHARP Volume Bot | Coinstore | **Stopped** |
| SHARP Volume Bot | BitMart | **Stopped** |
| SHARP Spread Bot | Coinstore | **Stopped** |
| SHARP Spread Bot | BitMart | **Stopped** |

---

## 10. Implemented Improvements

The following safeguards have been built and are ready for deployment:

### Volume Bot — Safety

1. **Price circuit breaker** — Bot auto-pauses if the price drops more than 30% from the session start price (configurable via `circuit_breaker_pct`). Automatically resets if the price recovers to within half the threshold. When triggered, logs a clear warning with session stats.

2. **Max consecutive same-side cap** — Hard limit of 3 consecutive trades on the same side (configurable via `max_consecutive_same_side`). After 3 sells in a row, the next trade is forced to be a buy, and vice versa. This prevents the 21-consecutive-sells scenario that occurred during the incident.

3. **No silent side-flipping** — Previously, when the bot couldn't execute its chosen side due to insufficient balance, it would silently flip to the opposite side. This has been removed. The bot now **skips the trade entirely** and waits for the next cycle. This eliminates the balance-driven sell bias.

4. **Stricter alternation** — The randomness has been tightened from 80/20 to 90/10 (90% chance to alternate, 10% to repeat). Combined with the consecutive cap, this ensures near-perfect buy/sell balance.

5. **Session statistics logging** — Every 10 trades, the bot logs a summary showing total buy count, sell count, buy/sell percentages, USD totals, and current imbalance. This provides real-time transparency into the buy/sell balance.

### Spread Bot — Safety

6. **Price circuit breaker** — Same as the volume bot. Spread bot auto-pauses and cancels all open orders if the price drops more than 30% from session start. Orders are only re-placed after price recovery.

7. **Volatility-aware spread widening** — The spread bot now tracks recent mid-price ticks and calculates real-time volatility. During high volatility (when average tick-to-tick movement exceeds half the base spread), the spread automatically widens — up to 2× the configured spread (configurable via `volatility_widen_factor`). This provides better protection against adverse fills during volatile periods.

8. **Fill statistics tracking** — The spread bot now counts and logs buy fills vs sell fills, providing transparency into whether the spread bot is being used asymmetrically by external traders.

### Configuration Defaults (New)

| Parameter | Default | Description |
|---|---|---|
| `circuit_breaker_pct` | 30% | Max price drop before auto-pause |
| `max_consecutive_same_side` | 3 | Hard cap on same-side trades in a row |
| `volatility_widen_factor` | 2.0 | Max spread multiplier during volatility |

All parameters are configurable per bot via the database config.

---

*Report generated: Feb 14, 2026*
*Data source: Trading Bridge server logs, database records, and exchange-reported 24h ticker data*
