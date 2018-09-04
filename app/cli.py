import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from pathlib import Path
import psycopg2.extras

def register_cli(app: Flask):
    app.cli.add_command(init_db)
    app.cli.add_command(launch_experiment)

@click.command('init-db')
@with_appcontext
def init_db():
    click.echo(click.style('[!] initializing database', fg='green'))
    from .db import db
    with db.connection as conn:
        with conn.cursor() as c:
            with current_app.open_resource('schema.sql', 'r') as f:
                c.execute(f.read())

@click.command('launch-experiment')
@click.argument('experiment_dir', type=click.Path(exists=True, file_okay=False))
@with_appcontext
def launch_experiment(experiment_dir):
    from .db import db

    experiment_dir = Path(experiment_dir)
    with db.connection as conn:
        # create a new experiment
        with conn.cursor() as c:
            c.execute('INSERT INTO experiments DEFAULT VALUES RETURNING id')
            exp_id = c.fetchone()[0]

        for x in experiment_dir.iterdir():
            if x.is_dir():
                # push the base image
                with conn.cursor() as c:
                    c.execute('INSERT INTO images (exp_id, uri) VALUES (%s, %s) RETURNING id', (exp_id, str(x / 'image.png')))
                    image_id = c.fetchone()[0]
                
                # push bases
                bases = list(x.glob('basis_*.png'))
                print(bases)
                with conn.cursor() as c:
                    psycopg2.extras.execute_values(c, 'INSERT INTO bases (image_id, uri) VALUES %s', [(image_id, str(p)) for p in bases])