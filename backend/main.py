import os
import re
import time

from collections import defaultdict, deque
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


from services.stock_service import (
    get_stock_quote,
    get_stock_history,
    resolve_symbol,
)

from services.search_service import (
    search_web,
    search_multiple,
)

from services.llm_service import (
    generate_answer,
)


# ============================================================
# ENV
# ============================================================

load_dotenv()


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="SentiNews API",
    version="1.2.0",
)


# ============================================================
# CORS
# ============================================================

frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000",
).strip()


allowed_origins = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}

if frontend_url:
    allowed_origins.add(frontend_url)


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(
        allowed_origins
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# RATE LIMIT
# ============================================================

RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW = 60

request_log = defaultdict(
    deque
)


def enforce_rate_limit(
    request: Request,
):
    ip = "unknown"

    if request.client:
        ip = request.client.host

    now = time.time()

    timestamps = request_log[ip]

    while timestamps:
        if (
            now - timestamps[0]
            > RATE_LIMIT_WINDOW
        ):
            timestamps.popleft()

        else:
            break

    if len(timestamps) >= RATE_LIMIT_REQUESTS:

        raise HTTPException(
            status_code=429,
            detail=(
                "Too many requests. "
                "Please try again shortly."
            ),
        )

    timestamps.append(now)


# ============================================================
# TIME
# ============================================================

def india_now():
    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    )


def today_label():
    return india_now().strftime(
        "%d %B %Y"
    )


def current_time_label():
    return india_now().strftime(
        "%d %B %Y, %I:%M %p IST"
    )


# ============================================================
# COMPANY ALIASES
# ============================================================

COMPANY_ALIASES = {
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
# COMPANY DETECTION
# ============================================================

def detect_companies(
    text: str,
):
    """
    Detect known Indian companies.

    Returns:
        [
            "TCS",
            "INFY"
        ]
    """

    text_upper = text.upper()

    found = []

    for alias, symbol in COMPANY_ALIASES.items():

        pattern = (
            r"(?<![A-Z0-9])"
            + re.escape(alias)
            + r"(?![A-Z0-9])"
        )

        match = re.search(
            pattern,
            text_upper,
        )

        if match:
            found.append(
                (
                    match.start(),
                    symbol,
                )
            )

    found.sort(
        key=lambda item: item[0]
    )

    companies = []

    for _, symbol in found:

        if symbol not in companies:
            companies.append(symbol)

    return companies


# ============================================================
# FOLLOW-UP CONTEXT
# ============================================================

def latest_user_message(
    history,
):
    if not history:
        return ""

    for turn in reversed(history):

        if turn.get("role") == "user":

            return (
                turn.get("content")
                or ""
            )

    return ""


# ============================================================
# QUERY ROUTER
# ============================================================

def route_query(
    query: str,
    history=None,
):
    query_clean = query.strip()

    query_lower = (
        query_clean.lower()
    )

    previous_user = latest_user_message(
        history or []
    )

    routing_text = (
        query_clean
        + " "
        + previous_user
    )

    companies = detect_companies(
        routing_text
    )

    current_market_patterns = [
        "today",
        "today's",
        "todays",
        "right now",
        "currently",
        "current market",
        "what happened in the market",
        "what happened in today's market",
        "what is happening in the market",
        "what is happening with the market",
        "how is the market",
        "how are markets",
        "market today",
        "nifty today",
        "sensex today",
    ]

    comparison_patterns = [
        "compare",
        "comparison",
        "vs ",
        " versus ",
        "better than",
        "difference between",
    ]

    sector_terms = [
        "it stocks",
        "banking stocks",
        "bank stocks",
        "pharma stocks",
        "pharmaceutical stocks",
        "auto stocks",
        "automobile stocks",
        "metal stocks",
        "metals stocks",
        "fmcg stocks",
        "energy stocks",
        "financial stocks",
        "realty stocks",
        "real estate stocks",
        "psu stocks",
        "private banks",
        "public sector banks",
    ]

    education_patterns = [
        "what is",
        "what are",
        "explain",
        "meaning of",
        "define",
        "how does",
        "how do",
        "why is",
        "why are",
        "formula",
        "concept",
        "difference between",
    ]

    news_patterns = [
        "news",
        "latest",
        "recent",
        "today",
        "why did",
        "why has",
        "why is",
        "fell",
        "fall",
        "falling",
        "dropped",
        "drop",
        "rose",
        "rising",
        "surged",
        "surge",
        "jumped",
        "jump",
        "movement",
        "move",
        "moving",
        "announcement",
        "results",
        "earnings",
    ]

    safety_patterns = [
        "should i buy",
        "should i sell",
        "buy or sell",
        "which stock should",
        "best stock to buy",
        "best stock for",
        "give me a target",
        "price target",
        "target price",
        "will it rise",
        "will it fall",
        "predict",
        "prediction",
        "guaranteed return",
    ]

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    if any(
        pattern in query_lower
        for pattern in safety_patterns
    ):
        return {
            "queryType": "safety",
            "companies": companies,
            "primaryCompany": (
                companies[0]
                if companies
                else None
            ),
        }

    # --------------------------------------------------------
    # CURRENT MARKET
    # --------------------------------------------------------

    if any(
        pattern in query_lower
        for pattern in current_market_patterns
    ):
        return {
            "queryType": "market",
            "companies": [],
            "primaryCompany": None,
        }

    # --------------------------------------------------------
    # SECTOR
    # --------------------------------------------------------

    if any(
        term in query_lower
        for term in sector_terms
    ):
        return {
            "queryType": "sector",
            "companies": companies,
            "primaryCompany": (
                companies[0]
                if companies
                else None
            ),
        }

    # --------------------------------------------------------
    # COMPARISON
    # --------------------------------------------------------

    if any(
        pattern in query_lower
        for pattern in comparison_patterns
    ):

        return {
            "queryType": "comparison",
            "companies": companies,
            "primaryCompany": (
                companies[0]
                if companies
                else None
            ),
        }

    # --------------------------------------------------------
    # EDUCATION
    # --------------------------------------------------------

    # Educational questions without a stock movement
    # should remain educational.
    if any(
        pattern in query_lower
        for pattern in education_patterns
    ) and not any(
        pattern in query_lower
        for pattern in news_patterns
    ):
        return {
            "queryType": "education",
            "companies": companies,
            "primaryCompany": (
                companies[0]
                if companies
                else None
            ),
        }

    # --------------------------------------------------------
    # STOCK NEWS
    # --------------------------------------------------------

    if companies:

        if any(
            pattern in query_lower
            for pattern in news_patterns
        ):
            return {
                "queryType": "stock_news",
                "companies": companies,
                "primaryCompany": companies[0],
            }

        return {
            "queryType": "stock",
            "companies": companies,
            "primaryCompany": companies[0],
        }

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return {
        "queryType": "education",
        "companies": [],
        "primaryCompany": None,
    }


# ============================================================
# SEARCH QUERY BUILDER
# ============================================================

def build_search_queries(
    query: str,
    query_type: str,
    companies: list[str],
):
    date = today_label()

    # --------------------------------------------------------
    # CURRENT MARKET
    # --------------------------------------------------------

    if query_type == "market":

        return [
            (
                "Indian stock market today "
                "Nifty 50 Sensex live "
                f"{date}"
            ),
            (
                "Nifty 50 today live "
                "market update "
                f"{date}"
            ),
            (
                "Sensex today live "
                "market update "
                f"{date}"
            ),
            (
                "Indian stock market today "
                "sectors banks IT "
                f"{date}"
            ),
        ]

    # --------------------------------------------------------
    # STOCK NEWS
    # --------------------------------------------------------

    if query_type == "stock_news":

        symbol = (
            companies[0]
            if companies
            else ""
        )

        return [
            (
                f"{symbol} latest stock news India "
                f"{date}"
            ),
            (
                f"{symbol} today stock price "
                f"movement news India {date}"
            ),
            (
                f"{symbol} company announcement "
                f"latest India {date}"
            ),
        ]

    # --------------------------------------------------------
    # STOCK
    # --------------------------------------------------------

    if query_type == "stock":

        symbol = (
            companies[0]
            if companies
            else ""
        )

        return [
            (
                f"{symbol} latest stock information "
                f"India {date}"
            ),
            (
                f"{symbol} latest news India "
                f"{date}"
            ),
        ]

    # --------------------------------------------------------
    # SECTOR
    # --------------------------------------------------------

    if query_type == "sector":

        return [
            (
                f"Indian sector stocks today "
                f"{query} {date}"
            ),
            (
                f"{query} India stock market "
                f"latest news {date}"
            ),
            (
                f"Indian stocks sector performance "
                f"{date}"
            ),
        ]

    # --------------------------------------------------------
    # COMPARISON
    # --------------------------------------------------------

    if query_type == "comparison":

        if len(companies) >= 2:

            first = companies[0]
            second = companies[1]

            return [
                (
                    f"{first} vs {second} "
                    f"latest India stocks {date}"
                ),
                (
                    f"{first} {second} "
                    f"latest news performance {date}"
                ),
            ]

        return [
            f"{query} India stocks {date}"
        ]

    # --------------------------------------------------------
    # EDUCATION
    # --------------------------------------------------------

    if query_type == "education":

        return [
            query
        ]

    return [
        query
    ]


# ============================================================
# STOCK MARKET DATA
# ============================================================

def build_market_data(
    companies: list[str],
):
    market_data = []

    for symbol in companies:

        try:
            quote = get_stock_quote(
                symbol
            )

        except Exception as error:
            print(
                f"Stock quote failed for {symbol}:",
                error,
            )
            continue

        if not quote:
            continue

        last = quote.get("last")
        previous_close = quote.get(
            "previousClose"
        )

        change = None
        change_percent = None

        try:

            if (
                last is not None
                and previous_close is not None
            ):

                last_value = float(last)
                previous_value = float(
                    previous_close
                )

                change = (
                    last_value
                    - previous_value
                )

                if previous_value != 0:

                    change_percent = (
                        change
                        / previous_value
                    ) * 100

        except (
            TypeError,
            ValueError,
        ):
            change = None
            change_percent = None

        quote["change"] = change
        quote["changePercent"] = (
            change_percent
        )

        market_data.append(
            {
                "symbol": symbol,
                "exchange": "NSE",

                "dataSource": "TejHQ",
                "dataType": "EOD",

                "quote": quote,

                "freshness": {
                    "label": (
                        "Latest trading-day EOD"
                    ),
                    "isLive": False,
                },
            }
        )

    return market_data


# ============================================================
# EVIDENCE
# ============================================================

def build_evidence(
    results,
):
    primary_count = 0
    financial_count = 0

    for result in results:

        source_type = (
            result.get(
                "sourceType"
            )
            or result.get(
                "quality"
            )
            or "general"
        )

        if source_type == "primary":
            primary_count += 1

        elif source_type == "trusted_financial":
            financial_count += 1

    total = len(results)

    if (
        primary_count >= 1
        or financial_count >= 2
    ):
        level = "Strong evidence"

    elif (
        financial_count >= 1
        or total >= 3
    ):
        level = "Good evidence"

    else:
        level = "Limited evidence"

    return {
        "level": level,
        "primary": primary_count,
        "financial": financial_count,
        "total": total,
    }


# ============================================================
# SAFETY ANSWER
# ============================================================

def safety_answer():
    return (
        "I can help explain the stock, company news, "
        "valuation, historical performance, or market "
        "factors behind a move, but I won't provide a "
        "personalized buy/sell recommendation, price target, "
        "or guaranteed prediction."
    )


# ============================================================
# MODELS
# ============================================================

class HistoryTurn(BaseModel):
    role: Literal[
        "user",
        "assistant",
    ]

    content: str


class AskRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    history: list[HistoryTurn] = Field(
        default_factory=list
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "name": "SentiNews API",
        "version": "1.2.0",
        "status": "running",
        "docs": "/docs",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "SentiNews",
        "version": "1.2.0",
        "indiaTime": current_time_label(),
    }


# ============================================================
# STOCK QUOTE
# ============================================================

@app.get(
    "/api/stocks/{symbol}"
)
async def stock_quote(
    symbol: str,
    request: Request,
):

    enforce_rate_limit(request)

    resolved_symbol = resolve_symbol(
        symbol
    )

    quote = get_stock_quote(
        resolved_symbol
    )

    if not quote:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No stock data found "
                f"for {symbol}"
            ),
        )

    previous_close = quote.get(
        "previousClose"
    )

    last = quote.get(
        "last"
    )

    change = None
    change_percent = None

    try:

        if (
            last is not None
            and previous_close is not None
        ):

            last_value = float(last)
            previous_value = float(
                previous_close
            )

            change = (
                last_value
                - previous_value
            )

            if previous_value != 0:
                change_percent = (
                    change
                    / previous_value
                ) * 100

    except (
        TypeError,
        ValueError,
    ):
        pass

    quote["change"] = change
    quote["changePercent"] = (
        change_percent
    )

    return {
        "symbol": resolved_symbol,
        "dataType": "EOD",
        "dataSource": "TejHQ",
        "quote": quote,
    }


# ============================================================
# STOCK HISTORY
# ============================================================

@app.get(
    "/api/stocks/{symbol}/history"
)
async def stock_history(
    symbol: str,
    days: int = 90,
    request: Request = None,
):

    if request:
        enforce_rate_limit(request)

    if days not in [30, 90]:
        days = 90

    resolved_symbol = resolve_symbol(
        symbol
    )

    history = get_stock_history(
        resolved_symbol,
        days=days,
    )

    if not history:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No historical data found "
                f"for {symbol}"
            ),
        )

    return {
        **history,
        "dataType": "EOD",
        "dataSource": "TejHQ",
    }


# ============================================================
# GENERIC SEARCH
# ============================================================

@app.get("/api/search")
async def generic_search(
    q: str,
    request: Request,
):

    enforce_rate_limit(request)

    query = q.strip()

    if not query:

        raise HTTPException(
            status_code=400,
            detail="Search query is required.",
        )

    result = search_web(
        query=query,
        max_results=6,
    )

    if result is None:

        raise HTTPException(
            status_code=502,
            detail="Web search failed.",
        )

    return result


# ============================================================
# MAIN AI RESEARCH ENDPOINT
# ============================================================

@app.post("/api/ask")
async def ask(
    request_body: AskRequest,
    request: Request,
):

    enforce_rate_limit(request)

    query = (
        request_body.query
        .strip()
    )

    history = [
        turn.model_dump()
        for turn in request_body.history
    ]

    if not query:

        raise HTTPException(
            status_code=400,
            detail="Question is required.",
        )

    # --------------------------------------------------------
    # ROUTE
    # --------------------------------------------------------

    route = route_query(
        query=query,
        history=history,
    )

    query_type = route[
        "queryType"
    ]

    companies = route[
        "companies"
    ]

    primary_company = route[
        "primaryCompany"
    ]

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    if query_type == "safety":

        return {
            "query": query,
            "queryType": query_type,
            "companies": companies,
            "primaryCompany": primary_company,

            "answer": safety_answer(),

            "model": None,

            "results": [],

            "searchErrors": [],

            "searchQueries": [],

            "marketData": [],

            "evidence": {
                "level": "No web research required",
                "primary": 0,
                "financial": 0,
                "total": 0,
            },

            "disclaimer": (
                "SentiNews provides informational "
                "and educational research, not "
                "personalized investment advice."
            ),
        }

    # --------------------------------------------------------
    # SEARCH QUERIES
    # --------------------------------------------------------

    search_queries = build_search_queries(
        query=query,
        query_type=query_type,
        companies=companies,
    )

    # --------------------------------------------------------
    # WEB SEARCH
    # --------------------------------------------------------

    search_result = search_multiple(
        queries=search_queries,
        max_results_per_query=5,
    )

    results = search_result.get(
        "results",
        [],
    )

    search_errors = search_result.get(
        "errors",
        [],
    )

    # --------------------------------------------------------
    # STRUCTURED STOCK DATA
    # --------------------------------------------------------

    market_data = []

    if query_type in {
        "stock",
        "stock_news",
        "comparison",
    }:

        market_data = build_market_data(
            companies
        )

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    evidence = build_evidence(
        results
    )

    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------

    try:

        llm_result = generate_answer(
            query=query,
            query_type=query_type,
            company=primary_company,
            results=results,
            market_data=market_data,
            conversation_history=history,
        )

        answer = llm_result.get(
            "answer",
            "",
        )

        model = llm_result.get(
            "model"
        )

    except Exception as error:

        print(
            "LLM generation failed:",
            error,
        )

        raise HTTPException(
            status_code=502,
            detail=str(error),
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "query": query,

        "queryType": query_type,

        "companies": companies,

        "primaryCompany": primary_company,

        "answer": answer,

        "model": model,

        "results": results,

        "searchErrors": search_errors,

        "searchQueries": search_queries,

        "marketData": market_data,

        "evidence": evidence,

        "timestamp": current_time_label(),

        "disclaimer": (
            "SentiNews provides informational "
            "and educational research, not "
            "personalized investment advice."
        ),
    }