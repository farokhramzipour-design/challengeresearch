from __future__ import annotations

from typing import Dict, List


CATEGORY_TEMPLATES: Dict[str, List[str]] = {
    "sanctions/export-controls": [
        "UK EU export controls update sanctions trade impact",
        "UK EU dual-use export controls restrictions",
    ],
    "tariffs/trade remedies": [
        "UK EU tariffs antidumping countervailing duties",
        "EU trade remedies measures affecting imports",
    ],
    "customs/border processes": [
        "UK EU customs border checks delays",
        "EU customs procedures changes impact on UK trade",
    ],
    "shipping/logistics/ports": [
        "UK EU ports congestion shipping delays",
        "freight logistics disruptions Europe ports",
    ],
    "insurance/freight rates": [
        "marine insurance costs Europe shipping",
        "freight rate volatility Europe UK",
    ],
    "energy inputs": [
        "energy prices impact on manufacturing Europe UK trade",
        "gas supply risk Europe industrial costs",
    ],
    "FX/payments": [
        "GBP EUR volatility trade payments risk",
        "cross-border payment frictions UK EU trade",
    ],
    "supply-chain disruptions": [
        "supply chain disruptions affecting UK EU imports",
        "critical components shortages Europe manufacturing",
    ],
    "ESG/CBAM-type regulation": [
        "EU CBAM compliance requirements UK exporters",
        "ESG regulation supply chain due diligence EU",
    ],
    "labor/driver shortages": [
        "truck driver shortages Europe UK logistics",
        "labor shortages ports logistics Europe",
    ],
    "geopolitical conflict risks": [
        "geopolitical conflict impact on European trade routes",
        "trade disruption risk from conflict affecting UK EU",
    ],
}


def generate_queries(categories: List[str] | None = None) -> List[str]:
    if categories is None:
        categories = list(CATEGORY_TEMPLATES.keys())

    queries: List[str] = []
    for cat in categories:
        templates = CATEGORY_TEMPLATES.get(cat, [])
        queries.extend(templates)
    return queries
