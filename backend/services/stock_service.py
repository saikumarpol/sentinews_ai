import requests
from datetime import date, timedelta


BASE_URL = "https://api.tejhq.dev"


# ============================================================
# COMMON INDIAN STOCK SYMBOLS
# ============================================================

STOCK_ALIASES = {
    # Major companies
    "RELIANCE": "RELIANCE",
    "RELIANCE INDUSTRIES": "RELIANCE",

    "INFOSYS": "INFY",
    "INFY": "INFY",

    "TCS": "TCS",
    "TATA CONSULTANCY SERVICES": "TCS",

    "HDFC": "HDFCBANK",
    "HDFC BANK": "HDFCBANK",
    "HDFCBANK": "HDFCBANK",

    "ICICI": "ICICIBANK",
    "ICICI BANK": "ICICIBANK",
    "ICICIBANK": "ICICIBANK",

    "SBI": "SBIN",
    "STATE BANK OF INDIA": "SBIN",
    "SBIN": "SBIN",

    "AXIS": "AXISBANK",
    "AXIS BANK": "AXISBANK",
    "AXISBANK": "AXISBANK",

    "KOTAK": "KOTAKBANK",
    "KOTAK BANK": "KOTAKBANK",
    "KOTAKBANK": "KOTAKBANK",

    "ITC": "ITC",

    "BHARTI AIRTEL": "BHARTIARTL",
    "AIRTEL": "BHARTIARTL",
    "BHARTIARTL": "BHARTIARTL",

    "TATA MOTORS": "TATAMOTORS",
    "TATAMOTORS": "TATAMOTORS",

    "TATA STEEL": "TATASTEEL",
    "TATASTEEL": "TATASTEEL",

    "LARSEN": "LT",
    "L&T": "LT",
    "LT": "LT",

    "HINDUSTAN UNILEVER": "HINDUNILVR",
    "HUL": "HINDUNILVR",
    "HINDUNILVR": "HINDUNILVR",

    "MARUTI": "MARUTI",
    "MARUTI SUZUKI": "MARUTI",

    "SUN PHARMA": "SUNPHARMA",
    "SUNPHARMA": "SUNPHARMA",

    "WIPRO": "WIPRO",

    "HCL": "HCLTECH",
    "HCL TECHNOLOGIES": "HCLTECH",
    "HCLTECH": "HCLTECH",

    "ADANI": "ADANIENT",
    "ADANI ENTERPRISES": "ADANIENT",
    "ADANIENT": "ADANIENT",

    "ADANI PORTS": "ADANIPORTS",
    "ADANIPORTS": "ADANIPORTS",

    "BAJAJ FINANCE": "BAJFINANCE",
    "BAJFINANCE": "BAJFINANCE",

    "BAJAJ FINSERV": "BAJAJFINSV",
    "BAJAJFINSV": "BAJAJFINSV",
}


# ============================================================
# SYMBOL RESOLVER
# ============================================================

def resolve_symbol(user_input: str) -> str:
    """
    Convert a user's company name / alias into an NSE symbol.

    Examples:

    Infosys -> INFY
    HDFC -> HDFCBANK
    SBI -> SBIN
    Reliance Industries -> RELIANCE
    """

    cleaned = (
        user_input
        .strip()
        .upper()
    )

    return STOCK_ALIASES.get(
        cleaned,
        cleaned,
    )


# ============================================================
# LATEST STOCK QUOTE
# ============================================================

def get_stock_quote(symbol: str):

    symbol = resolve_symbol(symbol)

    url = (
        f"{BASE_URL}/v1/ohlcv/nse/"
        f"{symbol}"
    )

    try:

        response = requests.get(
            url,
            timeout=10,
        )

        if response.status_code != 200:

            print(
                "Tej API error:",
                response.status_code,
            )

            print(
                response.text
            )

            return None

        result = response.json()

        data = result.get(
            "data",
            [],
        )

        if not data:
            return None

        latest = data[-1]

        return {
            "symbol": symbol,
            "date": latest.get("date"),
            "open": latest.get("open"),
            "high": latest.get("high"),
            "low": latest.get("low"),
            "close": latest.get("close"),
            "last": latest.get("last"),
            "previousClose": latest.get(
                "prev_close"
            ),
            "volume": latest.get("volume"),
            "turnover": latest.get(
                "turnover"
            ),
            "trades": latest.get(
                "trades"
            ),
        }

    except requests.RequestException as error:

        print(
            "Stock API request failed:",
            error,
        )

        return None


# ============================================================
# STOCK HISTORY
# ============================================================

def get_stock_history(
    symbol: str,
    days: int = 90,
):

    symbol = resolve_symbol(symbol)

    if days not in [30, 90]:
        days = 90

    today = date.today()

    start_date = (
        today -
        timedelta(days=days)
    )

    url = (
        f"{BASE_URL}/v1/ohlcv/nse/"
        f"{symbol}"
    )

    params = {
        "from": start_date.isoformat(),
        "to": today.isoformat(),
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        if response.status_code != 200:

            print(
                "Tej history API error:",
                response.status_code,
            )

            print(
                response.text
            )

            return None

        result = response.json()

        data = result.get(
            "data",
            [],
        )

        if not data:
            return None

        history = []

        for row in data:

            history.append(
                {
                    "date": row.get(
                        "date"
                    ),
                    "open": row.get(
                        "open"
                    ),
                    "high": row.get(
                        "high"
                    ),
                    "low": row.get(
                        "low"
                    ),
                    "close": row.get(
                        "close"
                    ),
                    "volume": row.get(
                        "volume"
                    ),
                }
            )

        return {
            "symbol": symbol,
            "days": days,
            "data": history,
        }

    except requests.RequestException as error:

        print(
            "Stock history request failed:",
            error,
        )

        return None