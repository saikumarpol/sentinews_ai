from services.query_router import (
    classify_query,
    build_search_queries,
)


test_queries = [
    "Why did TCS fall recently?",
    "Latest HDFC Bank news",
    "What happened in today's Indian market?",
    "What is PE ratio?",
    "Explain repo rate",
    "Compare TCS and Infosys",
    "Why are IT stocks falling?",
    "What is happening with Reliance?",
]


for query in test_queries:

    result = classify_query(query)

    search_queries = build_search_queries(
        query=query,
        query_type=result["type"],
        companies=result["companies"],
    )

    print("\n====================================")
    print("Question:", query)
    print("Type:", result["type"])
    print("Companies:", result["companies"])
    print("Primary:", result["primary_company"])
    print("Search queries:")

    for search_query in search_queries:
        print(" -", search_query)