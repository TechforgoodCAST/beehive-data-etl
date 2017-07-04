from flask import current_app, g
from pymongo import MongoClient, ASCENDING, DESCENDING


def connect_db():
    """Connects to the specific database."""
    client = MongoClient(current_app.config["MONGO_HOST"], current_app.config["MONGO_PORT"])
    db = client[current_app.config["MONGO_DB"]]
    current_app.logger.info("Connected to '%s' mongo database [host: %s, port: %s]" % (
        current_app.config["MONGO_DB"],
        current_app.config["MONGO_HOST"],
        current_app.config["MONGO_PORT"]
    ))
    return db


def init_db():
    """Initializes the database."""
    db = get_db()
    # with current_app.open_resource('schema.sql', mode='r') as f:
    #     db.cursor().executescript(f.read())
    # db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db
