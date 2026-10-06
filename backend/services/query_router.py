import re


# ============================================================
# Known Indian companies
# ============================================================

COMPANIES = {
    "TATA CONSULTANCY SERVICES": "TCS",
    "TCS": "TCS",

    "RELIANCE INDUSTRIES": "RELIANCE",
    "RELIANCE": "RELIANCE",

    "INFOSYS": "INFY",
    "INFY": "INFY",

    "HDFC BANK": "HDFCBANK",
    "HDFC": "HDFCBANK",
    "HDFCBANK": "HDFCBANK",

    "ICICI BANK": "ICICIBANK",
    "ICICI": "ICICIBANK",
    "ICICIBANK": "ICICIBANK",

    "STATE BANK OF INDIA": "SBIN",
    "SBI": "SBIN",
    "SBIN": "SBIN",

    "AXIS BANK": "AXISBANK",
    "AXIS": "AXISBANK",
    "AXISBANK": "AXISBANK",

    "KOTAK BANK": "KOTAKBANK",
    "KOTAK": "KOTAKBANK",
    "KOTAKBANK": "KOTAKBANK",

    "ITC": "ITC",

    "WIPRO": "WIPRO",

    "HCL TECHNOLOGIES": "HCLTECH",
    "HCL": "HCLTECH",
    "HCLTECH": "HCLTECH",

    "BHARTI AIRTEL": "BHARTIARTL",
    "AIRTEL": "BHARTIARTL",
    "BHARTIARTL": "BHARTIARTL",

    "TATA MOTORS": "TATAMOTORS",
    "TATAMOTORS": "TATAMOTORS",

    "TATA STEEL": "TATASTEEL",
    "TATASTEEL": "TATASTEEL",

    "MARUTI SUZUKI": "MARUTI",
    "MARUTI": "MARUTI",

    "SUN PHARMA": "SUNPHARMA",
    "SUNPHARMA": "SUNPHARMA",

    "ADANI ENTERPRISES": "ADANIENT",
    "ADANI": "ADANIENT",
    "ADANIENT": "ADANIENT",

    "ADANI PORTS": "ADANIPORTS",
    "ADANIPORTS": "ADANIPORTS",

    "BAJAJ FINANCE": "BAJFINANCE",
    "BAJFINANCE": "BAJFINANCE",

    "BAJAJ FINSERV": "BAJAJFINSV",
    "BAJAJFINSV": "BAJAJFINSV",

    "LARSEN": "LT",
    "L&T": "LT",
    "LT": "LT",

    "HINDUSTAN UNILEVER": "HINDUNILVR",
    "HUL": "HINDUNILVR",
    "HINDUNILVR": "HINDUNILVR",
}


# ============================================================
# Market keywords
# ============================================================

MARKET_KEYWORDS = [
    "nifty",
    "nifty 50",
    "sensex",
    "bank nifty",
    "market",
    "indian market",
    "stock market",
    "share market",
    "indices",
    "index",
]


# ============================================================
# Sector keywords
# ============================================================

SECTORS = {
    "it": [
        "it stocks",
        "it sector",
        "technology stocks",
        "technology sector",
    ],
    "banking": [
        "banking stocks",
        "banking sector",
        "bank stocks",
    ],
    "pharma": [
        "pharma stocks",
        "pharma sector",
        "pharmaceutical stocks",
    ],
    "auto": [
        "auto stocks",
        "auto sector",
        "automobile stocks",
    ],
    "financial": [
        "financial stocks",
        "financial sector",
    ],
    "metal": [
        "metal stocks",
        "metal sector",
    ],
    "energy": [
        "energy stocks",
        "energy sector",
    ],
    "fmcg": [
        "fmcg stocks",
        "fmcg sector",
    ],
}


# ============================================================
# News keywords
# ============================================================

NEWS_KEYWORDS = [
    "news",
    "latest",
    "today",
    "recent",
    "recently",
    "update",
    "updates",
    "announcement",
    "announcements",
    "headline",
    "headlines",
    "why did",
    "why is",
    "why are",
    "fell",
    "fall",
    "fallen",
    "dropped",
    "drop",
    "rose",
    "rise",
    "rising",
    "surged",
    "surge",
    "declined",
    "decline",
    "crashed",
    "crash",
    "jumped",
    "jump",
]


# ============================================================
# Education keywords
# ============================================================

EDUCATION_KEYWORDS = [
    "what is",
    "what are",
    "explain",
    "meaning of",
    "define",
    "definition",
    "how does",
    "how do",
    "learn",
    "teach me",
    "concept",
    "basics",
    "beginner",
]


FINANCE_CONCEPTS = [
    "pe ratio",
    "p/e ratio",
    "pb ratio",
    "p/b ratio",
    "eps",
    "roe",
    "roce",
    "dividend",
    "dividend yield",
    "market cap",
    "market capitalization",
    "revenue",
    "profit",
    "ebitda",
    "cash flow",
    "debt to equity",
    "debt equity",
    "repo rate",
    "interest rate",
    "inflation",
    "gdp",
    "ipo",
    "fpo",
    "mutual fund",
    "etf",
    "stock split",
    "bonus shares",
]


# ============================================================
# Comparison keywords
# ============================================================

COMPARISON_KEYWORDS = [
    "compare",
    "comparison",
    "vs",
    "versus",
    "difference between",
    "better than",
    "against",
]


# ============================================================
# Helpers
# ============================================================

def normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


def find_companies(query: str):
    """
    Detect companies in the order they appear in the
    user's original question.
    """

    normalized = normalize_query(query)

    matches = []

    for name, symbol in COMPANIES.items():

        position = normalized.find(
            name.lower()
        )

        if position >= 0:

            matches.append(
                {
                    "position": position,
                    "symbol": symbol,
                }
            )

    matches.sort(
        key=lambda item: item["position"]
    )

    found = []

    for item in matches:

        symbol = item["symbol"]

        if symbol not in found:
            found.append(symbol)

    return found


def contains_any(
    query: str,
    keywords: list[str],
):
    normalized = normalize_query(query)

    return any(
        keyword.lower() in normalized
        for keyword in keywords
    )


def detect_sector(query: str):

    normalized = normalize_query(query)

    for sector, keywords in SECTORS.items():

        if any(
            keyword.lower() in normalized
            for keyword in keywords
        ):
            return sector

    return None


# ============================================================
# Classification
# ============================================================

def classify_query(query: str):

    normalized = normalize_query(query)

    companies = find_companies(
        normalized
    )

    is_comparison = contains_any(
        normalized,
        COMPARISON_KEYWORDS,
    )

    is_education = (
        contains_any(
            normalized,
            EDUCATION_KEYWORDS,
        )
        or contains_any(
            normalized,
            FINANCE_CONCEPTS,
        )
    )

    is_market = contains_any(
        normalized,
        MARKET_KEYWORDS,
    )

    sector = detect_sector(
        normalized
    )

    is_news = contains_any(
        normalized,
        NEWS_KEYWORDS,
    )

    if (
        is_comparison
        and len(companies) >= 2
    ):
        query_type = "comparison"

    elif (
        is_education
        and not companies
    ):
        query_type = "education"

    elif (
        is_market
        and not companies
    ):
        query_type = "market"

    elif (
        sector
        and not companies
    ):
        query_type = "sector"

    elif (
        companies
        and is_news
    ):
        query_type = "stock_news"

    elif companies:
        query_type = "stock"

    elif is_news:
        query_type = "news"

    else:
        query_type = "general"

    return {
        "type": query_type,
        "companies": companies,
        "primary_company": (
            companies[0]
            if companies
            else None
        ),
        "sector": sector,
        "is_comparison": is_comparison,
    }


# ============================================================
# Search queries
# ============================================================

def build_search_queries(
    query: str,
    query_type: str,
    companies=None,
    sector=None,
):

    companies = companies or []

    queries = []

    if query_type == "stock_news":

        for company in companies[:2]:

            queries.extend(
                [
                    f"{company} latest news India stock",
                    f"{company} recent stock price movement India",
                    f"{company} latest company announcement",
                ]
            )

    elif query_type == "stock":

        for company in companies[:2]:

            queries.append(
                f"{company} latest stock news India"
            )

    elif query_type == "market":

        queries.extend(
            [
                "Indian stock market latest news NIFTY Sensex",
                "NIFTY 50 latest market news India",
                "Sensex latest market news India",
            ]
        )

    elif query_type == "sector":

        sector_name = sector or "stock"

        queries.extend(
            [
                f"Indian {sector_name} sector latest news stocks",
                f"Indian {sector_name} stocks latest developments",
                f"Indian {sector_name} sector market today",
            ]
        )

    elif query_type == "education":

        queries.append(query)

    elif query_type == "comparison":

        if len(companies) >= 2:

            first = companies[0]
            second = companies[1]

            queries.extend(
                [
                    f"{first} vs {second} India stocks",
                    f"{first} {second} latest company news",
                ]
            )

        else:
            queries.append(query)

    elif query_type == "news":

        queries.extend(
            [
                f"{query} latest India",
                f"{query} latest news",
            ]
        )

    else:

        queries.append(query)

    unique_queries = []

    for item in queries:

        cleaned = item.strip()

        if (
            cleaned
            and cleaned not in unique_queries
        ):
            unique_queries.append(
                cleaned
            )

    return unique_queries[:5]