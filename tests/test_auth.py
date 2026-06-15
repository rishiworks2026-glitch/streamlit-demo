import sys
import os
import pytest

# ensure project root is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth import build_credentials_from_db
from utils import hash_password_bcrypt
from database import add_user, get_all_users, authenticate_user, init_db

def test_hash_and_db_auth(tmp_path, monkeypatch):
    # create a temporary database by monkeypatching DB path
    test_db = tmp_path / "test_data.db"
    monkeypatch.setattr("database.DB_PATH", str(test_db))
    
    # Initialize the fresh test database
    init_db()
    
    email = 'test@example.com'
    business = 'Test Shop'
    pwd = 'secretpass'
    hashed = hash_password_bcrypt(pwd)
    
    # Add user to the isolated test database
    uid = add_user(business, email, hashed)
    assert uid is not None
    
    users = get_all_users()
    assert any(u['email'] == email for u in users)
    
    auth = authenticate_user(email, hashed)
    assert auth is not None
