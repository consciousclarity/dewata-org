"""integration test ordering.

`phase-1/tests/api/ceremony/test_routes.py` and
`phase-1/tests/db/test_migrations.py` both open connections to the
same disposable database (`DEWATA_TEST_DSN`).  pytest default
collection order puts them in lexicographic file order, which
breaks api-test fixtures because the schema isn't ready yet.

this conftest forces db tests to run first.  it does **not**
run concurrent processes (xdist).
"""

# pytest plugin metadata
__pytest_order__ = True


def pytest_collection_modifyitems(config, items):
    """reorder so that db tests run before api tests."""
    db = [i for i in items if "tests/db/" in str(i.fspath)]
    rest = [i for i in items if "tests/db/" not in str(i.fspath)]
    items[:] = db + rest
