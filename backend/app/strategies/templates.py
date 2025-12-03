"""Pre-built options strategy templates

Common options strategies ready to use.
"""

from datetime import datetime
from .builder import StrategyBuilder


def long_call(
    strike: float,
    expiry: datetime,
    premium: float,
    quantity: int = 1,
    **greeks
) -> StrategyBuilder:
    """
    Long Call - Bullish strategy
    
    Max Profit: Unlimited
    Max Loss: Premium paid
    Breakeven: Strike + Premium
    """
    strategy = StrategyBuilder(name="Long Call")
    strategy.add_leg(
        action="buy",
        option_type="call",
        strike=strike,
        expiry=expiry,
        quantity=quantity,
        premium=premium,
        **greeks
    )
    return strategy


def long_put(
    strike: float,
    expiry: datetime,
    premium: float,
    quantity: int = 1,
    **greeks
) -> StrategyBuilder:
    """
    Long Put - Bearish strategy
    
    Max Profit: Strike - Premium
    Max Loss: Premium paid
    Breakeven: Strike - Premium
    """
    strategy = StrategyBuilder(name="Long Put")
    strategy.add_leg(
        action="buy",
        option_type="put",
        strike=strike,
        expiry=expiry,
        quantity=quantity,
        premium=premium,
        **greeks
    )
    return strategy


def short_call(
    strike: float,
    expiry: datetime,
    premium: float,
    quantity: int = 1,
    **greeks
) -> StrategyBuilder:
    """
    Short (Naked) Call - Bearish/Neutral strategy
    
    Max Profit: Premium received
    Max Loss: Unlimited
    Breakeven: Strike + Premium
    
    WARNING: Unlimited risk
    """
    strategy = StrategyBuilder(name="Short Call")
    strategy.add_leg(
        action="sell",
        option_type="call",
        strike=strike,
        expiry=expiry,
        quantity=quantity,
        premium=premium,
        **greeks
    )
    return strategy


def short_put(
    strike: float,
    expiry: datetime,
    premium: float,
    quantity: int = 1,
    **greeks
) -> StrategyBuilder:
    """
    Short (Naked) Put - Bullish/Neutral strategy
    
    Max Profit: Premium received
    Max Loss: Strike - Premium
    Breakeven: Strike - Premium
    """
    strategy = StrategyBuilder(name="Short Put")
    strategy.add_leg(
        action="sell",
        option_type="put",
        strike=strike,
        expiry=expiry,
        quantity=quantity,
        premium=premium,
        **greeks
    )
    return strategy


def bull_call_spread(
    long_strike: float,
    short_strike: float,
    expiry: datetime,
    long_premium: float,
    short_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Bull Call Spread - Moderately bullish strategy
    
    Buy lower strike call, sell higher strike call
    
    Max Profit: (Short Strike - Long Strike) - Net Debit
    Max Loss: Net Debit
    Breakeven: Long Strike + Net Debit
    """
    strategy = StrategyBuilder(name="Bull Call Spread")
    strategy.add_leg("buy", "call", long_strike, expiry, quantity, long_premium)
    strategy.add_leg("sell", "call", short_strike, expiry, quantity, short_premium)
    return strategy


def bear_call_spread(
    short_strike: float,
    long_strike: float,
    expiry: datetime,
    short_premium: float,
    long_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Bear Call Spread (Credit Spread) - Moderately bearish strategy
    
    Sell lower strike call, buy higher strike call
    
    Max Profit: Net Credit
    Max Loss: (Long Strike - Short Strike) - Net Credit
    Breakeven: Short Strike + Net Credit
    """
    strategy = StrategyBuilder(name="Bear Call Spread")
    strategy.add_leg("sell", "call", short_strike, expiry, quantity, short_premium)
    strategy.add_leg("buy", "call", long_strike, expiry, quantity, long_premium)
    return strategy


def bull_put_spread(
    short_strike: float,
    long_strike: float,
    expiry: datetime,
    short_premium: float,
    long_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Bull Put Spread (Credit Spread) - Moderately bullish strategy
    
    Sell higher strike put, buy lower strike put
    
    Max Profit: Net Credit
    Max Loss: (Short Strike - Long Strike) - Net Credit
    Breakeven: Short Strike - Net Credit
    """
    strategy = StrategyBuilder(name="Bull Put Spread")
    strategy.add_leg("sell", "put", short_strike, expiry, quantity, short_premium)
    strategy.add_leg("buy", "put", long_strike, expiry, quantity, long_premium)
    return strategy


def bear_put_spread(
    long_strike: float,
    short_strike: float,
    expiry: datetime,
    long_premium: float,
    short_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Bear Put Spread - Moderately bearish strategy
    
    Buy higher strike put, sell lower strike put
    
    Max Profit: (Long Strike - Short Strike) - Net Debit
    Max Loss: Net Debit
    Breakeven: Long Strike - Net Debit
    """
    strategy = StrategyBuilder(name="Bear Put Spread")
    strategy.add_leg("buy", "put", long_strike, expiry, quantity, long_premium)
    strategy.add_leg("sell", "put", short_strike, expiry, quantity, short_premium)
    return strategy


def long_straddle(
    strike: float,
    expiry: datetime,
    call_premium: float,
    put_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Long Straddle - High volatility strategy
    
    Buy call and put at same strike
    
    Max Profit: Unlimited
    Max Loss: Total premiums paid
    Breakevens: Strike ± Total Premium
    """
    strategy = StrategyBuilder(name="Long Straddle")
    strategy.add_leg("buy", "call", strike, expiry, quantity, call_premium)
    strategy.add_leg("buy", "put", strike, expiry, quantity, put_premium)
    return strategy


def short_straddle(
    strike: float,
    expiry: datetime,
    call_premium: float,
    put_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Short Straddle - Low volatility strategy
    
    Sell call and put at same strike
    
    Max Profit: Total premiums received
    Max Loss: Unlimited
    Breakevens: Strike ± Total Premium
    
    WARNING: Unlimited risk
    """
    strategy = StrategyBuilder(name="Short Straddle")
    strategy.add_leg("sell", "call", strike, expiry, quantity, call_premium)
    strategy.add_leg("sell", "put", strike, expiry, quantity, put_premium)
    return strategy


def long_strangle(
    call_strike: float,
    put_strike: float,
    expiry: datetime,
    call_premium: float,
    put_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Long Strangle - High volatility strategy
    
    Buy OTM call and OTM put
    
    Max Profit: Unlimited
    Max Loss: Total premiums paid
    Breakevens: Call Strike + Total Premium, Put Strike - Total Premium
    """
    strategy = StrategyBuilder(name="Long Strangle")
    strategy.add_leg("buy", "call", call_strike, expiry, quantity, call_premium)
    strategy.add_leg("buy", "put", put_strike, expiry, quantity, put_premium)
    return strategy


def short_strangle(
    call_strike: float,
    put_strike: float,
    expiry: datetime,
    call_premium: float,
    put_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Short Strangle - Low volatility strategy
    
    Sell OTM call and OTM put
    
    Max Profit: Total premiums received
    Max Loss: Unlimited
    Breakevens: Call Strike + Total Premium, Put Strike - Total Premium
    
    WARNING: Unlimited risk on upside
    """
    strategy = StrategyBuilder(name="Short Strangle")
    strategy.add_leg("sell", "call", call_strike, expiry, quantity, call_premium)
    strategy.add_leg("sell", "put", put_strike, expiry, quantity, put_premium)
    return strategy


def iron_condor(
    put_long_strike: float,
    put_short_strike: float,
    call_short_strike: float,
    call_long_strike: float,
    expiry: datetime,
    put_long_premium: float,
    put_short_premium: float,
    call_short_premium: float,
    call_long_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Iron Condor - Neutral/Low volatility strategy
    
    Combination of bull put spread and bear call spread
    
    Max Profit: Net Credit
    Max Loss: Wing Width - Net Credit
    Breakevens: Put Short Strike - Net Credit, Call Short Strike + Net Credit
    """
    strategy = StrategyBuilder(name="Iron Condor")
    # Bull put spread (lower)
    strategy.add_leg("buy", "put", put_long_strike, expiry, quantity, put_long_premium)
    strategy.add_leg("sell", "put", put_short_strike, expiry, quantity, put_short_premium)
    # Bear call spread (upper)
    strategy.add_leg("sell", "call", call_short_strike, expiry, quantity, call_short_premium)
    strategy.add_leg("buy", "call", call_long_strike, expiry, quantity, call_long_premium)
    return strategy


def iron_butterfly(
    long_strike_low: float,
    short_strike: float,
    long_strike_high: float,
    expiry: datetime,
    put_long_premium: float,
    put_short_premium: float,
    call_short_premium: float,
    call_long_premium: float,
    quantity: int = 1
) -> StrategyBuilder:
    """
    Iron Butterfly - Neutral/Low volatility strategy
    
    Similar to iron condor but with short strikes at same price
    
    Max Profit: Net Credit
    Max Loss: Wing Width - Net Credit
    Breakevens: Short Strike ± (Wing Width - Net Credit)
    """
    strategy = StrategyBuilder(name="Iron Butterfly")
    strategy.add_leg("buy", "put", long_strike_low, expiry, quantity, put_long_premium)
    strategy.add_leg("sell", "put", short_strike, expiry, quantity, put_short_premium)
    strategy.add_leg("sell", "call", short_strike, expiry, quantity, call_short_premium)
    strategy.add_leg("buy", "call", long_strike_high, expiry, quantity, call_long_premium)
    return strategy


def calendar_spread(
    strike: float,
    near_expiry: datetime,
    far_expiry: datetime,
    near_premium: float,
    far_premium: float,
    option_type: str = "call",
    quantity: int = 1
) -> StrategyBuilder:
    """
    Calendar Spread (Time Spread) - Neutral strategy
    
    Sell near-term option, buy far-term option at same strike
    
    Profits from time decay difference
    """
    strategy = StrategyBuilder(name="Calendar Spread")
    strategy.add_leg("sell", option_type, strike, near_expiry, quantity, near_premium)
    strategy.add_leg("buy", option_type, strike, far_expiry, quantity, far_premium)
    return strategy


def diagonal_spread(
    short_strike: float,
    long_strike: float,
    near_expiry: datetime,
    far_expiry: datetime,
    short_premium: float,
    long_premium: float,
    option_type: str = "call",
    quantity: int = 1
) -> StrategyBuilder:
    """
    Diagonal Spread - Directional + time decay strategy
    
    Like calendar spread but with different strikes
    
    Call diagonal: Bullish bias
    Put diagonal: Bearish bias
    """
    strategy = StrategyBuilder(name="Diagonal Spread")
    strategy.add_leg("sell", option_type, short_strike, near_expiry, quantity, short_premium)
    strategy.add_leg("buy", option_type, long_strike, far_expiry, quantity, long_premium)
    return strategy


# Additional popular strategies

def butterfly_spread(
    lower_strike: float,
    middle_strike: float,
    upper_strike: float,
    expiry: datetime,
    lower_premium: float,
    middle_premium: float,
    upper_premium: float,
    option_type: str = "call",
    quantity: int = 1
) -> StrategyBuilder:
    """
    Butterfly Spread - Neutral strategy
    
    Buy 1 lower strike, sell 2 middle strikes, buy 1 upper strike
    
    Max Profit: Middle Strike - Lower Strike - Net Debit
    Max Loss: Net Debit
    """
    strategy = StrategyBuilder(name="Butterfly Spread")
    strategy.add_leg("buy", option_type, lower_strike, expiry, quantity, lower_premium)
    strategy.add_leg("sell", option_type, middle_strike, expiry, quantity * 2, middle_premium)
    strategy.add_leg("buy", option_type, upper_strike, expiry, quantity, upper_premium)
    return strategy


def collar(
    underlying_price: float,
    put_strike: float,
    call_strike: float,
    expiry: datetime,
    put_premium: float,
    call_premium: float,
    stock_quantity: int = 100
) -> StrategyBuilder:
    """
    Collar - Protective strategy for stock owners
    
    Own stock + buy protective put + sell covered call
    
    Limits both upside and downside
    """
    strategy = StrategyBuilder(name="Collar")
    strategy.set_underlying_price(underlying_price)
    strategy.add_leg("buy", "put", put_strike, expiry, stock_quantity // 100, put_premium)
    strategy.add_leg("sell", "call", call_strike, expiry, stock_quantity // 100, call_premium)
    return strategy


def ratio_spread(
    long_strike: float,
    short_strike: float,
    expiry: datetime,
    long_premium: float,
    short_premium: float,
    long_quantity: int = 1,
    short_quantity: int = 2,
    option_type: str = "call"
) -> StrategyBuilder:
    """
    Ratio Spread - Directional with limited risk
    
    Buy 1, sell 2 (or other ratio) at different strikes
    
    Can be done for credit or small debit
    """
    strategy = StrategyBuilder(name="Ratio Spread")
    strategy.add_leg("buy", option_type, long_strike, expiry, long_quantity, long_premium)
    strategy.add_leg("sell", option_type, short_strike, expiry, short_quantity, short_premium)
    return strategy
