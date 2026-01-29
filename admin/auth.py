from flask import Blueprint, current_app, redirect, request, url_for
from flask_login import login_user, logout_user

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


def load_user(user_id: str):
    from models import User

    if not user_id or not user_id.isdigit():
        return None
    return User.query.get(int(user_id))


@admin_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    from flask import render_template
    from models import User

    if request.method == "GET":
        return render_template("admin/login.html", next=request.args.get("next"))

    username: str = (request.form.get("username") or "").strip()
    password: str = request.form.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password) or not user.is_active:
        return render_template(
            "admin/login.html",
            next=request.form.get("next"),
            error="Invalid username or password",
        )

    login_user(user)
    next_url: str | None = request.form.get("next") or request.args.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("admin.index"))


@admin_auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("admin_auth.login"))
