from flask import Flask, flash, redirect, request, Response, url_for
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user
from wtforms import PasswordField

from models import User, Role
from models.phrase_list.list_record import ListRecord
from models.phrase_list.phrase_record import PhraseRecord

from admin.words_list_controller import (
    export_phrases_to_text,
    get_phrases_sorted,
    import_phrases_from_file,
    minusate_phrases_from_file,
    remove_phrase_from_list,
    update_phrase_in_list,
)


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
        words: list[PhraseRecord] = get_phrases_sorted(list_record)
        list_title = list_record.title if list_record else self.list_slug
        import_url = url_for(".import_phrases") if list_record else None
        export_url = url_for(".export_phrases") if list_record else None
        minusate_url = url_for(".minusate_phrases") if list_record else None
        endpoint = self.endpoint
        words_with_actions = [
            (w, url_for(f"{endpoint}.edit_phrase", phrase_id=w.id), url_for(f"{endpoint}.delete_phrase", phrase_id=w.id))
            for w in words
        ]
        return self.render(
            "admin/words_list.html",
            list_title=list_title,
            list_slug=self.list_slug,
            words_with_actions=words_with_actions,
            import_url=import_url,
            export_url=export_url,
            minusate_url=minusate_url,
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
        added = import_phrases_from_file(list_record, file)
        flash(f"Импорт: добавлено фраз в список: {added}.")
        return redirect(url_for(".index"))

    @expose("/minusate", methods=["GET", "POST"])
    def minusate_phrases(self):
        if request.method != "POST":
            return redirect(url_for(".index"))
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return redirect(url_for(".index"))
        file = request.files.get("file")
        if not file or file.filename == "":
            return redirect(url_for(".index"))
        if not file.filename.lower().endswith(".txt"):
            return redirect(url_for(".index"))
        removed = minusate_phrases_from_file(list_record, file)
        flash(f"Минусация: удалено фраз из списка: {removed}.")
        return redirect(url_for(".index"))

    @expose("/phrase/<int:phrase_id>/edit", methods=["GET", "POST"])
    def edit_phrase(self, phrase_id: int):
        if request.method != "POST":
            return redirect(url_for(".index"))
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return redirect(url_for(".index"))
        new_text = request.form.get("phrase", "").strip()
        err = update_phrase_in_list(list_record, phrase_id, new_text)
        if err:
            flash(err)
        else:
            flash("Фраза сохранена.")
        return redirect(url_for(".index"))

    @expose("/phrase/<int:phrase_id>/delete", methods=["GET", "POST"])
    def delete_phrase(self, phrase_id: int):
        if request.method != "POST":
            return redirect(url_for(".index"))
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return redirect(url_for(".index"))
        if remove_phrase_from_list(list_record, phrase_id):
            flash("Фраза удалена из списка.")
        else:
            flash("Фраза не найдена в списке.")
        return redirect(url_for(".index"))

    @expose("/export")
    def export_phrases(self) -> Response:
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return redirect(url_for(".index"))
        content = export_phrases_to_text(list_record)
        filename = f"{list_record.slug}.txt"
        return Response(
            content,
            mimetype="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
