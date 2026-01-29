"""CLI: create first admin user (with role \"admin\")."""

import click
from extensions import db
from models import User, Role


@click.command("create-admin")
@click.option("--username", default=None, help="Admin username (prompt if omitted)")
@click.option("--password", default=None, help="Admin password (prompt if omitted)")
@click.option("--email", default=None, help="Admin email (prompt if omitted)")
def create_admin_cmd(
    username: str | None,
    password: str | None,
    email: str | None,
) -> None:
    username = username or click.prompt("Username", type=str)
    password = password or click.prompt("Password", type=str, hide_input=True)
    email = email or click.prompt("Email", type=str)

    role = Role.query.filter_by(name="admin").first()
    if not role:
        role = Role(name="admin", description="Administrator")
        db.session.add(role)
        db.session.commit()

    if User.query.filter_by(username=username).first():
        click.echo("User already exists.")
        return

    user = User(username=username, email=email)
    user.set_password(password)
    user.roles.append(role)
    db.session.add(user)
    db.session.commit()
    click.echo("Admin user created.")
