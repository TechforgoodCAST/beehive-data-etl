from flask import current_app, g
from pymongo import MongoClient, ASCENDING, DESCENDING


def connect_db():
    """Connects to the specific database."""
    if current_app.config["MONGODB_URI"]:
        client = MongoClient(current_app.config["MONGODB_URI"])
        db = client.get_default_database()
    else:
        client = MongoClient(current_app.config["MONGODB_HOST"], current_app.config["MONGODB_PORT"])
        db = client[current_app.config["MONGODB_DB"]]
    current_app.logger.info("Connected to '%s' mongo database [host: %s, port: %s]" % (
        db.name,
        client.address[0],
        client.address[1]
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
