from app.services.dedupe import dedupe_items


def test_dedupe_exact_title():
    items = [
        {"title": "Tariff Increase", "summary": "Tariffs rise on steel imports."},
        {"title": "Tariff Increase", "summary": "Tariffs rise on steel imports in EU."},
    ]
    embeddings = [[1.0, 0.0], [1.0, 0.0]]
    result = dedupe_items(items, embeddings, threshold=0.8)
    assert len(result.items) == 1
    assert result.duplicates_removed == 1
