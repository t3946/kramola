"""Run real parser under Flask app_context for debugging via pytest.

No mocks: ParserFedsFM().load() is called for real (needs Selenium/Chrome).
Use this test in debug to step through the parser.

Run: pytest tests/test_sync_extremists_cmd.py -v
  (in env where app + Selenium are available, e.g. docker compose exec application ...)
"""

import pytest

from flask import Flask


# Expected shape of parser.load() result (test data structure)
PARSER_RESULT_KEYS = ("international", "russian", "international_excluded", "russian_excluded")
BLOCK_KEYS = ("namesFL", "namesUL")


@pytest.fixture
def app() -> Flask:
    """Flask app (same as in production)."""
    from app import app as flask_app
    return flask_app


def test_parser_runs_with_flask_app_context(app: Flask) -> None:
    """Run real parser under app_context; result has expected keys and list fields."""
    with app.app_context():
        from services.parser.parser_feds_fm import ParserFedsFM

        parser = ParserFedsFM()
        data = parser.load()

        assert isinstance(data, dict)
        for key in PARSER_RESULT_KEYS:
            assert key in data, f"Missing key: {key}"
            block = data[key]
            assert isinstance(block, dict), f"{key} is not dict"
            for bkey in BLOCK_KEYS:
                assert bkey in block, f"Missing block key: {bkey}"
                assert isinstance(block[bkey], list), f"{key}.{bkey} is not list"

        # Optional: keep parsed data for inspection when debugging
        _parsed_data = data  # noqa: F841
