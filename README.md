# Inventory IQ — Dead Stock Management & Analytics

A premium Streamlit web application designed for small retailers to identify slow-moving inventory, estimate potential revenue loss, recommend pricing promotions, record sales, and view interactive dashboard analytics.

## Features
- **User Authentication:** Sign up/Login secure system powered by `streamlit-authenticator` and SQLite with bcrypt password hashing.
- **Inventory CRUD:** Full Create, Read, Update, and Delete actions for products.
- **Sales Logging:** Record product sales with automated stock decrements and complete transaction history.
- **Dead Stock Alerts:** Urgency-based color-coded banners:
  - 🟡 **Yellow Alert:** Slow Moving Stock (30-59 days unsold)
  - 🟠 **Orange Alert:** Discount Recommended (60-89 days unsold)
  - 🔴 **Red Alert:** Clearance Needed (90+ days unsold)
- **Promotion Recommendations:** Suggests optimal strategies (BOGO, percentage discounts, volume bundles) based on inventory age and volume.
- **Interactive Dashboard:** Premium light-blue theme featuring metrics (Total Products, Inventory Value, Dead Stock Value, Monthly Revenue) and Plotly Express visual charts (Revenue Trend, Stock Value by Category, Dead Stock Urgency Distribution, Top Selling Products).
- **Report Exports:** Export clean, Excel-compatible CSV reports for Inventory, Sales History, and Dead Stock alerts.

## Setup & Running (macOS/Linux)

1. **Activate virtual environment & install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Initialize and seed the database:**
   ```bash
   python seed_data.py
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## Demo Credentials (Seeded)
- **Username (Email)**: `demo_iqlight.com` (which maps to `demo@iqlight.com`)
- **Password**: `demo123`
