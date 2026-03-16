from flask import Flask
import json

from services.analysis.stats import StatsMatches


class TestStats():
    @staticmethod
    def init_app() -> Flask:
        """Return Flask app. Use: with self.init_app().app_context(): ... for DB access."""
        from app import app
        return app

    @classmethod
    def test_find_extremists_in_pdf(cls) -> None:
        instance = cls()
        app = instance.init_app()

        with app.app_context():
            result = StatsMatches("aa9f59a8-0d9f-4c25-a74b-c7a2256baf6e").get_stats()

            print(result)