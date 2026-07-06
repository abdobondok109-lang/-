import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# 1. Page Configuration & Professional RTL Styling
st.set_page_config(page_title="تطبيق المخزن - المحاسب المحترف", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}
    body {direction: rtl; text-align: right;}
    div.stButton > button {width: 100%; font-weight: bold; background-color: #0F172A; color: white; border-radius: 8px; padding: 10px;}
    div.stButton > button:hover {background-color: #2563EB; color: white;}
    .stTabs [data-baseweb="tab"] {font-size: 16px; font-weight: bold; color: #1E293B;}
    .card {padding: 15px; border-radius: 8px; background-color: #F8FAFC; border-right: 5px solid #3B82F6; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);}
    .card-success {border-right-color: #10B981;}
    .card-danger {border-right-color: #EF4444;}
</style>
""", unsafe_allow_html=True)

DB_FILE = "el_makhzan_pro.db"

# 2. Database Initialization
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Inventory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT UNIQUE NOT NULL,
        total_received INTEGER DEFAULT 0,
        current_stock INTEGER DEFAULT 0,
        cost_price REAL NOT NULL,
        sell_price REAL DEFAULT 0,
        last_updated TEXT
    )""")
    
    # 2. Suppliers accounts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT UNIQUE NOT NULL,
        total_purchases REAL DEFAULT 0,
        total_paid REAL DEFAULT 0,
        total_due REAL DEFAULT 0
    )""")
    
    # 3. Purchase invoices / payments history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_ledgers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        product_name TEXT,
        quantity INTEGER DEFAULT 0,
        cost_price REAL DEFAULT 0,
        amount_paid REAL DEFAULT 0,
        amount_due REAL DEFAULT 0,
        transaction_type TEXT NOT NULL, -- 'فاتورة مشتريات' أو 'سداد دفعة'
        tx_date TEXT
    )""")
    
    # 4. Cash box / Revenues
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cash_box (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        statement TEXT,
        record_date TEXT
    )""")
    
    # 5. Categorized Expenses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        notes TEXT,
        expense_date TEXT
    )""")
    
    # 6. Saved Audit Sessions (History)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_date TEXT,
        cost_of_goods_sold REAL,
        cash_in_box REAL,
        total_expenses REAL,
        suppliers_paid REAL,
        suppliers_due REAL,
        net_profit REAL,
        details TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

# Application Title
st.title("📦 تطبيق المخزن الرقمي المتكامل")
st.write("النسخة الاحترافية المدمجة لإدارة المخازن، كشوف الموردين، وجلسات جرد الأرباح الفعلية.")

# App Tabs (Free Navigation - No Passwords)
tabs = st.tabs([
    "🛒 الفواتير والموردين", 
    "💸 الخزينة والمصروفات", 
    "🔍 دليل ومخزون المواد", 
    "🧮 جلسة الجرد والربح الحقيقي", 
    "📊 التقارير والأرشيف التاريخي"
])

# ==================== TAB 1: PURCHASES & SUPPLIERS ====================
with tabs[0]:
    st.subheader("🏬 نظام حسابات الموردين والفواتير")
    
    col_sup1, col_sup2 = st.columns(2)
    
    with col_sup1:
        st.markdown('<div class="card">📌 تسجيل فاتورة مشتريات واردة</div>', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_FILE)
        existing_prods = pd.read_sql_query("SELECT product_name FROM inventory", conn)['product_name'].tolist()
        conn.close()
        
        with st.form("invoice_form", clear_on_submit=True):
            sup_name = st.text_input("اسم المورد / الشركة").strip()
            
            p_type = st.radio("صنف المنتج", ["منتج مسجل سابقاً", "منتج جديد"], horizontal=True)
            if p_type == "منتج مسجل سابقاً" and existing_prods:
                p_name = st.selectbox("اختر الصنف", existing_prods)
            else:
                p_name = st.text_input("اسم الصنف الجديد")
                
            qty = st.number_input("الكمية الواردة", min_value=1, step=1)
            cost = st.number_input("سعر الشراء للوحدة (ج.م)", min_value=0.0, step=1.0)
            sell_p = st.number_input("سعر البيع المقترح للوحدة (ج.م)", min_value=0.0, step=1.0)
            paid = st.number_input("المبلغ المدفوع كاش من الفاتورة (ج.م)", min_value=0.0, step=10.0)
            tx_date = st.date_input("تاريخ الفاتورة").strftime("%Y-%m-%d")
            
            submit_inv = st.form_submit_button("إصدار الفاتورة وتحديث الحسابات")
            
            if submit_inv and sup_name and p_name:
                total_cost = qty * cost
                due = total_cost - paid
                
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                
                # Update Supplier Summary Table
                c.execute("INSERT OR IGNORE INTO suppliers (supplier_name) VALUES (?)", (sup_name,))
                c.execute("""UPDATE suppliers SET total_purchases = total_purchases + ?, total_paid = total_paid + ?, total_due = total_due + ? 
                             WHERE supplier_name = ?""", (total_cost, paid, due, sup_name))
                
                # Log to history ledger
                c.execute("""INSERT INTO purchase_ledgers (supplier_name, product_name, quantity, cost_price, amount_paid, amount_due, transaction_type, tx_date)
                             VALUES (?, ?, ?, ?, ?, ?, 'فاتورة مشتريات', ?)""", (sup_name, p_name, qty, cost, paid, due, tx_date))
                
                # Update Inventory stock
                c.execute("INSERT OR IGNORE INTO inventory (product_name, cost_price, sell_price) VALUES (?, ?, ?)", (p_name, cost, sell_p))
                c.execute("""UPDATE inventory SET total_received = total_received + ?, current_stock = current_stock + ?, cost_price = ?, sell_price = ?, last_updated = ?
                             WHERE product_name = ?""", (qty, qty, cost, sell_p, tx_date, p_name))
                
                conn.commit()
                conn.close()
                st.success(f"✔️ تم حفظ الفاتورة بنجاح وتحديث حساب المورد {sup_name}")
                
    with col_sup2:
        st.markdown('<div class="card">💳 سند صرف / سداد دفعة نقدية لمورد</div>', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_FILE)
        sups_list = pd.read_sql_query("SELECT supplier_name FROM suppliers", conn)['supplier_name'].tolist()
        conn.close()
        
        with st.form("payment_form", clear_on_submit=True):
            chosen_sup = st.selectbox("اختر المورد المستلم", sups_list if sups_list else ["لا يوجد موردين حالياً"])
            pay_amount = st.number_input("المبلغ المدفوع (ج.م)", min_value=0.0, step=50.0)
            pay_date = st.date_input("تاريخ السداد").strftime("%Y-%m-%d")
            submit_pay = st.form_submit_button("تسجيل السند المالي")
            
            if submit_pay and chosen_sup in sups_list and pay_amount > 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("""UPDATE suppliers SET total_paid = total_paid + ?, total_due = total_due - ? 
                             WHERE supplier_name = ?""", (pay_amount, pay_amount, chosen_sup))
                c.execute("""INSERT INTO purchase_ledgers (supplier_name, amount_paid, amount_due, transaction_type, tx_date)
                             VALUES (?, ?, ?, 'سداد دفعة', ?)""", (chosen_sup, pay_amount, -pay_amount, pay_date))
                conn.commit()
                conn.close()
                st.success(f"💵 تم إثبات السند النقدي بقيمة {pay_amount} ج.م للمورد {chosen_sup}")

    # Display Supplier Account Ledgers Table
    st.markdown("---")
    st.subheader("📑 كشف حساب أرصدة الموردين الإجمالي")
    conn = sqlite3.connect(DB_FILE)
    sups_df = pd.read_sql_query("SELECT supplier_name AS 'اسم المورد', total_purchases AS 'إجمالي المشتريات', total_paid AS 'إجمالي المدفوع نقداً', total_due AS 'الآجل المتبقي (عليك)' FROM suppliers", conn)
    conn.close()
    st.dataframe(sups_df, use_container_width=True)

# ==================== TAB 2: CASH & EXPENSES ====================
with tabs[1]:
    st.subheader("💸 إدارة الصندوق اليومي والمصاريف المبوبّة")
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown('<div class="card-success" style="padding:15px; background:#F0FDF4; border-right:5px solid #10B981; border-radius:8px;">💰 حركة إيداع كاش بالخزينة (مبيعات/رأس مال)</div>', unsafe_allow_html=True)
        with st.form("cash_form", clear_on_submit=True):
            cash_amt = st.number_input("قيمة المبلغ الوارد (ج.م)", min_value=0.0, step=50.0)
            cash_stmt = st.text_input("البيان / الشرح (مثال: مبيعات يومية، إيداع شخصي)")
            cash_date = st.date_input("تاريخ الإيداع").strftime("%Y-%m-%d")
            submit_cash = st.form_submit_button("تأكيد الإيداع في الخزنة")
            
            if submit_cash and cash_amt > 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO cash_box (amount, statement, record_date) VALUES (?, ?, ?)", (cash_amt, cash_stmt, cash_date))
                conn.commit()
                conn.close()
                st.success("تم إدخال الكاش وتحديث وعاء الخزينة الرئيسي.")
                
    with col_c2:
        st.markdown('<div class="card-danger" style="padding:15px; background:#FEF2F2; border-right:5px solid #EF4444; border-radius:8px;">🔴 النفقات والمصروفات التشغيلية المبوبة</div>', unsafe_allow_html=True)
        with st.form("exp_form", clear_on_submit=True):
            exp_cat = st.selectbox("تبويب المصروف", ["أجور ومرتبات", "إيجار المحل", "فواتير كهرباء ومياه", "نقل وشحن بضائع", "مصاريف نثريّة وضيافة"])
            exp_amt = st.number_input("المبلغ المنصرف (ج.م)", min_value=0.0, step=10.0)
            exp_notes = st.text_area("ملاحظات إضافية عن الصرف")
            exp_date = st.date_input("تاريخ المصروف").strftime("%Y-%m-%d")
            submit_exp = st.form_submit_button("إثبات وخصم المصروف")
            
            if submit_exp and exp_amt > 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO expenses (category, amount, notes, expense_date) VALUES (?, ?, ?, ?)", (exp_cat, exp_amt, exp_notes, exp_date))
                conn.commit()
                conn.close()
                st.success(f"تم إثبات مصروف '{exp_cat}' بنجاح.")

# ==================== TAB 3: INVENTORY MASTER DATA ====================
with tabs[2]:
    st.subheader("🔍 سجل ودليل المخازن الشامل")
    
    conn = sqlite3.connect(DB_FILE)
    inv_df = pd.read_sql_query("SELECT id AS 'كود الصنف', product_name AS 'اسم المنتج', total_received AS 'إجمالي الوارد التراكمي', current_stock AS 'الرصيد الفعلي الحالي', cost_price AS 'سعر الشراء (ج.م)', sell_price AS 'سعر البيع (ج.م)', last_updated AS 'آخر تحديث' FROM inventory", conn)
    conn.close()
    
    search_item = st.text_input("⚡ اكتب اسم المنتج للبحث السريع والتصفية...")
    if search_item:
        inv_df = inv_df[inv_df['اسم المنتج'].str.contains(search_item, case=False)]
        
    st.dataframe(inv_df, use_container_width=True)
    
    st.info("💡 لتعديل أي سعر أو تعديل كمية بالخطأ، يمكنك مراجعة الجداول وتصحيحها من قاعدة البيانات.")

# ==================== TAB 4: AUDIT SESSION (نظام الجرد المتفق عليه) ====================
with tabs[3]:
    st.subheader("🧮 جلسة جرد المستودع واستنتاج صافي الفائض الفعلي")
    st.write("تقوم فكرة هذه الشاشة على حساب الكميات المباعة من واقع النقص في الرفوف مضروباً في سعر الشراء، ومطابقته بالخزينة.")
    
    conn = sqlite3.connect(DB_FILE)
    audit_base = pd.read_sql_query("SELECT id, product_name, total_received, cost_price FROM inventory", conn)
    
    # Financial metrics aggregation
    total_sups_metrics = pd.read_sql_query("SELECT SUM(total_paid), SUM(total_due) FROM suppliers", conn)
    total_paid_sups = total_sups_metrics.iloc[0,0] or 0.0
    total_due_sups = total_sups_metrics.iloc[0,1] or 0.0
    
    total_cash_box = pd.read_sql_query("SELECT SUM(amount) FROM cash_box", conn).iloc[0,0] or 0.0
    total_expenses_all = pd.read_sql_query("SELECT SUM(amount) FROM expenses", conn).iloc[0,0] or 0.0
    conn.close()
    
    st.markdown("### 📝 جدول إدخال الجرد الفعلي الفردي للأصناف:")
    
    if "audit_state_df" not in st.session_state or len(st.session_state.audit_state_df) != len(audit_base):
        audit_base['الكمية الموجودة بالمحل فعلياً (العد اليدوي)'] = audit_base['total_received']
        st.session_state.audit_state_df = audit_base.copy()
        
    editable_audit = st.data_editor(
        st.session_state.audit_state_df[['id', 'product_name', 'total_received', 'cost_price', 'الكمية الموجودة بالمحل فعلياً (العد اليدوي)']],
        use_container_width=True,
        disabled=['id', 'product_name', 'total_received', 'cost_price']
    )
    
    st.markdown("---")
    actual_cash_box_input = st.number_input("💵 تأكيد مقدار الكاش والسيولة النقدية المتوفرة في الخزنة حالياً (ج.م):", value=float(total_cash_box))
    
    if st.button("📊 تشغيل ومعالجة جلسة الجرد الحالية"):
        total_cost_sold_goods = 0.0
        audit_details = []
        
        for idx, row in editable_audit.iterrows():
            total_in = row['total_received']
            actual_now = row['الكمية الموجودة بالمحل فعلياً (العد اليدوي)']
            sold_units = total_in - actual_now  # الكميات المستنتج بيعها
            
            c_price = row['cost_price']
            calc_cost = sold_units * c_price  # الكمية المباعة × سعر الشراء
            total_cost_sold_goods += calc_cost
            
            audit_details.append(f"📦 {row['product_name']} -> المباع المستنتج: {sold_units} قطعة | تكلفة الشراء المخرجة: {calc_cost:,.2f} ج.م")
            
        # The Custom Formula Agreed Upon:
        # المكسب الفعلي الصافي الفائض = الكاش الفعلي - (أموال الموردين المدفوعة + حساب الأوجل الخارجية للموردين + النفقات والمصاريف)
        net_actual_profit = actual_cash_box_input - (total_paid_sups + total_due_sups + total_expenses_all)
        
        st.markdown("### 📋 التقرير المالي المولد للجلسة:")
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.write(f"🔹 **تكلفة البضاعة المباعة الحقيقية (الكميات × سعر الشراء):** {total_cost_sold_goods:,.2f} ج.م")
            st.write(f"🔹 **إجمالي النقدية (الكاش) المتواجد بالخزينة:** {actual_cash_box_input:,.2f} ج.م")
            st.write(f"🔹 **إجمالي النفقات والمصاريف المخصومة:** {total_expenses_all:,.2f} ج.م")
            
        with col_m2:
            st.write(f"🔹 **إجمالي ما تم سداده للموردين نقداً:** {total_paid_sups:,.2f} ج.م")
            st.write(f"🔹 **إجمالي حسابات الآجل المتبقية للموردين:** {total_due_sups:,.2f} ج.م")
            
        st.markdown("---")
        if net_actual_profit >= 0:
            st.success(f"💰 **صافي الفائض والمكسب الفعلي الصافي للمحل:** {net_actual_profit:,.2f} ج.م")
        else:
            st.error(f"🚨 **عجز مالي أو خسارة فعلية مترتبة بالخزينة:** {net_actual_profit:,.2f} ج.م")
            
        # Save session temporarily in state to allow archiving
        st.session_state.current_session_data = {
            "cost": total_cost_sold_goods,
            "cash": actual_cash_box_input,
            "expenses": total_expenses_all,
            "paid_sups": total_paid_sups,
            "due_sups": total_due_sups,
            "net": net_actual_profit,
            "details": "\n".join(audit_details),
            "editor_data": editable_audit
        }
        
    if "current_session_data" in st.session_state:
        st.markdown("---")
        if st.button("💾 ترحيل واعتماد جلسة الجرد وتصفير الدورة للمرحلة القادمة"):
            sd = st.session_state.current_session_data
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            
            # Save into historical database
            c.execute("""INSERT INTO audit_history (audit_date, cost_of_goods_sold, cash_in_box, total_expenses, suppliers_paid, suppliers_due, net_profit, details)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                      (datetime.now().strftime("%Y-%m-%d %H:%M"), sd['cost'], sd['cash'], sd['expenses'], sd['paid_sups'], sd['due_sups'], sd['net'], sd['details']))
            
            # Apply and update new inventory starting state
            for _, r in sd['editor_data'].iterrows():
                c.execute("UPDATE inventory SET total_received = ?, current_stock = ? WHERE id = ?", (r['الكمية الموجودة بالمحل فعلياً (العد اليدوي)'], r['الكمية الموجودة بالمحل فعلياً (العد اليدوي)'], r['id']))
                
            conn.commit()
            conn.close()
            del st.session_state.current_session_data
            st.success("🎯 تم ترحيل الجلسة للأرشيف بنجاح، وتثبيت أرقام المخزن الجديدة كبداية للفترة القادمة!")
            st.rerun()

# ==================== TAB 5: ARCHIVES & REPORTS ====================
with tabs[4]:
    st.subheader("📊 الأرشيف التاريخي والسجلات المحفوظة")
    
    conn = sqlite3.connect(DB_FILE)
    history_df = pd.read_sql_query("SELECT id AS 'رقم الجلسة', audit_date AS 'تاريخ ووقت الجرد', cost_of_goods_sold AS 'تكلفة المباع', cash_in_box AS 'كاش الخزينة', total_expenses AS 'المصاريف', suppliers_paid AS 'المدفوع للموردين', suppliers_due AS 'آجل الموردين', net_profit AS 'المكسب الصافي الفعلي' FROM audit_history ORDER BY id DESC", conn)
    conn.close()
    
    if history_df.empty:
        st.info("لا توجد جلسات جرد مؤرشفة ومثبتة حتى الآن.")
    else:
        st.dataframe(history_df, use_container_width=True)
        
        # WhatsApp Report Exporting
        st.markdown("### 📲 مشاركة التقرير الأخير عبر واتساب")
        last_row = history_df.iloc[0]
        report_msg = f"📊 *تقرير جرد تطبيق المخزن*\n📅 التاريخ: {last_row['تاريخ ووقت الجرد']}\n💵 كاش الخزينة الفعلي: {last_row['كاش الخزينة']} ج.م\n📉 إجمالي المصاريف: {last_row['المصاريف']} ج.م\n🏬 آجل الموردين: {last_row['آجل الموردين']} ج.م\n💰 *صافي المكسب الفعلي الفائض: {last_row['المكسب الصافي الفعلي']} ج.م*"
        encoded_msg = urllib.parse.quote(report_msg)
        st.markdown(f'<a href="https://api.whatsapp.com/send?text={encoded_msg}" target="_blank"><button style="background-color:#25D366;color:white;padding:12px;border:none;border-radius:6px;cursor:pointer;width:100%;">📲 إرسال التقرير الختامي للواتساب</button></a>', unsafe_allow_html=True)
