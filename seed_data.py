from database import init_db, add_user, add_product, record_sale, list_products
from utils import hash_password, hash_password_bcrypt
import datetime

def seed():
    init_db()
    # create demo user
    email = 'demo@iqlight.com'
    business = 'Inventory IQ Demo'
    pwd = 'demo123'
    try:
        uid = add_user(business, email, hash_password_bcrypt(pwd))
    except Exception:
        # user may already exist; update their password to bcrypt
        from database import get_all_users, update_user_password
        users = get_all_users()
        uid = next((u['id'] for u in users if u['email'] == email), None)
        if uid:
            update_user_password(email, hash_password_bcrypt(pwd))
    if not uid:
        print('Failed to create or find demo user')
        return

    # add products with varying purchase dates
    today = datetime.date.today()
    products = [
        ("Phone Case A", "Accessories", 50, 50.0, 120.0, today - datetime.timedelta(days=10)),
        ("Wireless Mouse", "Electronics", 40, 150.0, 300.0, today - datetime.timedelta(days=45)),
        ("Charger X", "Electronics", 150, 200.0, 350.0, today - datetime.timedelta(days=75)),
        ("Sticker Pack", "Stationery", 300, 5.0, 20.0, today - datetime.timedelta(days=120)),
        ("Notebook Pro", "Stationery", 20, 40.0, 80.0, today - datetime.timedelta(days=5)),
    ]
    pids = []
    for name, cat, qty, cost, sell, pdate in products:
        pid = add_product(uid, name, cat, qty, cost, sell, pdate.isoformat())
        pids.append(pid)

    # create some sales to differentiate slow-moving
    # sell 10 of Phone Case A 5 days ago
    record_sale(pids[0], 10, (today - datetime.timedelta(days=5)).isoformat())
    # sell 2 of Notebook Pro today
    record_sale(pids[4], 2, today.isoformat())

    print('Seeded demo user:', email)
    print('Products:')
    for p in list_products(uid):
        print('-', p['product_id'], p['product_name'], 'qty=', p['quantity'])

if __name__ == '__main__':
    seed()
