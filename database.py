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
    try:
        cur = conn.cursor()
        # Enable foreign key support
        cur.execute("PRAGMA foreign_keys = ON;")
        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
        ''')
        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT,
            category TEXT,
            quantity INTEGER CHECK(quantity >= 0),
            cost_price REAL CHECK(cost_price >= 0.0),
            selling_price REAL CHECK(selling_price >= 0.0),
            purchase_date TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity_sold INTEGER CHECK(quantity_sold > 0),
            sale_date TEXT,
            FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE CASCADE
        )
        ''')
        
        # Schema migration (if table existed but role column didn't)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        except sqlite3.OperationalError:
            pass # column already exists
            
        # Create database-level performance indexes for foreign key lookups
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_user ON products(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id)")
        
        # Check if an admin exists; if not, seed a default admin account securely
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        if cur.fetchone()[0] == 0:
            default_admin_hash = "$2b$12$Stpib/JBwGTCnhiY28rocONaU71cNXPwvmlpIIWqNNAppKEb6U3Aq"
            cur.execute("INSERT OR IGNORE INTO users (business_name, email, password, role) VALUES (?, ?, ?, ?)",
                        ("Inventory IQ Admin", "admin@iqlight.com", default_admin_hash, "admin"))
        
        conn.commit()
    finally:
        conn.close()

def add_user(business_name: str, email: str, password_hashed: str, role: str = 'user') -> int:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (business_name, email, password, role) VALUES (?, ?, ?, ?)",
                    (business_name, email, password_hashed, role))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_all_users():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def update_user_password(email: str, new_password_hashed: str) -> bool:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET password = ? WHERE email = ?", (new_password_hashed, email))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def delete_user(email: str) -> bool:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def authenticate_user(email: str, password_hashed: str) -> Dict[str, Any] | None:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password_hashed))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def add_product(user_id: int, product_name: str, category: str, quantity: int, cost_price: float, selling_price: float, purchase_date: str):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (user_id, product_name, category, quantity, cost_price, selling_price, purchase_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, product_name, category, quantity, cost_price, selling_price, purchase_date, date.today().isoformat())
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def list_products(user_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE user_id = ?", (user_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def list_products_with_sale_info(user_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT p.product_id, p.user_id, p.product_name, p.category, p.quantity, 
                   p.cost_price, p.selling_price, p.purchase_date, p.created_at,
                   MAX(s.sale_date) as latest_sale_date
            FROM products p
            LEFT JOIN sales s ON p.product_id = s.product_id
            WHERE p.user_id = ?
            GROUP BY p.product_id
        ''', (user_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def update_product_quantity(product_id: int, new_qty: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE products SET quantity = ? WHERE product_id = ?", (new_qty, product_id))
        conn.commit()
    finally:
        conn.close()

def record_sale(product_id: int, quantity_sold: int, sale_date: str):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO sales (product_id, quantity_sold, sale_date) VALUES (?, ?, ?)", (product_id, quantity_sold, sale_date))
        # decrement product quantity
        cur.execute("SELECT quantity FROM products WHERE product_id = ?", (product_id,))
        row = cur.fetchone()
        if row:
            new_qty = max(0, row[0] - quantity_sold)
            cur.execute("UPDATE products SET quantity = ? WHERE product_id = ?", (new_qty, product_id))
        conn.commit()
    finally:
        conn.close()

def latest_sale_date(product_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT sale_date FROM sales WHERE product_id = ? ORDER BY sale_date DESC LIMIT 1", (product_id,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def get_dead_stock(user_id: int, days_threshold: int) -> List[Dict[str, Any]]:
    import datetime
    products = list_products(user_id)
    res = []
    today = datetime.date.today()
    for p in products:
        pid = p['product_id']
        last = latest_sale_date(pid)
        if last:
            try:
                last_date = datetime.date.fromisoformat(last)
                days = (today - last_date).days
            except Exception:
                days = 999
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

def delete_product(product_id: int, user_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        # Enforce security context: make sure the product belongs to the user
        cur.execute("SELECT 1 FROM products WHERE product_id = ? AND user_id = ?", (product_id, user_id))
        if cur.fetchone():
            cur.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
            cur.execute("DELETE FROM sales WHERE product_id = ?", (product_id,))
            conn.commit()
    finally:
        conn.close()

def update_product(product_id: int, user_id: int, product_name: str, category: str, quantity: int, cost_price: float, selling_price: float, purchase_date: str):
    conn = get_conn()
    try:
        cur = conn.cursor()
        # Enforce security context: make sure the product belongs to the user
        cur.execute("SELECT 1 FROM products WHERE product_id = ? AND user_id = ?", (product_id, user_id))
        if cur.fetchone():
            cur.execute(
                "UPDATE products SET product_name = ?, category = ?, quantity = ?, cost_price = ?, selling_price = ?, purchase_date = ? WHERE product_id = ? AND user_id = ?",
                (product_name, category, quantity, cost_price, selling_price, purchase_date, product_id, user_id)
            )
            conn.commit()
    finally:
        conn.close()

def list_sales(user_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
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
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_admin_metrics() -> Dict[str, Any]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'")
        total_users = cur.fetchone()[0] or 0
        
        cur.execute("SELECT COUNT(DISTINCT business_name) FROM users WHERE role != 'admin'")
        total_businesses = cur.fetchone()[0] or 0
        
        cur.execute("SELECT SUM(quantity) FROM products")
        total_products = cur.fetchone()[0] or 0
        
        cur.execute("SELECT SUM(quantity * cost_price) FROM products")
        total_locked_capital = cur.fetchone()[0] or 0.0
        
        cur.execute('''
            SELECT SUM(s.quantity_sold * p.selling_price) 
            FROM sales s 
            JOIN products p ON s.product_id = p.product_id
        ''')
        total_revenue = cur.fetchone()[0] or 0.0
        
        return {
            "total_users": total_users,
            "total_businesses": total_businesses,
            "total_products": total_products,
            "total_locked_capital": total_locked_capital,
            "total_revenue": total_revenue
        }
    finally:
        conn.close()

def get_admin_user_details() -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT u.id, u.business_name, u.email, u.role,
                   (SELECT COUNT(*) FROM products p WHERE p.user_id = u.id) as product_count,
                   (SELECT SUM(p.quantity * p.cost_price) FROM products p WHERE p.user_id = u.id) as inventory_value,
                   (SELECT SUM(s.quantity_sold * p.selling_price) FROM sales s JOIN products p ON s.product_id = p.product_id WHERE p.user_id = u.id) as total_sales
            FROM users u
            WHERE u.role != 'admin'
            ORDER BY u.id ASC
        ''')
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
