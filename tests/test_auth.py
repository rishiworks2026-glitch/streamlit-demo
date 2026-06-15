import sys
import os
import pytest
import sqlite3

# ensure project root is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth import build_credentials_from_db
from utils import hash_password_bcrypt
from database import (
    add_user, 
    get_all_users, 
    authenticate_user, 
    init_db, 
    add_product, 
    record_sale,
    get_admin_metrics, 
    get_admin_user_details
)

def test_hash_and_db_auth(tmp_path, monkeypatch):
    test_db = tmp_path / "test_data.db"
    monkeypatch.setattr("database.DB_PATH", str(test_db))
    
    init_db()
    
    email = 'test@example.com'
    business = 'Test Shop'
    pwd = 'secretpass'
    hashed = hash_password_bcrypt(pwd)
    
    uid = add_user(business, email, hashed)
    assert uid is not None
    
    users = get_all_users()
    assert any(u['email'] == email for u in users)
    
    auth = authenticate_user(email, hashed)
    assert auth is not None

def test_multi_user_isolation(tmp_path, monkeypatch):
    test_db = tmp_path / "test_data_multi.db"
    monkeypatch.setattr("database.DB_PATH", str(test_db))
    
    init_db()
    
    # Register User A
    email_a = 'usera@example.com'
    bus_a = 'Business A'
    pwd_a = 'passa123'
    hash_a = hash_password_bcrypt(pwd_a)
    uid_a = add_user(bus_a, email_a, hash_a, role='user')
    
    # Register User B
    email_b = 'userb@example.com'
    bus_b = 'Business B'
    pwd_b = 'passb123'
    hash_b = hash_password_bcrypt(pwd_b)
    uid_b = add_user(bus_b, email_b, hash_b, role='user')
    
    assert uid_a != uid_b
    
    users = get_all_users()
    user_a_rec = next((u for u in users if u['email'] == email_a), None)
    assert user_a_rec is not None
    assert user_a_rec['role'] == 'user'
    
    user_b_rec = next((u for u in users if u['email'] == email_b), None)
    assert user_b_rec is not None
    assert user_b_rec['role'] == 'user'

def test_database_constraints(tmp_path, monkeypatch):
    test_db = tmp_path / "test_data_constraints.db"
    monkeypatch.setattr("database.DB_PATH", str(test_db))
    
    init_db()
    
    uid = add_user("Store Test", "store@example.com", "pass")
    
    # Cost price must not be negative
    with pytest.raises(sqlite3.IntegrityError):
        add_product(uid, "Product A", "Gadgets", 10, -5.0, 10.0, "2026-06-15")
        
    # Quantity must not be negative
    with pytest.raises(sqlite3.IntegrityError):
        add_product(uid, "Product B", "Gadgets", -1, 5.0, 10.0, "2026-06-15")

def test_admin_rbac_metrics(tmp_path, monkeypatch):
    test_db = tmp_path / "test_data_rbac.db"
    monkeypatch.setattr("database.DB_PATH", str(test_db))
    
    init_db()
    
    # Register Users
    uid_1 = add_user("Biz A", "user1@example.com", "pass", role='user')
    uid_2 = add_user("Biz B", "user2@example.com", "pass", role='user')
    uid_admin = add_user("Admin Biz", "admin@example.com", "pass", role='admin')
    
    # Add products
    add_product(uid_1, "Prod A", "Cat A", 10, 5.0, 10.0, "2026-06-15")
    add_product(uid_2, "Prod B", "Cat B", 5, 20.0, 30.0, "2026-06-15")
    
    # Fetch admin metrics
    metrics = get_admin_metrics()
    assert metrics['total_users'] == 2 # Admin is excluded from user metrics
    assert metrics['total_businesses'] == 2
    assert metrics['total_products'] == 15
    assert metrics['total_locked_capital'] == (10 * 5.0) + (5 * 20.0) # 150.0
    
    details = get_admin_user_details()
    assert len(details) == 2 # 2 regular users
    assert any(d['email'] == 'user1@example.com' and d['inventory_value'] == 50.0 for d in details)
    assert any(d['email'] == 'user2@example.com' and d['inventory_value'] == 100.0 for d in details)
