from flask import current_app
from flask_login import LoginManager, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.errors import DuplicateKeyError

from .db import get_db

login_manager = LoginManager()


class User(UserMixin):

    def __init__(self, id):
        self.id = id
        self.email = None

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    return db[current_app.config['USERS_COLLECTION']].find_one({"email": user_id})


def register_user(email, password):
    # Connect to the DB
    db = get_db()

    # Ask for data to store
    pass_hash = generate_password_hash(password, method='pbkdf2:sha256')

    # Insert the user in the DB
    try:
        db[current_app.config['USERS_COLLECTION']].insert({"email": email, "password": pass_hash})
        print("User created.")
    except DuplicateKeyError:
        print("User already present in DB.")
