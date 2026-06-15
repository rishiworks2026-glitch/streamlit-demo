import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import sqlite3
from typing import Dict, List, Any

# Database functions
from database import (
    init_db, 
    add_user, 
    authenticate_user, 
    add_product, 
    list_products, 
    record_sale, 
    delete_product,
    update_product,
    list_sales,
    latest_sale_date
)
from utils import hash_password_bcrypt, today_date_str
from promotions import recommend_promotion
from auth import get_authenticator

# Page Configuration
st.set_page_config(page_title="Inventory IQ", page_icon="📊", layout="wide")

init_db()

# Custom Styling Injections
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Metrics / KPI styling */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 6px solid #0084ff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        transition: all 0.2s ease-in-out;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1);
        border-left-width: 8px;
    }
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0084ff;
    }
    
    /* Custom alerts */
    .alert-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .alert-yellow {
        border-left: 6px solid #f59e0b;
        background-color: #fffbeb;
    }
    .alert-orange {
        border-left: 6px solid #f97316;
        background-color: #fff7ed;
    }
    .alert-red {
        border-left: 6px solid #ef4444;
        background-color: #fef2f2;
    }
    .alert-title {
        font-weight: 700;
        font-size: 1.1rem;
        color: #1e293b;
        margin-bottom: 4px;
    }
    .alert-meta {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 8px;
    }
    .alert-action {
        font-size: 0.95rem;
        font-weight: 500;
        color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to compute days since last sale
def get_product_days_since_sale(p, today):
    pid = p['product_id']
    last = latest_sale_date(pid)
    if last:
        try:
            last_date = datetime.date.fromisoformat(last)
            return (today - last_date).days
        except Exception:
            pass
    pd = p.get('purchase_date')
    try:
        last_date = datetime.date.fromisoformat(pd) if pd else datetime.date.fromisoformat(p['created_at'])
        return (today - last_date).days
    except Exception:
        return 999

def signup_flow():
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
        <h3 style="margin-top:0; color:#0f172a; font-weight:700;">Create Business Account</h3>
        <p style="color:#64748b; font-size:0.9rem; margin-top:-5px;">Register your store details to begin managing your stock.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("signup_form"):
        business = st.text_input("Business Name")
        email = st.text_input("Email Address")
        pwd = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            if not business or not email or not pwd:
                st.error("Please fill in all fields.")
            else:
                try:
                    hashed = hash_password_bcrypt(pwd)
                    uid = add_user(business, email, hashed)
                    
                    # Fetch created user for session and auto-login
                    user = authenticate_user(email, hashed)
                    if user:
                        st.session_state['user'] = user
                        st.session_state['username'] = email
                        st.session_state['name'] = business
                        st.session_state['authentication_status'] = True
                        st.success("Account created successfully! Redirecting...")
                        st.rerun()
                    else:
                        st.info("Account created. Please login.")
                except sqlite3.IntegrityError:
                    st.error("An account with this email already exists.")
                except Exception as e:
                    st.error(f"Sign up failed: {e}")

def main():
    # Load authenticator
    authenticator = get_authenticator()
    
    # Handle cookie re-authentication
    if st.session_state.get('authentication_status') is True and 'user' not in st.session_state:
        username = st.session_state.get('username')
        email = username if username else None
        if email:
            from database import get_all_users
            for u in get_all_users():
                if u['email'] == email:
                    st.session_state['user'] = u
                    break

    # If user is not authenticated
    if st.session_state.get('authentication_status') is not True:
        st.markdown("""
        <div style="text-align: center; padding: 40px 0 20px 0;">
            <h1 style="color: #0084ff; font-weight: 800; font-size: 3rem; margin-bottom: 0;">Inventory IQ</h1>
            <p style="color: #64748b; font-size: 1.2rem; margin-top: 5px;">Smart Dead Stock Reduction & Analytics for Retailers</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            mode = st.radio("Access Portal", ["Login", "Sign Up"], horizontal=True)
            if mode == "Login":
                try:
                    authenticator.login(location='main')
                except Exception as e:
                    st.error(f"Login widget error: {e}")
                
                # Check status after submission
                if st.session_state.get('authentication_status') is True:
                    # Rerun to load user details
                    st.rerun()
                elif st.session_state.get('authentication_status') is False:
                    st.error("Invalid email or password.")
            else:
                signup_flow()
        return

    # User is logged in
    user = st.session_state['user']
    
    # Sidebar Branding
    st.sidebar.markdown("""
    <div style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 20px;">
        <h2 style="color: #0084ff; font-weight: 800; margin-bottom: 0; font-size: 1.8rem;">Inventory IQ</h2>
        <p style="color: #64748b; font-size: 0.85rem; margin-top: 2px;">Dead Stock Reduction</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch data for calculations
    products = list_products(user['id'])
    today = datetime.date.today()
    for p in products:
        p['days_since_sale'] = get_product_days_since_sale(p, today)
        
    sales = list_sales(user['id'])
    
    # Navigation
    page = st.sidebar.selectbox("Navigation", [
        "📊 Dashboard", 
        "📦 Manage Inventory", 
        "💸 Record Sales", 
        "⚠️ Dead Stock Alerts", 
        "💡 Promotions & Action",
        "📥 Export Reports"
    ])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style="font-size: 0.85rem; color: #475569;">
        Logged in to:<br><b>{user['business_name']}</b><br>
        Email: {user['email']}
    </div>
    """, unsafe_allow_html=True)
    
    # Render logout button
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    authenticator.logout(button_name="Logout", location="sidebar")
    
    # Handle page switching
    if page == "📊 Dashboard":
        render_dashboard(user, products, sales, today)
    elif page == "📦 Manage Inventory":
        render_manage_inventory(user, products)
    elif page == "💸 Record Sales":
        render_record_sales(user, products, sales)
    elif page == "⚠️ Dead Stock Alerts":
        render_dead_stock_alerts(user, products)
    elif page == "💡 Promotions & Action":
        render_promotions(user, products)
    elif page == "📥 Export Reports":
        render_export_reports(user, products, sales)

def render_dashboard(user, products, sales, today):
    st.title(f"Dashboard — {user['business_name']}")
    
    # Calculations
    total_products = len(products)
    inventory_val = sum(p['quantity'] * p['cost_price'] for p in products)
    dead_stock_val = sum(p['quantity'] * p['cost_price'] for p in products if p['days_since_sale'] >= 30)
    
    # Monthly Revenue calculation
    current_month = today.strftime("%Y-%m")
    monthly_rev = sum(s['quantity_sold'] * s['selling_price'] for s in sales if s['sale_date'].startswith(current_month))
    
    immediate_action_count = sum(1 for p in products if p['days_since_sale'] >= 60)
    
    # Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Products</div>
            <div class="kpi-value">{total_products}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Inventory Value</div>
            <div class="kpi-value">₹{inventory_val:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #ef4444;">
            <div class="kpi-label">Dead Stock Value</div>
            <div class="kpi-value" style="color: #ef4444;">₹{dead_stock_val:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #10b981;">
            <div class="kpi-label">Monthly Revenue</div>
            <div class="kpi-value" style="color: #10b981;">₹{monthly_rev:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #f97316;">
            <div class="kpi-label">Needs Action (60d+)</div>
            <div class="kpi-value" style="color: #f97316;">{immediate_action_count}</div>
        </div>
        """, unsafe_allow_html=True)

    # Charts Section
    st.markdown("### Visual Insights")
    c1, c2 = st.columns(2)
    
    with c1:
        # Sales Trend
        if sales:
            sales_df = pd.DataFrame(sales)
            daily_rev = sales_df.groupby('sale_date')['revenue'].sum().reset_index()
            daily_rev = daily_rev.sort_values('sale_date')
            fig_sales = px.line(
                daily_rev, 
                x='sale_date', 
                y='revenue', 
                title="Revenue Trend (₹)",
                labels={'sale_date': 'Date', 'revenue': 'Revenue (₹)'},
                markers=True
            )
            fig_sales.update_traces(line_color='#0084ff', line_width=3)
            st.plotly_chart(fig_sales, use_container_width=True)
        else:
            st.info("No sales data available to show trends.")
            
        # Category Performance (Inventory value per category)
        if products:
            prod_df = pd.DataFrame(products)
            prod_df['val'] = prod_df['quantity'] * prod_df['cost_price']
            cat_val = prod_df.groupby('category')['val'].sum().reset_index()
            fig_cat = px.bar(
                cat_val,
                x='category',
                y='val',
                title="Stock Value by Category (₹)",
                labels={'category': 'Category', 'val': 'Value (₹)'},
                color='category',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_cat, use_container_width=True)

    with c2:
        # Dead Stock Distribution
        if products:
            counts = {"Healthy (<30d)": 0, "Slow Moving (30-59d)": 0, "Discount Recom (60-89d)": 0, "Clearance needed (90d+)": 0}
            for p in products:
                days = p['days_since_sale']
                if days >= 90:
                    counts["Clearance needed (90d+)"] += 1
                elif days >= 60:
                    counts["Discount Recom (60-89d)"] += 1
                elif days >= 30:
                    counts["Slow Moving (30-59d)"] += 1
                else:
                    counts["Healthy (<30d)"] += 1
            pie_df = pd.DataFrame({"Category": list(counts.keys()), "Count": list(counts.values())})
            fig_pie = px.pie(
                pie_df,
                names="Category",
                values="Count",
                color="Category",
                color_discrete_map={
                    "Healthy (<30d)": "#10b981",
                    "Slow Moving (30-59d)": "#f59e0b",
                    "Discount Recom (60-89d)": "#f97316",
                    "Clearance needed (90d+)": "#ef4444"
                },
                title="Dead Stock Distribution"
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No product data to show distribution.")
            
        # Top Selling Products
        if sales:
            sales_df = pd.DataFrame(sales)
            top_sel = sales_df.groupby('product_name')['quantity_sold'].sum().reset_index()
            top_sel = top_sel.sort_values('quantity_sold', ascending=False).head(10)
            fig_top = px.bar(
                top_sel,
                x='quantity_sold',
                y='product_name',
                orientation='h',
                title="Top 10 Selling Products",
                labels={'quantity_sold': 'Units Sold', 'product_name': 'Product'},
                color_discrete_sequence=['#0084ff']
            )
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)
            
    # Inventory Overview Table
    st.markdown("### Inventory Overview")
    if products:
        overview_df = pd.DataFrame(products)
        overview_disp = overview_df[[
            'product_name', 'category', 'quantity', 'cost_price', 'selling_price', 'purchase_date', 'days_since_sale'
        ]].copy()
        overview_disp.columns = [
            'Product Name', 'Category', 'Quantity', 'Cost Price (₹)', 'Selling Price (₹)', 'Purchase Date', 'Days Unsold'
        ]
        st.dataframe(overview_disp, use_container_width=True, hide_index=True)
    else:
        st.info("Your inventory is currently empty.")

def render_manage_inventory(user, products):
    st.title("Manage Inventory")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Product", "✏️ Edit Product", "🗑️ Delete Product"])
    
    with tab1:
        st.subheader("Add New Product")
        with st.form("add_product_form"):
            name = st.text_input("Product Name")
            cat = st.text_input("Category")
            qty = st.number_input("Quantity", min_value=0, value=1, step=1)
            cost = st.number_input("Cost Price (₹)", min_value=0.0, value=0.0, format="%.2f")
            sell = st.number_input("Selling Price (₹)", min_value=0.0, value=0.0, format="%.2f")
            pdate = st.date_input("Purchase Date", value=datetime.date.today())
            submitted = st.form_submit_button("Add Product")
            if submitted:
                if not name or not cat:
                    st.error("Product name and category are required.")
                else:
                    pid = add_product(user['id'], name, cat, int(qty), float(cost), float(sell), pdate.isoformat())
                    st.success(f"Product '{name}' added successfully!")
                    st.rerun()
                    
    with tab2:
        st.subheader("Edit Existing Product")
        if not products:
            st.info("No products available to edit.")
        else:
            prod_map = {f"{p['product_id']} - {p['product_name']}": p for p in products}
            selected_option = st.selectbox("Select Product to Edit", list(prod_map.keys()), key="edit_selector")
            selected_prod = prod_map[selected_option]
            
            with st.form("edit_product_form"):
                new_name = st.text_input("Product Name", value=selected_prod['product_name'])
                new_cat = st.text_input("Category", value=selected_prod['category'])
                new_qty = st.number_input("Quantity", min_value=0, value=int(selected_prod['quantity']), step=1)
                new_cost = st.number_input("Cost Price (₹)", min_value=0.0, value=float(selected_prod['cost_price']), format="%.2f")
                new_sell = st.number_input("Selling Price (₹)", min_value=0.0, value=float(selected_prod['selling_price']), format="%.2f")
                
                try:
                    curr_pdate = datetime.date.fromisoformat(selected_prod['purchase_date'])
                except Exception:
                    curr_pdate = datetime.date.today()
                new_pdate = st.date_input("Purchase Date", value=curr_pdate)
                
                submitted = st.form_submit_button("Update Product")
                if submitted:
                    if not new_name or not new_cat:
                        st.error("Product name and category cannot be empty.")
                    else:
                        update_product(
                            selected_prod['product_id'], 
                            new_name, 
                            new_cat, 
                            int(new_qty), 
                            float(new_cost), 
                            float(new_sell), 
                            new_pdate.isoformat()
                        )
                        st.success(f"Product '{new_name}' updated successfully!")
                        st.rerun()

    with tab3:
        st.subheader("Delete Product")
        if not products:
            st.info("No products available to delete.")
        else:
            prod_map = {f"{p['product_id']} - {p['product_name']}": p['product_id'] for p in products}
            selected_option = st.selectbox("Select Product to Delete", list(prod_map.keys()), key="delete_selector")
            
            st.warning(f"Are you sure you want to delete '{selected_option}'? This will also clear all related sales records.")
            
            if st.button("Confirm Delete", type="primary"):
                pid = prod_map[selected_option]
                delete_product(pid)
                st.success("Product deleted successfully!")
                st.rerun()

def render_record_sales(user, products, sales):
    st.title("Record Sales")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("New Sale Entry")
        if not products:
            st.info("No products in inventory yet. Please add products first.")
        else:
            prod_map = {f"{p['product_name']} (In Stock: {p['quantity']})": p for p in products if p['quantity'] > 0}
            if not prod_map:
                st.warning("All products are currently out of stock.")
            else:
                selected_option = st.selectbox("Choose Product Sold", list(prod_map.keys()))
                selected_prod = prod_map[selected_option]
                
                with st.form("sale_entry_form"):
                    qty_sold = st.number_input("Quantity Sold", min_value=1, max_value=int(selected_prod['quantity']), value=1, step=1)
                    sale_date = st.date_input("Sale Date", value=datetime.date.today())
                    submitted = st.form_submit_button("Record Sale")
                    
                    if submitted:
                        record_sale(selected_prod['product_id'], int(qty_sold), sale_date.isoformat())
                        st.success(f"Recorded sale of {qty_sold} {selected_prod['product_name']}!")
                        st.rerun()
                        
    with col2:
        st.subheader("Sales History")
        if not sales:
            st.info("No sales recorded yet.")
        else:
            sales_df = pd.DataFrame(sales)
            sales_disp = sales_df[['sale_date', 'product_name', 'quantity_sold', 'selling_price', 'revenue', 'profit']].copy()
            sales_disp.columns = ['Sale Date', 'Product Name', 'Qty Sold', 'Selling Price (₹)', 'Total Revenue (₹)', 'Total Profit (₹)']
            st.dataframe(sales_disp, use_container_width=True, hide_index=True)

def render_dead_stock_alerts(user, products):
    st.title("Dead Stock Alerts")
    
    days_threshold = st.slider("Filter products with no sales for at least (days):", min_value=10, max_value=365, value=30)
    
    dead_stock = [p for p in products if p['days_since_sale'] >= days_threshold]
    
    if not dead_stock:
        st.success(f"🎉 No products match the {days_threshold} days dead stock threshold.")
        return

    st.write(f"Showing **{len(dead_stock)}** products needing attention:")
    
    for p in dead_stock:
        days = p['days_since_sale']
        if days >= 90:
            alert_class = "alert-red"
            status_text = "Clearance Sale Needed (90+ days)"
            action_text = "🚨 Critical: Product has not sold for a long period. Recommend immediate clearance sale of 40-50% off or bundle as a free gift with hot sellers."
        elif days >= 60:
            alert_class = "alert-orange"
            status_text = "Discount Recommended (60-89 days)"
            action_text = "🧡 Action Needed: Suggest 20-30% discount or running a promotional campaign to stimulate demand."
        else:
            alert_class = "alert-yellow"
            status_text = "Slow Moving Stock (30-59 days)"
            action_text = "💛 Warning: Slow moving. Recommend displaying at the storefront or offering a Buy 1 Get 1 (BOGO) deal."

        st.markdown(f"""
        <div class="alert-card {alert_class}">
            <div class="alert-title">{p['product_name']} (Qty: {p['quantity']})</div>
            <div class="alert-meta">
                Category: <b>{p['category']}</b> | Purchase Date: <b>{p['purchase_date']}</b> | Days Unsold: <b style='font-size:1.1rem;'>{days} days</b>
            </div>
            <div class="alert-action">
                <b>Recommended Strategy:</b> {action_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_promotions(user, products):
    st.title("Promotion Suggestions & Calculator")
    
    slow_products = [p for p in products if p['days_since_sale'] >= 30]
    
    if not slow_products:
        st.success("All stock is moving healthy! No promotions needed.")
        return
        
    st.subheader("Dead Stock Revenue Loss Calculator")
    st.markdown("""
    The table below highlights slow-moving products, their locked cost capital, and potential revenue loss. 
    Review suggested pricing discounts to release cash flow.
    """)
    
    calc_rows = []
    for p in slow_products:
        days = p['days_since_sale']
        qty = p['quantity']
        cost = p['cost_price']
        sell = p['selling_price']
        locked_cost = qty * cost
        potential_rev = qty * sell
        
        # Intelligent recommendation logic
        rec = recommend_promotion(p)
        rec_msg = rec['message']
        
        if days >= 90:
            sug_disc = "50%"
            sug_price = sell * 0.5
        elif days >= 60:
            sug_disc = "25%"
            sug_price = sell * 0.75
        else:
            sug_disc = "10% / BOGO"
            sug_price = sell * 0.9
            
        calc_rows.append({
            'Product': p['product_name'],
            'Days Unsold': days,
            'Qty': qty,
            'Locked Cost (₹)': locked_cost,
            'Potential Rev (₹)': potential_rev,
            'Suggested Action': rec_msg,
            'Discount': sug_disc,
            'Promo Price (₹)': f"{sug_price:,.2f}"
        })
        
    calc_df = pd.DataFrame(calc_rows)
    
    total_locked = calc_df['Locked Cost (₹)'].sum()
    st.warning(f"⚠️ **Locked Cost Capital:** You have **₹{total_locked:,.2f}** tied up in slow-moving inventory.")
    
    st.dataframe(calc_df, use_container_width=True, hide_index=True)

def render_export_reports(user, products, sales):
    st.title("Export Reports")
    st.markdown("Download clean CSV reports of your inventory, sales, and dead stock to upload to accounting tools or open in Excel.")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("Inventory Report")
        if products:
            df_prod = pd.DataFrame(products)
            df_prod_disp = df_prod[['product_id', 'product_name', 'category', 'quantity', 'cost_price', 'selling_price', 'purchase_date', 'days_since_sale']].copy()
            df_prod_disp.columns = ['ID', 'Name', 'Category', 'Quantity', 'Cost Price (₹)', 'Selling Price (₹)', 'Purchase Date', 'Days Unsold']
            
            st.dataframe(df_prod_disp.head(5), use_container_width=True, hide_index=True)
            
            csv_data = df_prod_disp.to_csv(index=False)
            st.download_button(
                label="📥 Download Inventory CSV",
                data=csv_data,
                file_name=f"inventory_report_{datetime.date.today().isoformat()}.csv",
                mime="text/csv"
            )
        else:
            st.info("No inventory data.")

    with c2:
        st.subheader("Sales History Report")
        if sales:
            df_sales = pd.DataFrame(sales)
            df_sales_disp = df_sales[['sale_id', 'sale_date', 'product_name', 'category', 'quantity_sold', 'selling_price', 'revenue', 'profit']].copy()
            df_sales_disp.columns = ['Sale ID', 'Date', 'Product Name', 'Category', 'Qty Sold', 'Unit Price (₹)', 'Total Revenue (₹)', 'Profit (₹)']
            
            st.dataframe(df_sales_disp.head(5), use_container_width=True, hide_index=True)
            
            csv_data = df_sales_disp.to_csv(index=False)
            st.download_button(
                label="📥 Download Sales CSV",
                data=csv_data,
                file_name=f"sales_report_{datetime.date.today().isoformat()}.csv",
                mime="text/csv"
            )
        else:
            st.info("No sales data.")

    with c3:
        st.subheader("Dead Stock Report")
        dead_stock = [p for p in products if p['days_since_sale'] >= 30]
        if dead_stock:
            df_dead = pd.DataFrame(dead_stock)
            df_dead['potential_revenue_loss'] = df_dead['quantity'] * df_dead['selling_price']
            df_dead_disp = df_dead[['product_name', 'category', 'quantity', 'cost_price', 'selling_price', 'days_since_sale', 'potential_revenue_loss']].copy()
            df_dead_disp.columns = ['Name', 'Category', 'Quantity', 'Cost Price (₹)', 'Selling Price (₹)', 'Days Unsold', 'Potential Revenue Loss (₹)']
            
            st.dataframe(df_dead_disp.head(5), use_container_width=True, hide_index=True)
            
            csv_data = df_dead_disp.to_csv(index=False)
            st.download_button(
                label="📥 Download Dead Stock CSV",
                data=csv_data,
                file_name=f"dead_stock_report_{datetime.date.today().isoformat()}.csv",
                mime="text/csv"
            )
        else:
            st.info("No dead stock detected.")

if __name__ == '__main__':
    main()
