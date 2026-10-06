import os
import re
from datetime import datetime
from html import unescape
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


# ============================================================
# ENV
# ============================================================

load_dotenv()


TAVILY_API_URL = "https://api.tavily.com/search"


# ============================================================
# SOURCE QUALITY
# ============================================================

PRIMARY_DOMAINS = {
    "sebi.gov.in",
    "nseindia.com",
    "bseindia.com",
    "rbi.org.in",
    "mca.gov.in",
    "pib.gov.in",
    "indiabudget.gov.in",
}


TRUSTED_FINANCIAL_DOMAINS = {
    # Financial news / market data
    "reuters.com",
    "moneycontrol.com",
    "economictimes.indiatimes.com",
    "economictimes.com",
    "business-standard.com",
    "financialexpress.com",
    "livemint.com",
    "mint.com",
    "cnbctv18.com",
    "businessline.com",
    "thehindubusinessline.com",
    "etnownews.com",
    "ndtvprofit.com",

    # Market / broker research pages
    "zerodha.com",
    "pulse.zerodha.com",
    "upstox.com",
    "downstox.com",

    # Other useful financial reporting
    "timesofindia.indiatimes.com",
}


BLOCKED_DOMAINS = {
    "youtube.com",
    "youtu.be",
}


# ============================================================
# QUERIES THAT SHOULD NOT BE USED FOR TRADING CALLS
# ============================================================

BLOCKED_QUERY_TERMS = [
    "price prediction",
    "stock prediction",
    "nifty prediction",
    "bank nifty prediction",
    "tomorrow price",
    "target price",
    "price target",
    "will rise",
    "will fall",
    "multibagger",
    "buy signal",
    "sell signal",
    "trading call",
    "intraday call",
    "stock picks",
    "sure shot stock",
    "best stock to buy",
    "which stock should i buy",
]


# ============================================================
# DOMAIN HELPERS
# ============================================================

def get_domain(url: str) -> str:
    """
    Extract normalized hostname from a URL.
    """
    try:
        hostname = urlparse(url).hostname or ""
        hostname = hostname.lower().strip()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    except Exception:
        return ""


def domain_matches(domain: str, allowed_domain: str) -> bool:
    """
    Match exact domain or subdomain.
    """
    if not domain:
        return False

    return (
        domain == allowed_domain
        or domain.endswith("." + allowed_domain)
    )


def classify_domain(url: str) -> str:
    """
    Classify source quality.
    """

    domain = get_domain(url)

    for primary_domain in PRIMARY_DOMAINS:
        if domain_matches(domain, primary_domain):
            return "primary"

    for trusted_domain in TRUSTED_FINANCIAL_DOMAINS:
        if domain_matches(domain, trusted_domain):
            return "trusted_financial"

    for blocked_domain in BLOCKED_DOMAINS:
        if domain_matches(domain, blocked_domain):
            return "blocked"

    return "general"


# ============================================================
# QUERY SAFETY
# ============================================================

def contains_blocked_term(query: str) -> bool:
    normalized = query.lower().strip()

    return any(
        term in normalized
        for term in BLOCKED_QUERY_TERMS
    )


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(
    text: str,
    max_length: int = 2400,
) -> str:
    """
    Clean Tavily page snippets.

    Removes:
    - Markdown links
    - image links
    - HTML
    - URLs
    - navigation path fragments
    - excessive Markdown characters
    - excessive whitespace
    """

    if not text:
        return ""

    text = unescape(text)

    # Remove image markdown:
    # ![image](https://...)
    text = re.sub(
        r"!\[[^\]]*\]\([^)]+\)",
        " ",
        text,
    )

    # Convert markdown links:
    # [Economic Times](https://...)
    # -> Economic Times
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text,
    )

    # Remove navigation fragments such as:
    # [CAS]/market-data/...
    text = re.sub(
        r"\[[^\]]{1,100}\](?:/[A-Za-z0-9_.~:/?&=%+\-]+)+",
        " ",
        text,
    )

    # Remove HTML tags
    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    # Remove URLs
    text = re.sub(
        r"https?://\S+",
        " ",
        text,
    )

    # Remove Markdown formatting characters
    text = re.sub(
        r"[#*_`~]+",
        "",
        text,
    )

    # Remove escaped characters
    text = text.replace("\\n", " ")
    text = text.replace("\\t", " ")

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    if len(text) > max_length:
        text = (
            text[:max_length].rstrip()
            + "..."
        )

    return text


def clean_title(
    title: str,
    max_length: int = 180,
) -> str:
    if not title:
        return "Untitled source"

    title = unescape(title)

    title = re.sub(
        r"!\[[^\]]*\]\([^)]+\)",
        "",
        title,
    )

    title = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        title,
    )

    title = re.sub(
        r"https?://\S+",
        "",
        title,
    )

    title = re.sub(
        r"[#*_`~]+",
        "",
        title,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    ).strip()

    if len(title) > max_length:
        title = title[:max_length].rstrip() + "..."

    return title


# ============================================================
# DATE HELPERS
# ============================================================

def get_published_date(item: dict) -> str | None:
    """
    Tavily can expose publication date using different keys.
    """
    value = (
        item.get("published_date")
        or item.get("publishedDate")
        or item.get("date")
    )

    if not value:
        return None

    return str(value)


def published_timestamp(value: str | None) -> float:
    """
    Convert a publication timestamp to something sortable.
    """
    if not value:
        return 0.0

    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(
            normalized
        ).timestamp()

    except Exception:
        return 0.0


# ============================================================
# SEARCH
# ============================================================

def search_web(
    query: str,
    max_results: int = 6,
):
    """
    Search Tavily and return cleaned/ranked sources.
    """

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        print(
            "TAVILY_API_KEY is not configured."
        )

        return None

    query = query.strip()

    if not query:
        return {
            "query": query,
            "results": [],
        }

    # Financial safety
    if contains_blocked_term(query):
        print(
            f"Blocked recommendation-style query: {query}"
        )

        return {
            "query": query,
            "results": [],
            "blocked": True,
            "reason": (
                "Prediction or direct trading "
                "recommendation queries are not supported."
            ),
        }

    payload = {
        "query": query,
        "search_depth": "advanced",
        "topic": "general",
        "max_results": max(
            1,
            min(max_results, 10),
        ),
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            TAVILY_API_URL,
            json=payload,
            headers=headers,
            timeout=25,
        )

        if response.status_code != 200:
            print(
                "Tavily API error:",
                response.status_code,
                response.text,
            )

            return None

        data = response.json()

        raw_results = (
            data.get("results")
            or []
        )

        results = []

        for item in raw_results:

            url = (
                item.get("url")
                or ""
            ).strip()

            if not url:
                continue

            source_type = classify_domain(url)

            # Do not show blocked sources.
            if source_type == "blocked":
                continue

            title = clean_title(
                item.get("title")
                or "Untitled source"
            )

            content = clean_text(
                item.get("content")
                or ""
            )

            domain = get_domain(url)

            published_date = get_published_date(
                item
            )

            score = item.get("score")

            if score is None:
                score = 0

            # Quality score used internally for ranking.
            if source_type == "primary":
                quality_score = 4

            elif source_type == "trusted_financial":
                quality_score = 3

            else:
                quality_score = 1

            results.append(
                {
                    "title": title,
                    "url": url,
                    "content": content,
                    "domain": domain,

                    # Keep both fields so older frontend/backend
                    # code remains compatible.
                    "sourceType": source_type,
                    "quality": source_type,

                    "score": score,
                    "qualityScore": quality_score,

                    "publishedDate": published_date,
                }
            )

        # Rank:
        # 1. official / primary
        # 2. trusted financial
        # 3. general
        # 4. search score
        # 5. publication date
        results.sort(
            key=lambda item: (
                -item.get(
                    "qualityScore",
                    1,
                ),
                -(item.get("score") or 0),
                -published_timestamp(
                    item.get("publishedDate")
                ),
            )
        )

        return {
            "query": query,
            "results": results,
            "blocked": False,
        }

    except requests.RequestException as error:
        print(
            "Tavily request failed:",
            error,
        )

        return None

    except ValueError as error:
        print(
            "Tavily returned invalid JSON:",
            error,
        )

        return None

    except Exception as error:
        print(
            "Unexpected Tavily search error:",
            error,
        )

        return None


# ============================================================
# MULTI SEARCH
# ============================================================

def search_multiple(
    queries: list[str],
    max_results_per_query: int = 5,
):
    """
    Run multiple searches and combine results.

    Duplicate URLs are removed.
    """

    all_results = []
    search_errors = []

    seen_urls = set()

    for query in queries:

        query = query.strip()

        if not query:
            continue

        result = search_web(
            query=query,
            max_results=max_results_per_query,
        )

        if result is None:

            search_errors.append(
                {
                    "query": query,
                    "error": "Search request failed",
                }
            )

            continue

        if result.get("blocked"):

            search_errors.append(
                {
                    "query": query,
                    "error": result.get(
                        "reason",
                        "Search query blocked.",
                    ),
                }
            )

            continue

        for item in result.get(
            "results",
            [],
        ):

            url = (
                item.get("url")
                or ""
            ).strip()

            if not url:
                continue

            normalized_url = (
                url.rstrip("/")
                .lower()
            )

            if normalized_url in seen_urls:
                continue

            seen_urls.add(
                normalized_url
            )

            all_results.append(item)

    all_results.sort(
        key=lambda item: (
            -item.get(
                "qualityScore",
                1,
            ),
            -(item.get("score") or 0),
            -published_timestamp(
                item.get("publishedDate")
            ),
        )
    )

    # Prevent enormous LLM prompts.
    all_results = all_results[:12]

    return {
        "results": all_results,
        "errors": search_errors,
    }