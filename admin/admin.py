from flask import Flask, redirect, request, url_for
from flask_admin import Admin, AdminIndexView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user


class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))


def init_admin(app: Flask) -> Admin:
    admin = Admin(
        app,
        name="Kramola",
        theme=Bootstrap4Theme(swatch="cerulean"),
        index_view=SecureAdminIndexView(url="/admin", endpoint="admin"),
    )
    return admin
