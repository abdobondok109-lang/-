‏import streamlit as st
‏import pandas as pd
‏import sqlite3
‏from datetime import datetime
‏
‏# 1. Page Configuration
‏st.set_page_config(page_title="Inventory Management System", page_icon="📈", layout="wide")
‏
‏# 2. UI Styling (LTR Layout for English)
‏st.markdown("""
‏    <style>
‏        [data-testid="stSidebar"] {display: none;}
‏        [data-testid="stSidebarNav"] {display: none;}
‏        .reportview-container .main .block-container {padding-top: 1rem;}
‏        body {direction: ltr; text-align: left;}
‏    </style>
‏""", unsafe_allow_html=True)
‏
‏# 3. Database Initialization
‏DB_FILE = "local_storage.db"
‏
‏def init_database():
‏    conn = sqlite3.connect(DB_FILE)
‏    c = conn.cursor()
‏    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)")
‏    c.execute("CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT, qty REAL, buy_price REAL, sell_price REAL)")
‏    c.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, product_name TEXT, qty REAL, total REAL, client_name TEXT, payment_type TEXT)")
‏    c.execute("CREATE TABLE IF NOT EXISTS purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, product_name TEXT, qty REAL, total REAL, supplier_name TEXT, amount_paid REAL)")
‏    c.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, category TEXT, amount REAL, notes TEXT)")
‏    c.execute("CREATE TABLE IF NOT EXISTS credit_accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, client_name TEXT, amount REAL, status TEXT)")
‏    
‏    c.execute("SELECT COUNT(*) FROM users")
‏    if c.fetchone()[0] == 0:
‏        c.execute("INSERT INTO users VALUES ('admin', 'admin123', 'Manager')")
‏        c.execute("INSERT INTO users VALUES ('user', 'user123', 'Employee')")
‏    conn.commit()
‏    conn.close()
‏
‏init_database()
‏
‏def query_db(query, params=(), is_select=True):
‏    conn = sqlite3.connect(DB_FILE)
‏    if is_select:
‏        df = pd.read_sql_query(query, conn, params=params)
‏        conn.close()
‏        return df
‏    else:
‏        c = conn.cursor()
‏        c.execute(query, params)
‏        conn.commit()
‏        conn.close()
‏
‏# 4. Login System
‏if 'logged_in' not in st.session_state:
‏    st.session_state.logged_in = False
‏
‏if not st.session_state.logged_in:
‏    st.subheader("Sign In")
‏    u_input = st.text_input("Username")
‏    p_input = st.text_input("Password", type="password")
‏    if st.button("Login"):
‏        res = query_db("SELECT * FROM users WHERE username=? AND password=?", (u_input, p_input))
‏        if not res.empty:
‏            st.session_state.logged_in = True
‏            st.session_state.username = u_input
‏            st.session_state.role = res.iloc[0]['role']
‏            st.rerun()
‏        else:
‏            st.error("Invalid Username or Password")
‏    st.stop()
‏
‏# 5. Header & Navigation
‏st.title("Inventory Management System")
‏st.write(f"Active User: {st.session_state.username} | Role: {st.session_state.role}")
‏
‏menu_cols = st.columns(6)
‏with menu_cols[0]: m_dash = st.button("Dashboard")
‏with menu_cols[1]: m_prod = st.button("Products")
‏with menu_cols[2]: m_sales = st.button("Sales")
‏with menu_cols[3]: m_pur = st.button("Purchases")
‏with menu_cols[4]: m_exp = st.button("Expenses")
‏with menu_cols[5]: 
‏    if st.button("Logout"):
‏        st.session_state.logged_in = False
‏        st.rerun()
‏
‏if 'tab' not in st.session_state: st.session_state.tab = "dash"
‏if m_dash: st.session_state.tab = "dash"
‏if m_prod: st.session_state.tab = "prod"
‏if m_sales: st.session_state.tab = "sales"
‏if m_pur: st.session_state.tab = "pur"
‏if m_exp: st.session_state.tab = "exp"
‏
‏st.write("---")
‏
‏# 6. Tabs Logic
‏if st.session_state.tab == "dash":
‏    st.header("Dashboard Overview")
‏    sales_df = query_db("SELECT * FROM sales")
‏    pur_df = query_db("SELECT * FROM purchases")
‏    exp_df = query_db("SELECT * FROM expenses")
‏    
‏    total_s = sales_df['total'].sum() if not sales_df.empty else 0
‏    total_p = pur_df['total'].sum() if not pur_df.empty else 0
‏    total_e = exp_df['amount'].sum() if not exp_df.empty else 0
‏    net_profit = total_s - total_p - total_e
‏    
‏    c1, c2, c3, c4 = st.columns(4)
‏    c1.metric("Total Sales", f"${total_s}")
‏    c2.metric("Total Purchases", f"${total_p}")
‏    c3.metric("Total Expenses", f"${total_e}")
‏    c4.metric("Net Profit", f"${net_profit}")
‏
‏elif st.session_state.tab == "prod":
‏    st.header("Products & Inventory")
‏    search_p = st.text_input("Search Product by Name")
‏    
‏    with st.expander("Add New Product"):
‏        with st.form("add_product_form"):
‏            code = st.text_input("Product Code")
‏            name = st.text_input("Product Name")
‏            qty = st.number_input("Stock Quantity", min_value=0.0)
‏            b_price = st.number_input("Buying Price", min_value=0.0)
‏            s_price = st.number_input("Selling Price", min_value=0.0)
‏            if st.form_submit_button("Save Product"):
‏                query_db("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?)", (code, name, qty, b_price, s_price), is_select=False)
‏                st.success("Product Saved Successfully!")
‏                st.rerun()
‏                
‏    p_df = query_db("SELECT * FROM products")
‏    if search_p and not p_df.empty:
‏        p_df = p_df[p_df['name'].str.contains(search_p, case=False)]
‏    st.dataframe(p_df, use_container_width=True)
‏
‏elif st.session_state.tab == "sales":
‏    st.header("Sales Management")
‏    p_df = query_db("SELECT * FROM products")
‏    if not p_df.empty:
‏        with st.form("sale_f"):
‏            prod = st.selectbox("Select Product", p_df['name'].tolist())
‏            qty_s = st.number_input("Quantity to Sell", min_value=1.0)
‏            client = st.text_input("Client Name", value="Cash Customer")
‏            p_type = st.selectbox("Payment Type", ["Cash", "Credit"])
‏            
‏            if st.form_submit_button("Complete Sale"):
‏                p_row = p_df[p_df['name'] == prod].iloc[0]
‏                if p_row['qty'] >= qty_s:
‏                    total_cost = qty_s * p_row['sell_price']
‏                    t_now = datetime.now().strftime("%Y-%m-%d")
‏                    p_code = p_row['code']
‏                    
‏                    query_db("UPDATE products SET qty = qty - ? WHERE code = ?", (qty_s, p_code), is_select=False)
‏                    query_db("INSERT INTO sales (date, product_name, qty, total, client_name, payment_type) VALUES (?,?,?,?,?,?)", (t_now, prod, qty_s, total_cost, client, p_type), is_select=False)
‏                    st.success("Sale Recorded Successfully!")
‏                    st.rerun()
‏                else:
‏                    st.error("Error: Not enough stock available.")
‏    all_s = query_db("SELECT * FROM sales")
‏    st.dataframe(all_s, use_container_width=True)
‏
‏elif st.session_state.tab == "pur":
‏    st.header("Purchases Management")
‏    p_df = query_db("SELECT * FROM products")
‏    if not p_df.empty:
‏        with st.form("pur_f"):
‏            prod_p = st.selectbox("Select Product Received", p_df['name'].tolist())
‏            qty_p = st.number_input("Quantity Purchased", min_value=1.0)
‏            supplier = st.text_input("Supplier Name")
‏            paid = st.number_input("Amount Paid", min_value=0.0)
‏            
‏            if st.form_submit_button("Complete Purchase"):
‏                p_row = p_df[p_df['name'] == prod_p].iloc[0]
‏                total_p_cost = qty_p * p_row['buy_price']
‏                t_now = datetime.now().strftime("%Y-%m-%d")
‏                p_code = p_row['code']
‏                
‏                query_db("UPDATE products SET qty = qty + ? WHERE code = ?", (qty_p, p_code), is_select=False)
‏                query_db("INSERT INTO purchases (date, product_name, qty, total, supplier_name, amount_paid) VALUES (?,?,?,?,?,?)", (t_now, prod_p, qty_p, total_p_cost, supplier, paid), is_select=False)
‏                st.success("Stock Level Updated Successfully!")
‏                st.rerun()
‏    all_p = query_db("SELECT * FROM purchases")
‏    st.dataframe(all_p, use_container_width=True)
‏
‏elif st.session_state.tab == "exp":
‏    st.header("Expenses Management")
‏    with st.form("exp_f"):
‏        cat = st.selectbox("Category", ["Maintenance", "Salary", "Rent", "Utilities", "Other"])
‏        amt = st.number_input("Amount Spent", min_value=1.0)
‏        notes = st.text_area("Details / Notes")
‏        if st.form_submit_button("Record Expense"):
‏            t_now = datetime.now().strftime("%Y-%m-%d")
‏            query_db("INSERT INTO expenses (date, category, amount, notes) VALUES (?,?,?,?)", (t_now, cat, amt, notes), is_select=False)
‏            st.success("Expense Recorded Successfully!")
‏            st.rerun()
‏    all_e = query_db("SELECT * FROM expenses")
‏    st.dataframe(all_e, use_container_width=True)
‏
