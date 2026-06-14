import sys
import os
import pytest
# ensure project root is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from auth import build_credentials_from_db
from utils import hash_password_bcrypt
from database import add_user, get_all_users, authenticate_user, init_db

def test_hash_and_db_auth(tmp_path, monkeypatch):
    # create a temporary in-memory DB by monkeypatching DB path
    # since database.py uses file path, just add a user and verify retrieval
    init_db()
    email = 'test@example.com'
    business = 'Test Shop'
    pwd = 'secretpass'
    hashed = hash_password_bcrypt(pwd)
    # ensure no conflicting user exists
    from database import delete_user
    delete_user(email)
    uid = add_user(business, email, hashed)
    assert uid is not None
    users = get_all_users()
    assert any(u['email'] == email for u in users)
    auth = authenticate_user(email, hashed)
    assert auth is not None
