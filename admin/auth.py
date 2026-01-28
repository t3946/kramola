import os
from flask import Blueprint, current_app, redirect, request, url_for
from flask_login import UserMixin, login_user, logout_user

admin_auth_bp = Blueprint("admin_auth", __name__, url_prefix="/admin")


@admin_auth_bp.context_processor
def admin_auth_context() -> dict:
    """Inject Flask-Admin template context so admin/master.html renders correctly."""
    admin_list = current_app.extensions.get("admin", [])
    if not admin_list:
        return {}
    from flask_admin import helpers as admin_helpers

    admin = admin_list[0]
    return {
        "admin_base_template": admin.theme.base_template,
        "admin_view": admin.index_view,
        "theme": admin.theme,
        "h": admin_helpers,
        "get_url": admin_helpers.get_url,
    }


class AdminUser(UserMixin):
    def __init__(self, id: int, username: str) -> None:
        self.id = id
        self.username = username

    def get_id(self) -> str:
        return str(self.id)


def load_user(user_id: str) -> AdminUser | None:
    if user_id != "1":
        return None
    username: str = os.environ.get("ADMIN_USERNAME", "admin")
    return AdminUser(1, username)


@admin_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    from flask import render_template

    if request.method == "GET":
        return render_template("admin/login.html", next=request.args.get("next"))

    username: str = (request.form.get("username") or "").strip()
    password: str = request.form.get("password") or ""
    expected_username: str = os.environ.get("ADMIN_USERNAME", "admin")
    expected_password: str = os.environ.get("ADMIN_PASSWORD", "admin")

    if username != expected_username or password != expected_password:
        return render_template(
            "admin/login.html",
            next=request.form.get("next"),
            error="Invalid username or password",
        )

    login_user(AdminUser(1, username))
    next_url: str | None = request.form.get("next") or request.args.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("admin.index"))


@admin_auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("admin_auth.login"))
