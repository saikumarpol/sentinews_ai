from datetime import date, datetime
from typing import Any

from services.stock_service import (
    get_stock_quote,
    get_stock_history,
)


def parse_date(value: Any):
    if not value:
        return None

    if isinstance(value, date):
        return value

    text = str(value).strip()

    try:
        return datetime.fromisoformat(
            text
        ).date()
    except ValueError:
        pass

    try:
        return datetime.strptime(
            text,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        return None


def business_days_between(
    start: date,
    end: date,
) -> int:

    if start >= end:
        return 0

    count = 0
    current = start

    while current < end:
        current = current.fromordinal(
            current.toordinal() + 1
        )

        if current.weekday() < 5:
            count += 1

    return count


def get_freshness(
    quote: dict[str, Any],
) -> dict[str, Any]:

    data_date = parse_date(
        quote.get("date")
    )

    today = date.today()

    if not data_date:
        return {
            "status": "unknown",
            "label": "Date unavailable",
            "calendarDaysOld": None,
            "businessDaysOld": None,
        }

    calendar_days_old = (
        today - data_date
    ).days

    business_days_old = (
        business_days_between(
            data_date,
            today,
        )
    )

    if calendar_days_old <= 1:
        status = "current_eod"
        label = "Latest trading-day EOD"

    elif business_days_old <= 1:
        status = "previous_eod"
        label = "Previous trading-day EOD"

    else:
        status = "stale_eod"
        label = "Older EOD data"

    return {
        "status": status,
        "label": label,
        "calendarDaysOld": calendar_days_old,
        "businessDaysOld": business_days_old,
    }


def get_company_market_context(
    symbols: list[str],
    history_days: int = 30,
) -> list[dict[str, Any]]:

    output = []

    for symbol in symbols:

        quote = get_stock_quote(symbol)

        if not quote:
            continue

        freshness = get_freshness(
            quote
        )

        history = get_stock_history(
            symbol,
            history_days,
        )

        last_price = quote.get("last")
        previous_close = quote.get(
            "previousClose"
        )

        change = None
        change_percent = None

        if (
            isinstance(last_price, (int, float))
            and isinstance(
                previous_close,
                (int, float),
            )
            and previous_close != 0
        ):
            change = (
                last_price
                - previous_close
            )

            change_percent = (
                change
                / previous_close
                * 100
            )

        output.append(
            {
                "symbol": quote.get(
                    "symbol",
                    symbol,
                ),
                "quote": {
                    **quote,
                    "change": change,
                    "changePercent": change_percent,
                },
                "freshness": freshness,
                "history": (
                    history.get("data", [])
                    if history
                    else []
                ),
                "dataSource": "TejHQ",
                "dataType": "EOD",
                "exchange": "NSE",
            }
        )

    return output