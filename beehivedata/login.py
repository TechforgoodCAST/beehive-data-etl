from flask import current_app
from flask_login import LoginManager, UserMixin
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash
from random import getrandbits
from datetime import datetime

from .db import get_db

login_manager = LoginManager()


class User(UserMixin):

    def __init__(self, id, data={}):
        self.id = str(id)
        self.email = data["email"]
        self.api_key = data["api_key"]

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

    @staticmethod
    def generate_api_key():
        # https://stackoverflow.com/a/35161595
        return '%0x' % getrandbits(30 * 4)


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    u = db[current_app.config['USERS_COLLECTION']].find_one({"_id": ObjectId(user_id)})
    if u:
        return User(u["_id"], u)

    return None


@login_manager.request_loader
def load_user_from_request(request):
    db = get_db()

    # next, try to login using Basic Auth
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Token token=', '', 1)
        u = db[current_app.config['USERS_COLLECTION']].find_one({"api_key": api_key})
        if u:
            return User(u["_id"], u)

    # finally, return None if both methods did not login the user
    return None


def register_user(email, password, name=None, initials=None, role='moderator'):
    # Connect to the DB
    db = get_db()

    # Ask for data to store
    pass_hash = generate_password_hash(password, method='pbkdf2:sha256')

    # Insert the user in the DB
    db[current_app.config['USERS_COLLECTION']].insert({
        "email": email,
        "password": pass_hash,
        "name": name,
        "initials": initials,
        "api_key": User.generate_api_key(),
        "created_at": datetime.now(),
        "modified": datetime.now(),
        "role": role
    })
