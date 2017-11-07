import os
from flask import Flask, g, current_app
from flaskext.sass import sass
import click
from pymongo.errors import DuplicateKeyError
from num2words import num2words
import inflection

from .db import init_db, close_db
from .login import login_manager, register_user, set_password

from .views.insight import insight
from .views.integrations import integrations
from .views.api import api
from .views.home import home
from .views.user import user

from .actions.fetch_data import fetch_data, fetch_new
from .actions.fetch_charity_data import fetch_oscr, fetch_ccew, fetch_ccew_aoo, fetch_ccni, import_oscr, import_ccew, import_ccni
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
    register_template_filter(app)
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


def split_funders(ctx, param, value):
    if value:
        return value.split(",")
    return value


def register_cli(app):

    @app.cli.command('initdb')
    def initdb_command():
        """Creates the database tables."""
        init_db()
        print('Initialized the database.')

    @app.cli.command("find_new")
    @click.option('--registry', default="http://data.threesixtygiving.org/data.json", help="URL to download the data registry from")
    @click.option('--files-since', default=None, help="Look only for files modified since this date (in format YYYY-MM-DD)")
    def find_new_command(registry, files_since):
        """find any new funders"""
        fetch_new(registry, files_since)

    @app.cli.command("fetch_data")
    @click.option('--registry', default="http://data.threesixtygiving.org/data.json", help="URL to download the data registry from")
    @click.option('--files-since', default=None, help="Look only for files modified since this date (in format YYYY-MM-DD)")
    @click.option('--funders', default=None, callback=split_funders, help="Only update from these funders (comma separated list of funder prefixes/names/slugs)")
    @click.option('--skip-funders', default=None, callback=split_funders, help="Skip funders from update (comma separated list of funder prefixes/names/slugs)")
    def fetch_data_command(registry, files_since, funders, skip_funders):
        fetch_data(registry, files_since, funders, skip_funders)

    @app.cli.command("update_organisations")
    @click.option('--files-since', default=None, help="Look only for files modified since this date (in format YYYY-MM-DD)")
    @click.option('--funders', default=None, callback=split_funders, help="Only update from these funders (comma separated list of funder prefixes/names/slugs)")
    @click.option('--skip-funders', default=None, callback=split_funders, help="Skip funders from update (comma separated list of funder prefixes/names/slugs)")
    def update_organisations_command(funders, skip_funders):
        update_organisations(funders, skip_funders)

    @app.cli.command("update_charity")
    @click.option('--funders', default=None, callback=split_funders, help="Only update from these funders (comma separated list of funder prefixes/names/slugs)")
    @click.option('--skip-funders', default=None, callback=split_funders, help="Skip funders from update (comma separated list of funder prefixes/names/slugs)")
    def update_charity_command(funders, skip_funders):
        update_charity(funders, skip_funders)

    @app.cli.command("update_beneficiaries")
    @click.option('--funders', default=None, callback=split_funders, help="Only update from these funders (comma separated list of funder prefixes/names/slugs)")
    @click.option('--skip-funders', default=None, callback=split_funders, help="Skip funders from update (comma separated list of funder prefixes/names/slugs)")
    def update_beneficiaries_command(funders, skip_funders):
        update_beneficiaries(funders, skip_funders)

    @app.cli.command("update_geography")
    @click.option('--funders', default=None, callback=split_funders, help="Only update from these funders (comma separated list of funder prefixes/names/slugs)")
    @click.option('--skip-funders', default=None, callback=split_funders, help="Skip funders from update (comma separated list of funder prefixes/names/slugs)")
    def update_geography_command(funders, skip_funders):
        update_geography(funders, skip_funders)

    @app.cli.command("fetch_all")
    @click.option('--registry', default="http://data.threesixtygiving.org/data.json", help="URL to download the data registry from")
    @click.option('--files-since', default=None, help="Look only for files modified since this date (in format YYYY-MM-DD)")
    @click.option('--funders', default=None, callback=split_funders, help="Only update from these funders (comma separated list of funder prefixes/names/slugs)")
    @click.option('--skip-funders', default=None, callback=split_funders, help="Skip funders from update (comma separated list of funder prefixes/names/slugs)")
    def fetch_all_command(registry, files_since, funders, skip_funders):
        fetch_data(registry, files_since, funders, skip_funders)
        update_organisations(funders, skip_funders)
        update_charity(funders, skip_funders)
        update_beneficiaries(funders, skip_funders)
        update_geography(funders, skip_funders)

    @app.cli.command("update_all")
    @click.option('--funders', default=None, callback=split_funders, help="Only update from these funders (comma separated list of funder prefixes/names/slugs)")
    @click.option('--skip-funders', default=None, callback=split_funders, help="Skip funders from update (comma separated list of funder prefixes/names/slugs)")
    def update_all_command(funders, skip_funders):
        update_organisations(funders, skip_funders)
        update_charity(funders, skip_funders)
        update_beneficiaries(funders, skip_funders)
        update_geography(funders, skip_funders)

    @app.cli.command("fetch_charities")
    @click.option("--ccew", default="http://data.charitycommission.gov.uk/", help="URL of page containing Charity Commission data")
    @click.option("--ccni", default="http://www.charitycommissionni.org.uk/charity-search/?q=&include=Linked&include=Removed&exportCSV=1", help="CSV of Northern Ireland Charity Commission data")
    @click.option("--oscr", default="https://www.oscr.org.uk/charities/search-scottish-charity-register/charity-register-download", help="Page containing Scottish charity data")
    @click.option("--ccew-aoo", default="https://gist.githubusercontent.com/drkane/8973fd75009f502f28aacfdc396b40d2/raw/be43860d1cbddfb9f653c8866ecbbe83273993a8/cc-aoo-gss-iso.csv", help="CSV with mapping from Charity Commission to ISO/GSS codes")
    def fetch_charities_command(ccew, ccni, oscr, ccew_aoo):
        fetch_oscr(oscr)
        fetch_ccew(ccew)
        fetch_ccew_aoo(ccew_aoo)
        fetch_ccni(ccni)

    @app.cli.command("import_charities")    
    def import_charities_command():
        import_ccew()
        import_oscr()
        import_ccni()

    @app.cli.command("register_user")
    @click.argument('email')
    @click.argument('password')
    def register_user_command(email, password):
        try:
            register_user(email, password)
            print("User created.")
        except DuplicateKeyError:
            print("User already present in DB.")

    @app.cli.command("set_password")
    @click.argument('email')
    @click.argument('password')
    def register_user_command(email, password):
        set_password(email, password)
        print("Password set.")

def register_template_filter(app):

    # custom jinja2 filter for getting chart data
    @app.template_filter()
    def chart_data(value, label="count"):
        return [d[label] for d in value]

    # custom jinja2 filter for getting chart labels
    @app.template_filter()
    def chart_label(value):
        return chart_data(value, "label")

    @app.template_filter()
    def format_number(value, plural=None, word_before=10, ordinal=False, num_format=",.0f"):
        if word_before:
            if value <= word_before:
                value = num2words(value, ordinal)
        if isinstance(value, int):
            value = "{:{num_format}}".format(value, num_format=num_format)
        if plural:
            return "{} {}".format(value, inflection.pluralize(plural))
        else:
            return value


def register_teardowns(app):

    # @app.teardown_appcontext
    def close_db_teardown(error):
        close_db()
