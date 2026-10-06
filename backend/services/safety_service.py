import re


RESTRICTED_PATTERNS = [
    r"\bshould i buy\b",
    r"\bshould i sell\b",
    r"\bshould i hold\b",
    r"\bshould we buy\b",
    r"\bshould we sell\b",
    r"\bbuy this stock\b",
    r"\bsell this stock\b",
    r"\bwhat stock should i buy\b",
    r"\bwhich stock should i buy\b",
    r"\bwhat should i invest in\b",
    r"\bwhere should i invest\b",
    r"\bwhere to invest\b",
    r"\bstocks to buy\b",
    r"\bstocks to sell\b",
    r"\bstocks that will double\b",
    r"\bwhich stock will rise\b",
    r"\bwhich stock will fall\b",
    r"\bprice target\b",
    r"\btarget price\b",
    r"\btomorrow.?s price\b",
    r"\bnext week.?s price\b",
    r"\bfuture price\b",
    r"\bguaranteed return\b",
    r"\bguaranteed profit\b",
    r"\bmultibagger\b",
    r"\bportfolio advice\b",
    r"\bmy portfolio\b.*\bwhat should\b",
    r"\binvest\s+₹?\s*\d+",
    r"\binvest\s+rs\.?\s*\d+",
    r"\bwhere should i put\b.*\bmoney\b",
]


def is_restricted_query(
    query: str,
) -> bool:

    normalized = (
        query
        .lower()
        .strip()
    )

    for pattern in RESTRICTED_PATTERNS:

        if re.search(
            pattern,
            normalized,
        ):
            return True

    return False


def safety_response():
    return {
        "answer": (
            "I can help with educational and "
            "informational market research, but I "
            "can't provide personalized buy, sell, "
            "hold, price-target, or guaranteed-return "
            "recommendations.\n\n"
            "Instead, I can analyze the company's "
            "recent performance, financial metrics, "
            "news, historical data, risks, and the "
            "evidence behind a market movement."
        ),
        "type": "financial_advice_restricted",
        "restricted": True,
        "evidenceLevel": "not_applicable",
        "results": [],
        "searchQueries": [],
        "searchErrors": [],
        "marketData": [],
    }