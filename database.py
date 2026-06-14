import sqlite3
from typing import List, Dict, Any
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_name TEXT,
        category TEXT,
        quantity INTEGER,
        cost_price REAL,
        selling_price REAL,
        purchase_date TEXT,
        created_at TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity_sold INTEGER,
        sale_date TEXT
    )
    ''')
    conn.commit()
    conn.close()

def add_user(business_name: str, email: str, password_hashed: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (business_name, email, password) VALUES (?, ?, ?)",
                (business_name, email, password_hashed))
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid

def get_all_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_user_password(email: str, new_password_hashed: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = ? WHERE email = ?", (new_password_hashed, email))
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated

def delete_user(email: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted

def authenticate_user(email: str, password_hashed: str) -> Dict[str, Any] | None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password_hashed))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def add_product(user_id: int, product_name: str, category: str, quantity: int, cost_price: float, selling_price: float, purchase_date: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (user_id, product_name, category, quantity, cost_price, selling_price, purchase_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, product_name, category, quantity, cost_price, selling_price, purchase_date, date.today().isoformat())
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def list_products(user_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_product_quantity(product_id: int, new_qty: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE products SET quantity = ? WHERE product_id = ?", (new_qty, product_id))
    conn.commit()
    conn.close()

def record_sale(product_id: int, quantity_sold: int, sale_date: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO sales (product_id, quantity_sold, sale_date) VALUES (?, ?, ?)", (product_id, quantity_sold, sale_date))
    # decrement product quantity
    cur.execute("SELECT quantity FROM products WHERE product_id = ?", (product_id,))
    row = cur.fetchone()
    if row:
        new_qty = max(0, row[0] - quantity_sold)
        cur.execute("UPDATE products SET quantity = ? WHERE product_id = ?", (new_qty, product_id))
    conn.commit()
    conn.close()

def latest_sale_date(product_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT sale_date FROM sales WHERE product_id = ? ORDER BY sale_date DESC LIMIT 1", (product_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_dead_stock(user_id: int, days_threshold: int) -> List[Dict[str, Any]]:
    import datetime
    products = list_products(user_id)
    res = []
    today = datetime.date.today()
    for p in products:
        pid = p['product_id']
        last = latest_sale_date(pid)
        if last:
            last_date = datetime.date.fromisoformat(last)
            days = (today - last_date).days
        else:
            pd = p.get('purchase_date')
            try:
                last_date = datetime.date.fromisoformat(pd) if pd else datetime.date.fromisoformat(p['created_at'])
                days = (today - last_date).days
            except Exception:
                days = 999
        p['days_since_sale'] = days
        if days >= days_threshold:
            res.append(p)
    return res

def delete_product(product_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
    cur.execute("DELETE FROM sales WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()

def update_product(product_id: int, product_name: str, category: str, quantity: int, cost_price: float, selling_price: float, purchase_date: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE products SET product_name = ?, category = ?, quantity = ?, cost_price = ?, selling_price = ?, purchase_date = ? WHERE product_id = ?",
        (product_name, category, quantity, cost_price, selling_price, purchase_date, product_id)
    )
    conn.commit()
    conn.close()

def list_sales(user_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT s.sale_id, s.product_id, p.product_name, p.category, s.quantity_sold, s.sale_date, p.selling_price, p.cost_price,
               (s.quantity_sold * p.selling_price) as revenue,
               (s.quantity_sold * (p.selling_price - p.cost_price)) as profit
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        WHERE p.user_id = ?
        ORDER BY s.sale_date DESC
    ''', (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

