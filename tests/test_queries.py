from app.services.query import generate_queries


def test_generate_queries_default():
    queries = generate_queries()
    assert len(queries) > 0
    assert any("export" in q or "sanctions" in q for q in queries)


def test_generate_queries_subset():
    queries = generate_queries(["energy inputs"])
    assert len(queries) > 0
    assert all("energy" in q or "gas" in q for q in queries)
