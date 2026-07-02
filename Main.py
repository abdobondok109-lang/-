import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Pro Inventory & ERP", layout="wide")

# Custom CSS for Professional Look
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}
    body {direction: ltr; text-align: left;}
    .stButton>button {width: 100%;}
</style>
""", unsafe_allow_html=True)

DB_FILE = "pro_business_storage.db"

# 2. Advanced Database Setup
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Inventory
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        cost_price REAL NOT NULL,
        sell_price REAL NOT NULL,
        category TEXT
    )""")
    # Suppliers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        phone TEXT,
        debt_to_supplier REAL DEFAULT 0
    )""")
    # Sales & Customers (Ajel)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        product_id INTEGER,
        quantity_sold INTEGER,
        total_price REAL,
        amount_paid REAL,
        amount_due REAL,
        sale_date TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

# 3. App Title & Tabs
st.title("💼 Pro Business Management System")
st.write("Complete ERP solution for Inventory, Sales, Suppliers, and Credits.")

tabs = st.tabs(["📊 Dashboard & Profits", "📦 Inventory", "🛒 Sales & Credits (الآجل)", "👥 Suppliers"])

# ==================== TAB 1: DASHBOARD ====================
with tabs[0]:
    st.subheader("📈 Business Performance Overview")
    conn = sqlite3.connect(DB_FILE)
    inv_df = pd.read_sql_query("SELECT * FROM inventory", conn)
    sales_df = pd.read_sql_query("SELECT * FROM sales", conn)
    supp_df = pd.read_sql_query("SELECT * FROM suppliers", conn)
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculations
    total_sales = sales_df['total_price'].sum() if not sales_df.empty else 0.0
    total_paid = sales_df['amount_paid'].sum() if not sales_df.empty else 0.0
    total_ajel_customers = sales_df['amount_due'].sum() if not sales_df.empty else 0.0
    total_debt_suppliers = supp_df['debt_to_supplier'].sum() if not supp_df.empty else 0.0
    
    col1.metric("Total Sales", f"${total_sales:,.2f}")
    col2.metric("Collected Cash", f"${total_paid:,.2f}")
    col3.metric("Customer Credits (الآجل)", f"${total_ajel_customers:,.2f}", delta="-Owed to you")
    col4.metric("Supplier Debts", f"${total_debt_suppliers:,.2f}", delta="-You Owe")

# ==================== TAB 2: INVENTORY ====================
with tabs[1]:
    st.subheader("📦 Inventory Control")
    action = st.radio("Inventory Action", ["View Stock", "Add Product"], horizontal=True)
    
    if action == "View Stock":
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM inventory", conn)
        conn.close()
        if df.empty: st.info("Inventory is empty.")
        else: st.dataframe(df, use_container_width=True)
        
    elif action == "Add Product":
        with st.form("add_prod_form", clear_on_submit=True):
            p_name = st.text_input("Product Name")
            p_qty = st.number_input("Stock Quantity", min_value=0, step=1)
            p_cost = st.number_input("Cost Price (سعر الشراء)", min_value=0.0, step=0.5)
            p_sell = st.number_input("Selling Price (سعر البيع)", min_value=0.0, step=0.5)
            p_cat = st.text_input("Category")
            submit = st.form_submit_button("Add to Stock")
            
            if submit and p_name.strip() != "":
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO inventory (product_name, quantity, cost_price, sell_price, category) VALUES (?,?,?,?,?)",
                          (p_name, p_qty, p_cost, p_sell, p_cat))
                conn.commit()
                conn.close()
                st.success(f"Added {p_name} successfully!")

# ==================== TAB 3: SALES & AJEL ====================
with tabs[2]:
    st.subheader("🛒 POS & Customer Credit Ledger")
    s_action = st.radio("Sales Action", ["New Sale (Invoice)", "Sales Ledger & Ajel Status"], horizontal=True)
    
    conn = sqlite3.connect(DB_FILE)
    prod_df = pd.read_sql_query("SELECT id, product_name, quantity, sell_price FROM inventory WHERE quantity > 0", conn)
    conn.close()
    
    if s_action == "New Sale (Invoice)":
        if prod_df.empty:
            st.warning("No products available in stock to sell.")
        else:
            with st.form("sale_form", clear_on_submit=True):
                c_name = st.text_input("Customer Name", value="Walk-in Customer")
                p_list = [f"{row['id']} - {row['product_name']} (Available: {row['quantity']}) - ${row['sell_price']}" for _, row in prod_df.iterrows()]
                selected_p = st.selectbox("Select Product", p_list)
                p_id = int(selected_p.split(" - ")[0])
                
                qty_to_sell = st.number_input("Quantity to Sell", min_value=1, step=1)
                
                # Fetch selected product details
                chosen_row = prod_df[prod_df['id'] == p_id].iloc[0]
                calculated_total = chosen_row['sell_price'] * qty_to_sell
                st.write(f"**Total Invoice Amount:** ${calculated_total:,.2f}")
                
                paid_amount = st.number_input("Amount Paid Now", min_value=0.0, step=1.0)
                s_submit = st.form_submit_button("Complete Sale / Save Invoice")
                
                if s_submit:
                    if qty_to_sell > chosen_row['quantity']:
                        st.error("Not enough stock available!")
                    else:
                        due_amount = calculated_total - paid_amount
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        # Deduct stock
                        c.execute("UPDATE inventory SET quantity = quantity - ? WHERE id = ?", (qty_to_sell, p_id))
                        # Record sale
                        c.execute("""INSERT INTO sales (customer_name, product_id, quantity_sold, total_price, amount_paid, amount_due, sale_date)
                                     VALUES (?,?,?,?,?,?,?)""",
                                  (c_name, p_id, qty_to_sell, calculated_total, paid_amount, due_amount, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        conn.close()
                        st.success("Sale processed successfully!")
                        
    elif s_action == "Sales Ledger & Ajel Status":
        conn = sqlite3.connect(DB_FILE)
        sales_report = pd.read_sql_query("SELECT * FROM sales", conn)
        conn.close()
        if sales_report.empty: st.info("No sales recorded yet.")
        else:
            st.dataframe(sales_report, use_container_width=True)
            
            st.markdown("---")
            st.subheader("💵 Collect Due Payments (تسديد الآجل)")
            ajel_customers = sales_report[sales_report['amount_due'] > 0]
            if ajel_customers.empty:
                st.success("Hooray! No pending credits from customers.")
            else:
                c_list = [f"Invoice {row['id']} - {row['customer_name']} (Remaining: ${row['amount_due']})" for _, row in ajel_customers.iterrows()]
                selected_invoice = st.selectbox("Select Invoice to Pay", c_list)
                inv_id = int(selected_invoice.split(" - ")[0].split(" ")[1])
                
                pay_up = st.number_input("Payment Amount Collected", min_value=0.0, step=1.0)
                if st.button("Submit Customer Payment"):
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("UPDATE sales SET amount_paid = amount_paid + ?, amount_due = amount_due - ? WHERE id = ?", (pay_up, pay_up, inv_id))
                    conn.commit()
                    conn.close()
                    st.success("Payment recorded, ledger updated!")

# ==================== TAB 4: SUPPLIERS ====================
with tabs[3]:
    st.subheader("👥 Supplier Management")
    sup_action = st.radio("Supplier Action", ["Supplier Directory", "Add New Supplier"], horizontal=True)
    
    if sup_action == "Supplier Directory":
        conn = sqlite3.connect(DB_FILE)
        df_sup = pd.read_sql_query("SELECT * FROM suppliers", conn)
        conn.close()
        if df_sup.empty: st.info("No suppliers registered.")
        else:
            st.dataframe(df_sup, use_container_width=True)
            
            st.markdown("---")
            st.subheader("💳 Pay Supplier Balances (سداد للموردين)")
            with st.form("pay_sup_form"):
                s_list = [f"{row['id']} - {row['supplier_name']} (We owe: ${row['debt_to_supplier']})" for _, row in df_sup.iterrows() if row['debt_to_supplier'] > 0]
                if not s_list:
                    st.success("All supplier debts are settled!")
                else:
                    sel_sup = st.selectbox("Select Supplier", s_list)
                    s_id = int(sel_sup.split(" - ")[0])
                    sup_pay_amount = st.number_input("Amount Paid to Supplier", min_value=0.0)
                    sup_pay_btn = st.form_submit_button("Record Supplier Payment")
                    if sup_pay_btn:
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("UPDATE suppliers SET debt_to_supplier = debt_to_supplier - ? WHERE id = ?", (sup_pay_amount, s_id))
                        conn.commit()
                        conn.close()
                        st.success("Supplier debt updated!")
                        
    elif sup_action == "Add New Supplier":
        with st.form("add_sup_form", clear_on_submit=True):
            s_name = st.text_input("Supplier Name")
            s_phone = st.text_input("Phone Number")
            s_debt = st.number_input("Initial Balance Owed to Supplier (الحساب القديم إن وجد)", min_value=0.0)
            s_submit = st.form_submit_button("Save Supplier")
            
            if s_submit and s_name.strip() != "":
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO suppliers (supplier_name, phone, debt_to_supplier) VALUES (?,?,?)", (s_name, s_phone, s_debt))
                conn.commit()
                conn.close()
                st.success(f"Supplier {s_name} added successfully!")
