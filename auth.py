import streamlit_authenticator as stauth
from database import get_all_users, authenticate_user
from typing import Tuple

COOKIE_NAME = 'inventory_iqlight'
KEY = 'inventory_secret_key'
EXP_DAYS = 30

def build_credentials_from_db():
    users = get_all_users()
    credentials = {"usernames": {}}
    for u in users:
        # use email as username key
        username = u['email'].replace('@', '_')
        credentials['usernames'][username] = {
            'name': u.get('business_name') or u['email'],
            'email': u['email'],
            'password': u['password']
        }
    return credentials

def get_authenticator():
    creds = build_credentials_from_db()
    return stauth.Authenticate(
        credentials=creds,
        cookie_name=COOKIE_NAME,
        cookie_key=KEY,
        cookie_expiry_days=float(EXP_DAYS),
        auto_hash=False
    )

def authenticate_by_db(email: str, password_hashed: str):
    # helper for direct DB auth
    return authenticate_user(email, password_hashed)
