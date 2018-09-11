import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from pathlib import Path
import psycopg2.extras
import csv

def register_cli(app: Flask):
    app.cli.add_command(init_db)
    app.cli.add_command(launch_experiment)

@click.command('init-db')
@with_appcontext
def init_db():
    click.echo('[!] initializing database')
    from .db import db
    with db.connection as conn:
        with conn.cursor() as c:
            with current_app.open_resource('schema.sql', 'r') as f:
                c.execute(f.read())
    click.echo(click.style(f'[✔] successfully initialized database', fg='green'))


@click.command('launch-experiment')
@click.argument('experiment_dir', type=click.Path(exists=True, file_okay=False))
@click.option('--required-votes', default=3)
@with_appcontext
def launch_experiment(experiment_dir, required_votes):
    from .db import db
    from .master import Status, S2

    click.echo('[!] launching experiment...')

    experiment_dir = Path(experiment_dir)
    with db.connection as conn:
        # create a new experiment
        with conn.cursor() as c:
            c.execute('INSERT INTO experiments (required_votes_per_node) VALUES (%s) RETURNING id', (required_votes,))
            exp_id = c.fetchone()[0]

        for x in experiment_dir.iterdir():
            if x.is_dir():
                # push the base image
                with conn.cursor() as c:
                    c.execute('INSERT INTO images (exp_id, uri) VALUES (%s, %s) RETURNING id', (exp_id, str(x / 'image.png')))
                    graph_id = image_id = c.fetchone()[0]
                
                # push bases
                bases = list(x.glob('basis_*.png'))
                with conn.cursor() as c:
                    psycopg2.extras.execute_values(c,
                        'INSERT INTO bases (exp_id, image_id, uri) VALUES %s',
                        [(exp_id, image_id, str(p)) for p in bases])
                
                # push nodes
                with open(x/'nodes.csv') as f:
                    reader = csv.reader(f)
                    records = []
                    for row in reader:
                        id, *weights = row
                        records.append((exp_id, graph_id, int(id), [float(w) for w in weights]))
                    with conn.cursor() as c:
                        psycopg2.extras.execute_values(c, 'INSERT INTO nodes (exp_id, graph_id, id, basis_weights) VALUES %s',
                            records)
                
                # push edges
                with open(x/'edges.csv') as f:
                    reader = csv.reader(f)
                    records = []
                    for row in reader:
                        i, j = map(int, row)
                        records.append((exp_id, graph_id, i, j))
                    with conn.cursor() as c:
                        psycopg2.extras.execute_values(c, 'INSERT INTO edges (exp_id, graph_id, i, j) VALUES %s',
                            records)
        
                # first query & push jobs
                s2 = S2(conn, exp_id, graph_id)
                node_id = s2.get_query(conn)
                jobs = [
                    (exp_id, graph_id, node_id, ballot_id, Status.UNASSIGNED)
                    for ballot_id in range(required_votes)
                ]

                with conn.cursor() as c:
                    psycopg2.extras.execute_values(c, 'INSERT INTO jobs (exp_id, graph_id, node_id, ballot_id, status) VALUES %s',
                        jobs)
    
    click.echo(click.style(f'[✔] successfully launched experiment ({exp_id})', fg='green'))