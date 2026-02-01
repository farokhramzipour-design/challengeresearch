from app.models.schemas import OutputSchema


def test_schema_validation():
    data = {
        "run_id": "2026-02-01T00:00:00Z",
        "scope": {"regions": ["UK", "EU"], "topic": "global trade challenges", "languages": ["en"]},
        "items": [
            {
                "title": "CBAM compliance costs",
                "summary": "EU CBAM rules increase reporting and cost burdens for UK exporters.",
                "challenge_type": "ESG/CBAM",
                "impact_area": ["exports"],
                "severity": "medium",
                "time_horizon": "3-12m",
                "uk_relevance": "direct",
                "eu_relevance": "direct",
                "affected_sectors": ["steel"],
                "evidence": [
                    {
                        "source_name": "ec.europa.eu",
                        "url": "https://ec.europa.eu/example",
                        "published_at": None,
                        "quote": "CBAM reporting required for imports.",
                        "credibility": "high",
                    }
                ],
                "confidence": 0.7,
                "dedupe_key": "abc123",
            }
        ],
        "stats": {"found": 1, "kept": 1, "duplicates_removed": 0},
    }
    parsed = OutputSchema.model_validate(data)
    assert parsed.run_id == "2026-02-01T00:00:00Z"
