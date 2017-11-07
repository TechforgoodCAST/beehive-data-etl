from flask import current_app, g
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, CollectionInvalid


def connect_db():
    """Connects to the specific database."""
    if current_app.config.get("MONGODB_URI"):
        client = MongoClient(current_app.config["MONGODB_URI"])
        try:
            db = client.get_default_database()
        except ConfigurationError:
            db = client[current_app.config["MONGODB_DB"]]
    else:
        client = MongoClient(current_app.config["MONGODB_HOST"], current_app.config["MONGODB_PORT"])
        db = client[current_app.config["MONGODB_DB"]]
    client.admin.command('ismaster')
    current_app.logger.info("Connected to '%s' mongo database [host: %s, port: %s]" % (
        db.name,
        client.address[0],
        client.address[1]
    ))
    return db


def init_db():
    """Initializes the database."""
    db = get_db()
    current_app.logger.info("Initialising '%s' mongo database [host: %s, port: %s]" % (
        db.name,
        db.client.address[0],
        db.client.address[1]
    ))

    for c in ["grants", "downloads", "files", current_app.config['USERS_COLLECTION'], "charities"]:
        try:
            db.create_collection(c)
        except CollectionInvalid:
            pass

    db.grants.create_index("recipientOrganization.charityNumber")
    db.grants.create_index("recipientOrganization.companyNumber")
    db.grants.create_index("recipientOrganization.id")
    db.charities.create_index("source")
    db[current_app.config['USERS_COLLECTION']].create_index("email", unique=True)


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db


def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.client.close()
        current_app.logger.info("Disconnected from '%s' mongo database [host: %s, port: %s]" % (
            g.db.name,
            g.db.client.address[0],
            g.db.client.address[1]
        ))
