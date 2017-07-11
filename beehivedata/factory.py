import os
from flask import Flask, g, current_app
from flaskext.sass import sass
import click
from pymongo.errors import DuplicateKeyError

from .db import init_db, close_db
from .login import login_manager, register_user

from .views.insight import insight
from .views.integrations import integrations
from .views.api import api
from .views.home import home
from .views.user import user

from .actions.fetch_data import fetch_data
from .actions.update_organisations import update_organisations
from .actions.update_charity import update_charity
from .actions.update_beneficiaries import update_beneficiaries
from .actions.update_geography import update_geography


def create_app(config=None):
    app = Flask('beehivedata')

    app.config.update(dict(
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='default',
        MONGODB_PORT=27017,
        MONGODB_HOST='localhost',
        MONGODB_DB='360giving',
        MONGODB_TEST_DB='360giving_test',
        GA_KEY='UA-30021098-3',
        USERS_COLLECTION='users'
    ))
    app.config.update(config or {})

    # @TODO: get environment variables for heroku
    if os.environ.get("MONGODB_URI"):
        app.config.update(dict(
            MONGODB_URI=os.environ.get("MONGODB_URI")
        ))

    register_blueprints(app)
    register_cli(app)
    register_teardowns(app)
    login_manager.init_app(app)

    sass(app, input_dir='assets/scss', output_dir='css')

    return app


def register_blueprints(app):
    app.register_blueprint(insight, url_prefix='/insight')
    app.register_blueprint(integrations, url_prefix='/v1/integrations')
    app.register_blueprint(api, url_prefix='/v1')
    app.register_blueprint(home)
    app.register_blueprint(user)
    return None


def register_cli(app):

    @app.cli.command('initdb')
    def initdb_command():
        """Creates the database tables."""
        init_db()
        print('Initialized the database.')

    @app.cli.command("fetch_data")
    @click.option('--registry', default="http://data.threesixtygiving.org/data.json", help="URL to download the data registry from")
    @click.option('--files-since', default=None, help="Look only for files modified since this date (in format YYYY-MM-DD)")
    @click.option('--funders', default=None, help="Only update from these funders (comma separated list of funder prefixes/names/slugs)")
    def fetch_data_command(registry, files_since, funders):
        if funders:
            funders = funders.split(",")
        fetch_data(registry, files_since, funders)

    @app.cli.command("update_organisations")
    def update_organisations_command():
        update_organisations()

    @app.cli.command("update_charity")
    @click.option('--host', default="localhost", help="Host for the charity-base mongo database")
    @click.option('--port', default=27017, type=int, help="Port for the charity-base mongo database")
    @click.option('--db', default="charity-base", help="charity-base mongo database name")
    def update_charity_command(host, port, db):
        update_charity({"host": host, "port": port, "db": db})

    @app.cli.command("update_beneficiaries")
    def update_beneficiaries_command():
        update_beneficiaries()

    @app.cli.command("update_geography")
    def update_geography_command():
        update_geography()

    @app.cli.command("fetch_all")
    @click.option('--registry', default="http://data.threesixtygiving.org/data.json", help="URL to download the data registry from")
    @click.option('--files-since', default=None, help="Look only for files modified since this date (in format YYYY-MM-DD)")
    @click.option('--funders', default=None, help="Only update from these funders (comma separated list of funder prefixes/names/slugs)")
    @click.option('--host', default="localhost", help="Host for the charity-base mongo database")
    @click.option('--port', default=27017, type=int, help="Port for the charity-base mongo database")
    @click.option('--db', default="charity-base", help="charity-base mongo database name")
    def fetch_all_command(registry, files_since, funders, host, port, db):
        fetch_data_command(registry, files_since, funders)
        update_organisations_command()
        update_charity_command(host, port, db)
        update_beneficiaries_command()
        update_geography_command()

    @app.cli.command("register_user")
    @click.argument('email')
    @click.argument('password')
    def register_user_command(email, password):
        try:
            register_user(email, password)
            print("User created.")
        except DuplicateKeyError:
            print("User already present in DB.")


def register_teardowns(app):

    # @app.teardown_appcontext
    def close_db_teardown(error):
        close_db()
