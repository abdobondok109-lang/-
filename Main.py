import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Inventory Management", layout="wide")

# 2. UI Styling (LTR Layout for English)
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}
    .reportview-container .main .block-container {max-width: 100%;}
    body {direction: ltr; text-align: left;}
</style>
""", unsafe_allow_html=True)

# 3. Database Initialization
DB_FILE = "local_storage.db"

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        category TEXT,
        last_updated TEXT
    )
    """)
    conn.commit()
    conn.close()

init_database()

# 4. App Title
st.title("📦 Smart Inventory System")
st.write("Manage your stock, prices, and products efficiently.")

# 5. Inventory Management Logic
menu = ["View Inventory", "Add Product", "Update Stock", "Delete Product"]
choice = st.selectbox("Select Action", menu)

if choice == "View Inventory":
    st.subheader("📋 Current Stock")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()
    if df.empty:
        st.info("Your inventory is currently empty.")
    else:
        st.dataframe(df, use_container_width=True)

elif choice == "Add Product":
    st.subheader("➕ Add New Product")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Product Name")
        qty = st.number_input("Quantity", min_value=0, step=1)
        price = st.number_input("Price ($)", min_value=0.0, step=0.25)
        cat = st.text_input("Category (Optional)")
        submit = st.form_submit_input("Save Product")
        
        if submit:
            if name.strip() == "":
                st.error("Product name cannot be empty.")
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO inventory (product_name, quantity, price, category, last_updated) VALUES (?, ?, ?, ?, ?)",
                               (name, qty, price, cat, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success(f"Successfully added: {name}")

elif choice == "Update Stock":
    st.subheader("🔄 Update Existing Stock")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, product_name FROM inventory", conn)
    conn.close()
    
    if df.empty:
        st.info("No products available to update.")
    else:
        product_list = [f"{row['id']} - {row['product_name']}" for _, row in df.iterrows()]
        selected_prod = st.selectbox("Choose Product", product_list)
        prod_id = int(selected_prod.split(" - ")[0])
        
        new_qty = st.number_input("New Quantity", min_value=0, step=1)
        new_price = st.number_input("New Price ($)", min_value=0.0, step=0.25)
        
        if st.button("Update"):
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE inventory SET quantity = ?, price = ?, last_updated = ? WHERE id = ?",
                           (new_qty, new_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), prod_id))
            conn.commit()
            conn.close()
            st.success("Product updated successfully!")

elif choice == "Delete Product":
    st.subheader("🗑️ Delete Product from System")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, product_name FROM inventory", conn)
    conn.close()
    
    if df.empty:
        st.info("No products available to delete.")
    else:
        product_list = [f"{row['id']} - {row['product_name']}" for _, row in df.iterrows()]
        selected_prod = st.selectbox("Choose Product to Delete", product_list)
        prod_id = int(selected_prod.split(" - ")[0])
        
        if st.button("Delete Permanent", type="primary"):
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventory WHERE id = ?", (prod_id,))
            conn.commit()
            conn.close()
            st.success("Product removed from database.")
