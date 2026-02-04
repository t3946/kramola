"""MySQL / SQLAlchemy app config and init."""

import os
from urllib.parse import quote_plus
from flask import Flask
from flask_migrate import Migrate
from extensions import db


def init_mysql(app: Flask) -> None:
    mysql_user = os.environ.get("MYSQL_USER")
    mysql_password = quote_plus(os.environ.get("MYSQL_PASSWORD"))
    mysql_host = os.environ.get("MYSQL_HOST", "127.0.0.1")
    mysql_port = os.environ.get("MYSQL_PORT", "3306")
    mysql_database = os.environ.get("MYSQL_DATABASE", "kramola")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    Migrate(app, db)
