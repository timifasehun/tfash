# %% [markdown]
# # first_backtest.py — YOUR FIRST SYSTEMATIC TRADING BACKTEST
#
# This is a lesson disguised as a program. Read it top to bottom. Every block has
# a comment explaining not just WHAT it does but WHY — because the "why" is the
# part that separates a backtest that fools you from one that teaches you.
#
# **What this script does:**
# 1. Downloads real daily crypto price data (Bitcoin) — free, no API key.
# 2. Builds a simple "moving-average crossover" trading rule.
# 3. Backtests it HONESTLY — respecting trading costs and avoiding "lookahead
#    bias" (the #1 way beginners accidentally cheat).
# 4. Compares it against just buying and holding.
# 5. Reports the metrics that actually matter and plots the result.
#
# The strategy itself is deliberately simple and probably NOT profitable after
# costs. That is the point. You are here to learn the machinery, not to get rich.
#
# **Two ways to run this file:**
# - All at once, in a terminal: `python first_backtest.py`
# - Cell by cell (recommended for learning): click inside a `# %%` block and press
#   `Shift+Enter`. Output — including DataFrame tables — appears in a side pane.
#
# Setup (run once): `pip install yfinance pandas numpy matplotlib`

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# When exploring interactively, show more columns instead of truncating with "..."
pd.set_option("display.max_columns", 30)

# %% [markdown]
# ## STEP 1 — GET THE DATA
#
# Rule of thumb you'll relearn forever: most "bad models" are actually bad data.
# Before trusting any signal, trust your data first.

# %%
def load_data(symbol="BTC-USD", start="2019-01-01"):
    """Download daily OHLCV data. Returns a clean DataFrame indexed by date."""
    import yfinance as yf

    # auto_adjust=True gives prices adjusted for splits/dividends. For crypto it
    # doesn't matter, but it's a good habit for when you move to equities/NGX.
    df = yf.download(symbol, start=start, auto_adjust=True, progress=False)

    # yfinance sometimes returns "multi-level" columns. Flatten them so we can
    # just say df["Close"] without surprises.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Keep only what we need and drop any rows with missing prices.
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    return df


# %%
# Run STEP 1. The last line is a DataFrame, so it renders as a table you can SEE.
# Each row is one day; each column is a price (Open/High/Low/Close) or Volume.
data = load_data("BTC-USD")
data.head()

# %%
# A few other ways to "look at" the data from different angles:
print("Shape (rows, columns):", data.shape)
print("\nColumn data types:\n", data.dtypes)
data.describe()  # summary statistics per column

# %% [markdown]
# ## STEP 2 — BUILD THE SIGNAL
#
# A "signal" is a rule that says, each day, whether we want to be IN the market
# (holding) or OUT (in cash). Here: hold when the short-term average price is
# above the long-term average (a crude "uptrend" detector).

# %%
def add_signal(df, fast=20, slow=100):
    """Add moving averages and a 0/1 'in the market?' signal column."""
    df = df.copy()

    # A moving average smooths out day-to-day noise. "fast" reacts quickly,
    # "slow" reacts slowly. When fast crosses above slow -> momentum is up.
    df["ma_fast"] = df["Close"].rolling(fast).mean()
    df["ma_slow"] = df["Close"].rolling(slow).mean()

    # signal = 1 means "we want to be holding", 0 means "we want to be in cash".
    df["signal"] = (df["ma_fast"] > df["ma_slow"]).astype(int)

    return df


# %%
# Run STEP 2, then LOOK at the new columns. We view rows 100..110 because the
# 100-day moving average is NaN before day 100 (not enough history to average).
data = add_signal(data, fast=20, slow=100)
data[["Close", "ma_fast", "ma_slow", "signal"]].iloc[100:110]

# %%
# See it visually: price with its two moving averages layered on top.
data[["Close", "ma_fast", "ma_slow"]].plot(figsize=(11, 5), title="Close vs moving averages")
plt.show()

# %% [markdown]
# ## STEP 3 — BACKTEST IT (THE HONEST WAY)
#
# The rung everyone rushes and pros obsess over. If you remember only two things
# from this whole script, make it these:
#
# **(A) LOOKAHEAD BIAS.** On day T you can compute the signal only AFTER the day's
# close is known — so you can't trade on it until day T+1. Multiplying today's
# signal by today's return uses information from the future: a subtle cheat that
# makes garbage strategies look brilliant. The fix is one line: shift the signal
# forward by one day.
#
# **(B) COSTS.** Every switch between holding and cash costs a fee and a bit of
# spread. Ignore costs and a strategy that trades constantly looks free. It isn't.

# %%
def backtest(df, cost_per_trade=0.001):
    """Turn a signal into an equity curve, honestly. cost_per_trade = 0.1%."""
    df = df.copy()

    # Daily percentage return of just holding the asset.
    df["ret"] = df["Close"].pct_change()

    # (A) THE ANTI-LOOKAHEAD SHIFT. Our POSITION today is yesterday's signal,
    # because that's the most recent signal we could actually have acted on.
    df["position"] = df["signal"].shift(1).fillna(0)

    # (B) COSTS. A "trade" happens on any day the position changes (0->1 or
    # 1->0). position.diff().abs() is 1 on those days, 0 otherwise.
    df["trade"] = df["position"].diff().abs().fillna(0)
    df["cost"] = df["trade"] * cost_per_trade

    # Our strategy's daily return = (are we holding?) * (asset return) - costs.
    df["strat_ret"] = df["position"] * df["ret"] - df["cost"]

    # An equity curve compounds returns over time. Start with 1 unit of money;
    # (1 + r).cumprod() shows what it grows to. We do this for our strategy and
    # for a plain buy-and-hold benchmark, so we can compare.
    df["equity_strategy"] = (1 + df["strat_ret"]).cumprod()
    df["equity_buyhold"] = (1 + df["ret"]).cumprod()

    return df.dropna()


# %%
# Run STEP 3, then compare `signal` and `position`: position is signal slid DOWN
# one row — that is the anti-lookahead shift, made visible.
data = backtest(data, cost_per_trade=0.001)
data[["signal", "position", "ret", "trade", "strat_ret"]].iloc[100:110]

# %%
# Boolean filtering: show only the days a trade actually fired (position flipped).
data[data["trade"] == 1][["Close", "signal", "position", "cost"]].head(15)

# %% [markdown]
# ## STEP 4 — MEASURE IT
#
# "It made money" is not analysis. These three numbers are the starting
# vocabulary of every quant conversation.

# %%
def metrics(daily_returns, periods_per_year=365):
    """Return (total_return, annualized_Sharpe, max_drawdown) for a return series."""
    r = daily_returns.dropna()

    # TOTAL RETURN: what 1 unit of money became, minus the 1 you started with.
    total_return = (1 + r).prod() - 1

    # SHARPE RATIO: return per unit of risk (volatility). Higher = smoother ride
    # for the same gain. We annualize by scaling with sqrt(periods). Crypto
    # trades every day, so 365; stock markets use ~252 trading days.
    sharpe = np.sqrt(periods_per_year) * r.mean() / r.std() if r.std() > 0 else 0.0

    # MAX DRAWDOWN: the worst peak-to-trough drop along the way. This is the
    # number that tells you whether you could actually STOMACH the strategy.
    equity = (1 + r).cumprod()
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1
    max_drawdown = drawdown.min()

    return total_return, sharpe, max_drawdown


def report(df):
    """Print a side-by-side comparison of the strategy vs buy-and-hold."""
    strat = metrics(df["strat_ret"])
    hold = metrics(df["ret"])

    print("\n" + "=" * 60)
    print(f"{'METRIC':<22}{'STRATEGY':>18}{'BUY & HOLD':>18}")
    print("-" * 60)
    labels = ["Total return", "Sharpe ratio", "Max drawdown"]
    fmts = ["{:+.1%}", "{:.2f}", "{:.1%}"]
    for label, fmt, s, h in zip(labels, fmts, strat, hold):
        print(f"{label:<22}{fmt.format(s):>18}{fmt.format(h):>18}")
    print("=" * 60)

    n_trades = int(df["trade"].sum())
    print(f"Number of trades: {n_trades}   (each one cost you money)\n")


# %%
# Run STEP 4. Also build a small DataFrame of the metrics so it renders as a
# clean table (nicer to read than the printed version when exploring).
report(data)

pd.DataFrame(
    {"Strategy": metrics(data["strat_ret"]), "Buy & Hold": metrics(data["ret"])},
    index=["Total return", "Sharpe ratio", "Max drawdown"],
)

# %% [markdown]
# ## STEP 5 — SEE IT

# %%
def plot(df, symbol="BTC-USD"):
    """Plot the two equity curves so you can eyeball the difference."""
    plt.figure(figsize=(11, 6))
    plt.plot(df.index, df["equity_buyhold"], label="Buy & Hold", linewidth=1.5)
    plt.plot(df.index, df["equity_strategy"], label="MA Crossover Strategy", linewidth=1.5)
    plt.title(f"{symbol}: Strategy vs Buy & Hold (growth of 1 unit)")
    plt.ylabel("Portfolio value (started at 1)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("backtest_result.png", dpi=120)
    print("Saved chart to backtest_result.png")


# %%
# Run STEP 5. plt.show() renders the chart inline in the interactive pane.
plot(data, "BTC-USD")
plt.show()

# %% [markdown]
# ## NOW EXPERIMENT — this is how you actually learn
#
# Re-run from STEP 2 after changing things:
# - Change `fast`/`slow` (e.g. 10/50, 50/200). Watch the trade count and Sharpe.
# - Change the symbol in STEP 1 to `"ETH-USD"`.
# - Set `cost_per_trade=0` and see how much "profit" was fake (just costs).
#
# Ask yourself after each run: am I finding an edge, or fitting noise?

# %%
# This block runs ONLY when you execute the file as a whole (`python first_backtest.py`).
# When running cell-by-cell above, it's skipped — you've already built `data`.
if __name__ == "__main__":
    SYMBOL = "BTC-USD"
    print(f"Downloading {SYMBOL} ...")
    data = load_data(SYMBOL)
    data = add_signal(data, fast=20, slow=100)
    data = backtest(data, cost_per_trade=0.001)
    report(data)
    plot(data, SYMBOL)

# %%
