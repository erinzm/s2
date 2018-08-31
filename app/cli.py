import click
from flask import Flask, current_app
from flask.cli import with_appcontext

def register_cli(app: Flask):
    app.cli.add_command(init_db)

@click.command('init-db')
@with_appcontext
def init_db():
    click.echo(click.style('[!] initializing database', fg='green'))
    from .db import db
    with db.connection as conn:
        with conn.cursor() as c:
            with current_app.open_resource('schema.sql', 'r') as f:
                c.execute(f.read())
