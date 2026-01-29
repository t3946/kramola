from flask import Flask, redirect, request, url_for
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user
from wtforms import PasswordField

from models import User, Role


class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))


class SecureModelView(ModelView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))


class UserView(SecureModelView):
    column_exclude_list = ["password_hash"]
    form_excluded_columns = ["password_hash"]
    form_extra_fields = {"password": PasswordField("Password (required on create, leave blank on edit)")}
    column_list = ["id", "username", "email", "is_active", "created_at", "role"]
    column_searchable_list = ["username", "email"]
    form_columns = ["username", "email", "is_active", "role"]

    def on_model_change(self, form, model, is_created: bool) -> None:
        if is_created and (not getattr(form, "password", None) or not form.password.data):
            raise ValueError("Password is required when creating a user.")
        if getattr(form, "password", None) and form.password.data:
            model.set_password(form.password.data)


class RoleView(SecureModelView):
    column_list = ["id", "name", "description"]
    column_searchable_list = ["name"]
    form_columns = ["name", "description"]


def init_admin(app: Flask, db) -> Admin:
    admin = Admin(
        app,
        name="Kramola",
        theme=Bootstrap4Theme(swatch="cerulean"),
        index_view=SecureAdminIndexView(url="/admin", endpoint="admin"),
    )
    admin.add_view(UserView(User, db.session, category="Users", name="Users"))
    admin.add_view(RoleView(Role, db.session, category="Users", name="Roles"))
    return admin
