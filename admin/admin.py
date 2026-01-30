from types import SimpleNamespace
from datetime import datetime, timedelta

from flask import Flask, redirect, request, url_for
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user
from wtforms import PasswordField

from models import User, Role

_TEST_PHRASES = [
    "тест", "пример", "слово", "запись", "элемент", "вариант", "образец", "проверка", "данные", "строка",
]

TEST_WORDS = [
    SimpleNamespace(
        phrase=_TEST_PHRASES[i],
        created_at=(datetime.now() - timedelta(days=10 - i)).strftime("%Y-%m-%d %H:%M"),
    )
    for i in range(10)
]


class WordsListView(BaseView):
    def __init__(self, list_slug: str, list_title: str, **kwargs):
        self.list_slug = list_slug
        self.list_title = list_title
        super().__init__(**kwargs)

    def is_visible(self) -> bool:
        return False

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    @expose("/")
    def index(self):
        return self.render(
            "admin/words_list.html",
            list_title=self.list_title,
            list_slug=self.list_slug,
            words=TEST_WORDS,
        )


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
        index_view=SecureAdminIndexView(url="/admin", endpoint="admin", name="Главная"),
    )
    admin.add_view(UserView(User, db.session, category="Пользователи", name="Пользователи"))
    admin.add_view(RoleView(Role, db.session, category="Пользователи", name="Роли"))
    admin.add_view(
        WordsListView(
            "profanity",
            "Матные слова",
            name="Матные слова",
            url="words-list/profanity",
            endpoint="words_list_profanity",
            category="Готовые списки",
        )
    )
    admin.add_view(
        WordsListView(
            "prohibited-substances",
            "Запрещенные вещества",
            name="Запрещенные вещества",
            url="words-list/prohibited-substances",
            endpoint="words_list_prohibited_substances",
            category="Готовые списки",
        )
    )
    admin.add_view(
        WordsListView(
            "swear-words",
            "Ругательства",
            name="Ругательства",
            url="words-list/swear-words",
            endpoint="words_list_swear_words",
            category="Готовые списки",
        )
    )
    admin.add_view(
        WordsListView(
            "extremists-terrorists",
            "Экстремисты и террористы",
            name="Экстремисты и террористы",
            url="words-list/extremists-terrorists",
            endpoint="words_list_et",
            category="Готовые списки",
        )
    )
    return admin
