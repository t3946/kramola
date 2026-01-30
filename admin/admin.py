from flask import Flask, flash, redirect, request, url_for
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user
from wtforms import PasswordField

from extensions import db
from models import User, Role
from models.phrase_list.list_phrase import ListPhrase
from models.phrase_list.list_record import ListRecord
from models.phrase_list.phrase_record import PhraseRecord


def _lines_from_uploaded_file(file) -> list[str]:
    content = file.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    return [line.strip() for line in content.splitlines() if line.strip()]


class WordsListView(BaseView):
    def __init__(self, list_slug: str, **kwargs):
        self.list_slug = list_slug
        super().__init__(**kwargs)

    def is_visible(self) -> bool:
        return False

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    @expose("/")
    def index(self):
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        words: list[PhraseRecord] = []
        if list_record:
            words = (
                PhraseRecord.query.join(ListPhrase)
                .filter(ListPhrase.list_id == list_record.id)
                .order_by(PhraseRecord.created_at.desc())
                .all()
            )
        list_title = list_record.title if list_record else self.list_slug
        import_url = url_for(f".import_phrases") if list_record else None
        return self.render(
            "admin/words_list.html",
            list_title=list_title,
            list_slug=self.list_slug,
            words=words,
            import_url=import_url,
        )

    @expose("/import", methods=["POST"])
    def import_phrases(self):
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return redirect(url_for(".index"))
        file = request.files.get("file")
        if not file or file.filename == "":
            return redirect(url_for(".index"))
        if not file.filename.lower().endswith(".txt"):
            return redirect(url_for(".index"))
        lines: list[str] = _lines_from_uploaded_file(file)
        added = 0
        for phrase_text in lines:
            phrase_record = PhraseRecord.query.filter_by(phrase=phrase_text).first()
            if not phrase_record:
                phrase_record = PhraseRecord(phrase=phrase_text)
                db.session.add(phrase_record)
                db.session.flush()
            link = ListPhrase.query.filter_by(
                phrase_id=phrase_record.id,
                list_id=list_record.id,
            ).first()
            if not link:
                db.session.add(ListPhrase(phrase_id=phrase_record.id, list_id=list_record.id))
                added += 1
        db.session.commit()
        flash(f"Импорт: добавлено фраз в список: {added}.")
        return redirect(url_for(".index"))


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
    with app.app_context():
        list_records = ListRecord.query.order_by(ListRecord.id).all()
    for list_record in list_records:
        endpoint = f"words_list_{list_record.slug.replace('-', '_')}"
        admin.add_view(
            WordsListView(
                list_record.slug,
                name=list_record.title or list_record.slug,
                url=f"words-list/{list_record.slug}",
                endpoint=endpoint,
                category="Готовые списки",
            )
        )
    return admin
