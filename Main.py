import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# 1. Page Configuration
st.set_page_config(page_title="نظام إدارة المستودع والجرد الذكي", layout="wide")

# Custom CSS for Professional RTL & UI Look
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}
    body {direction: rtl; text-align: right;}
    div.stButton > button {width: 100%; font-weight: bold; background-color: #1E3A8A; color: white; border-radius: 8px;}
    div.stButton > button:hover {background-color: #3B82F6; color: white;}
    .stTabs [data-baseweb="tab"] {font-size: 16px; font-weight: bold;}
    .report-box {padding: 15px; border-radius: 8px; background-color: #F3F4F6; border-right: 5px solid #10B981; margin-bottom: 10px;}
    .warning-box {padding: 15px; border-radius: 8px; background-color: #FEF3C7; border-right: 5px solid #D97706; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

DB_FILE = "advanced_erp_storage.db"
OWNER_PIN = "1234" # يمكنك تغيير الرقم السري الخاص بك من هنا

# 2. Database Setup
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Inventory
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        total_received INTEGER DEFAULT 0,
        current_stock INTEGER DEFAULT 0,
        cost_price REAL NOT NULL,
        sell_price REAL DEFAULT 0,
        category TEXT,
        last_updated TEXT
    )""")
    # Purchase Invoices
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        cost_price REAL NOT NULL,
        total_cost REAL NOT NULL,
        amount_paid REAL DEFAULT 0,
        amount_due REAL DEFAULT 0,
        invoice_date TEXT
    )""")
    # Daily Cash & Revenues
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        record_date TEXT
    )""")
    # Expenses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_type TEXT NOT NULL,
        amount REAL NOT NULL,
        notes TEXT,
        expense_date TEXT
    )""")
    # Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_date TEXT,
        total_cost_value REAL,
        actual_cash_received REAL,
        total_expenses REAL,
        total_paid_suppliers REAL,
        total_due_suppliers REAL,
        net_profit REAL,
        details TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

# Session State for Ghost Mode
if "show_profit_tab" not in st.session_state:
    st.session_state.show_profit_tab = True
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 3. Main Title
st.title("💼 نظام المستودع الذكي وإدارة الجرد المتقدم")
st.write("نظام متكامل يعتمد على الجرد الدوري لاستنتاج المبيعات والأرباح دون الحاجة لكاشير يومي.")

# Ghost mode activation via secret input
secret_trigger = st.text_input("البحث العام في النظام / رمز التفعيل السري", type="password", help="اكتب الكود السري هنا لإعادة إظهار صفحة الأرباح المخفية")
if secret_trigger == OWNER_PIN:
    st.session_state.show_profit_tab = True

# Define available tabs
all_tabs = ["📦 المشتريات والموردين", "💸 الخزينة والمصاريف", "🔍 البحث والتعديلات", "🧮 إجراء جرد جديد", "📊 الأرباح وسجلات الجرد الخفية"]
if not st.session_state.show_profit_tab:
    all_tabs.remove("📊 الأرباح وسجلات الجرد الخفية")

tabs = st.tabs(all_tabs)

# ==================== TAB 1: PURCHASES & SUPPLIERS ====================
with tabs[0]:
    st.subheader("🛒 تسجيل بضاعة واردة (فاتورة شراء)")
    
    p_conn = sqlite3.connect(DB_FILE)
    existing_prods = pd.read_sql_query("SELECT DISTINCT product_name FROM inventory", p_conn)['product_name'].tolist()
    p_conn.close()
    
    with st.form("purchase_form", clear_on_submit=True):
        sup_name = st.text_input("اسم المورد / الشركة")
        
        prod_type = st.radio("نوع المنتج", ["منتج مسجل سابقاً", "منتج جديد تماماً"], horizontal=True)
        if prod_type == "منتج مسجل سابقاً" and existing_prods:
            p_name = st.selectbox("اختر المنتج من القائمة", existing_prods)
        else:
            p_name = st.text_input("اسم المنتج الجديد")
            
        p_qty = st.number_input("الكمية المشتراة", min_value=1, step=1)
        p_cost = st.number_input("سعر الشراء للقطعة (ج.م)", min_value=0.0, step=1.0)
        p_sell = st.number_input("سعر البيع المقترح للقطعة (ج.م) - اختياري", min_value=0.0, step=1.0, value=0.0)
        
        p_paid = st.number_input("المبلغ المدفوع للمورد حالياً (ج.م)", min_value=0.0, step=10.0)
        p_date = st.date_input("تاريخ الفاتورة").strftime("%Y-%m-%d")
        
        submit_purchase = st.form_submit_button("حفظ فاتورة الشراء وتحديث المستودع")
        
        if submit_purchase and p_name and sup_name:
            total_c = p_qty * p_cost
            due_c = total_c - p_paid
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""INSERT INTO purchase_invoices (supplier_name, product_name, quantity, cost_price, total_cost, amount_paid, amount_due, invoice_date)
                         VALUES (?,?,?,?,?,?,?,?)""", (sup_name, p_name, p_qty, p_cost, total_c, p_paid, due_c, p_date))
            
            c.execute("SELECT id, total_received, current_stock FROM inventory WHERE product_name = ?", (p_name,))
            row = c.fetchone()
            if row:
                new_total = row[1] + p_qty
                new_stock = row[2] + p_qty
                if p_sell > 0:
                    c.execute("UPDATE inventory SET total_received=?, current_stock=?, cost_price=?, sell_price=?, last_updated=? WHERE id=?",
                              (new_total, new_stock, p_cost, p_sell, p_date, row[0]))
                else:
                    c.execute("UPDATE inventory SET total_received=?, current_stock=?, cost_price=?, last_updated=? WHERE id=?",
                              (new_total, new_stock, p_cost, p_date, row[0]))
            else:
                c.execute("INSERT INTO inventory (product_name, total_received, current_stock, cost_price, sell_price, last_updated) VALUES (?,?,?,?,?,?)",
                          (p_name, p_qty, p_qty, p_cost, p_sell, p_date))
                
            conn.commit()
            conn.close()
            st.success(f"تم تسجيل الفاتورة بنجاح وتحديث المخزن لـ {p_name}!")
            
            wa_text = f"📄 *فاتورة شراء من: {sup_name}*\n📅 التاريخ: {p_date}\n📦 المنتج: {p_name}\n🔢 الكمية: {p_qty}\n💰 سعر الشراء: {p_cost} ج.م\n💵 الإجمالي: {total_c} ج.م\n💳 المدفوع: {p_paid} ج.م\n🔴 المتبقي (آجل): {due_c} ج.م"
            encoded_text = urllib.parse.quote(wa_text)
            wa_url = f"https://api.whatsapp.com/send?text={encoded_text}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px;border:none;border-radius:5px;width:100%;font-weight:bold;cursor:pointer;">📲 مشاركة الفاتورة عبر الواتساب</button></a>', unsafe_allow_html=True)

# ==================== TAB 2: CASH & EXPENSES ====================
with tabs[1]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 خزينة نهاية اليوم (الأموال الواردة)")
        with st.form("revenue_form", clear_on_submit=True):
            rev_amount = st.number_input("إجمالي المبلغ الوارد اليومي (ج.م)", min_value=0.0, step=50.0)
            rev_date = st.date_input("تاريخ التحصيل", key="rev_date").strftime("%Y-%m-%d")
            submit_rev = st.form_submit_button("تسجيل الإيراد المالي في الخزنة")
            if submit_rev and rev_amount > 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO daily_revenue (amount, record_date) VALUES (?,?)", (rev_amount, rev_date))
                conn.commit()
                conn.close()
                st.success("تم إيداع المبلغ في سجل الخزينة بنجاح!")
                
    with col2:
        st.subheader("🔴 المصاريف والنفقات التشغيلية")
        with st.form("expense_form", clear_on_submit=True):
            exp_type = st.selectbox("نوع المصروف", ["مرتبات عمال", "صيانة وتصليح", "إيجار", "كهرباء ومياه", "مصاريف أخرى"])
            exp_amount = st.number_input("قيمة المصروف (ج.م)", min_value=0.0, step=10.0)
            exp_notes = st.text_area("تفاصيل وملاحظات إضافية")
            exp_date = st.date_input("تاريخ الصرف", key="exp_date").strftime("%Y-%m-%d")
            submit_exp = st.form_submit_button("تسجيل المصروف")
            if submit_exp and exp_amount > 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO expenses (expense_type, amount, notes, expense_date) VALUES (?,?)", (exp_type, exp_amount, exp_notes, exp_date))
                conn.commit()
                conn.close()
                st.success("تم تسجيل المصروف وخصمه بنجاح!")

# ==================== TAB 3: SEARCH & EDIT ====================
with tabs[2]:
    st.subheader("🔍 محرك البحث والتعديل المتقدم")
    
    search_query = st.text_input("ابحث هنا (باسم المنتج، المورد، أو التاريخ)")
    search_category = st.selectbox("اختر الجدول الذي تريد البحث فيه وتعديله", ["فاتورة مشتريات", "المستودع الحالي", "سجل الخزينة اليومي", "سجل المصاريف"])
    
    conn = sqlite3.connect(DB_FILE)
    if search_category == "فاتورة مشتريات":
        df = pd.read_sql_query("SELECT * FROM purchase_invoices", conn)
    elif search_category == "المستودع الحالي":
        df = pd.read_sql_query("SELECT * FROM inventory", conn)
    elif search_category == "سجل الخزينة اليومي":
        df = pd.read_sql_query("SELECT * FROM daily_revenue", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()
    
    if search_query:
        df = df.astype(str)
        df = df[df.apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)]
        
    st.write(f"📊 النتائج المتاحة ({len(df)} سجل):")
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key=f"editor_{search_category}")
    
    if st.button("💾 حفظ التعديلات والتغييرات بشكل نهائي"):
        conn = sqlite3.connect(DB_FILE)
        if search_category == "فاتورة مشتريات":
            edited_df.to_sql("purchase_invoices", conn, if_exists="replace", index=False)
        elif search_category == "المستودع الحالي":
            edited_df.to_sql("inventory", conn, if_exists="replace", index=False)
        elif search_category == "سجل الخزينة اليومي":
            edited_df.to_sql("daily_revenue", conn, if_exists="replace", index=False)
        else:
            edited_df.to_sql("expenses", conn, if_exists="replace", index=False)
        conn.commit()
        conn.close()
        st.success("تم تحديث وحفظ البيانات المعدلة بنجاح!")

# ==================== TAB 4: NEW AUDIT (الجرد الجديد) ====================
with tabs[3]:
    st.subheader("🧮 شاشة إجراء جرد فعلي للمستودع")
    
    conn = sqlite3.connect(DB_FILE)
    inv_data = pd.read_sql_query("SELECT id, product_name, total_received, cost_price FROM inventory", conn)
    
    # Calculate current totals for suppliers invoices (Paid vs Due)
    totals_sups = pd.read_sql_query("SELECT SUM(amount_paid), SUM(amount_due) FROM purchase_invoices", conn)
    total_paid_sups = totals_sups.iloc[0,0] or 0.0
    total_due_sups = totals_sups.iloc[0,1] or 0.0
    
    total_rev_all = pd.read_sql_query("SELECT SUM(amount) FROM daily_revenue", conn).iloc[0,0] or 0.0
    total_exp_all = pd.read_sql_query("SELECT SUM(amount) FROM expenses", conn).iloc[0,0] or 0.0
    conn.close()
    
    st.write("📝 أدخل الكميات الفردية الحالية الموجودة في المحل لتوليد التقرير الحسابي الحقيقي:")
    
    if "audit_input" not in st.session_state or len(st.session_state.audit_input) != len(inv_data):
        inv_data['الكمية الفردية الفعلية بالمحل حالياً'] = inv_data['total_received']
        st.session_state.audit_input = inv_data.copy()
        
    audit_editor = st.data_editor(st.session_state.audit_input[['id', 'product_name', 'total_received', 'cost_price', 'الكمية الفردية الفعلية بالمحل حالياً']], 
                                  use_container_width=True, disabled=['id', 'product_name', 'total_received', 'cost_price'])
    
    st.markdown("---")
    st.subheader("💼 مطابقة الجرد الختامي بالخزينة المالية الحالية")
    
    actual_cash_input = st.number_input("تأكيد إجمالي الكاش الفعلي المتوفر في الخزينة حالياً (ج.م)", value=float(total_rev_all))
    
    if st.button("📊 تشغيل ومعالجة التقرير الختامي للجرد المستنتج"):
        total_cost_val = 0.0
        details_list = []
        
        for index, row in audit_editor.iterrows():
            total_in = row['total_received']
            actual_now = row['الكمية الفردية الفعلية بالمحل حالياً']
            sold_qty = total_in - actual_now  # الكمية المباعة المستنتجة
            
            cost_p = row['cost_price']
            item_cost = sold_qty * cost_p  # تضريب الكمية المباعة × سعر الشراء
            total_cost_val += item_cost
            
            details_list.append(f"المنتج: {row['product_name']} | الكمية المستنتجة المباعة: {sold_qty} قطع | تكلفة الشراء المضروبة: {item_cost:,.2f} ج.م")
            
        # New Financial Formula: المكسب الفعلي = الكاش - (المدفوع للموردين + الآجل للموردين + النفقات والمصاريف)
        net_prof = actual_cash_input - (total_paid_sups + total_due_sups + total_exp_all)
        
        st.markdown("### 📋 النتيجة الحسابية المعتمدة بناءً على تضريب سعر الشراء والخزينة:")
        st.write(f"🔹 **إجمالي تكلفة البضاعة التي خرجت من المستودع (المباعة × سعر الشراء):** {total_cost_val:,.2f} ج.م")
        st.write(f"🔹 **إجمالي الكاش المتوفر حالياً بالخزينة:** {actual_cash_input:,.2f} ج.م")
        st.write(f"🔹 **إجمالي الأموال المدفوعة للموردين:** {total_paid_sups:,.2f} ج.م")
        st.write(f"🔹 **إجمالي الآجل المتبقي (الخارجي للموردين):** {total_due_sups:,.2f} ج.م")
        st.write(f"🔹 **إجمالي النفقات والمصاريف المخصومة:** {total_exp_all:,.2f} ج.م")
        
        # Display Net Profit clearly
        if net_prof >= 0:
            st.success(f"💰 **صافي المكسب الفعلي الفائض:** {net_prof:,.2f} ج.م")
        else:
            st.error(f"🚨 **عجز مالي / خسارة فعلية بالخزينة بمقدار:** {net_prof:,.2f} ج.م")
            
        st.info("💡 تم حساب الأرباح والمطابقة، لاعتماد هذا الجرد وحفظه بشكل نهائي في السجلات التاريخية، يرجى إدخال الرمز السري للمالك في التبويب المخصص للأرباح.")
        
        st.session_state.temp_audit = {
            "cost": total_cost_val,
            "cash": actual_cash_input,
            "expenses": total_exp_all,
            "paid_sups": total_paid_sups,
            "due_sups": total_due_sups,
            "net": net_prof,
            "details": "\n".join(details_list)
        }

# ==================== TAB 5: HIDDEN REVENUE & AUDIT LOGS ====================
if st.session_state.show_profit_tab:
    with tabs[-1]:
        st.subheader("🔒 اللوحة السرية لإدارة الأرباح والمكاسب العليا")
        
        if not st.session_state.authenticated:
            pin_input = st.text_input("أدخل رمز المرور الخاص بالمالك لفتح الخزنة (PIN)", type="password")
            if pin_input == OWNER_PIN:
                st.session_state.authenticated = True
                st.rerun()
            else:
                if pin_input: st.error("الرمز السري خاطئ! تم حجب البيانات.")
        
        if st.session_state.authenticated:
            st.success("🔓 تم التحقق بنجاح. مرحباً بك يا مالك العمل.")
            
            hide_completely = st.checkbox("🚫 تفعيل وضع الشبح (إخفاء هذه الصفحة تماماً من القائمة الآن)")
            if hide_completely:
                st.session_state.show_profit_tab = False
                st.session_state.authenticated = False
                st.rerun()
                
            st.markdown("---")
            st.subheader("📊 تقارير تحليل الأداء وصافي الأرباح الحقيقية")
            
            if "temp_audit" in st.session_state:
                st.markdown('<div class="report-box">📝 يوجد جرد معلق تم تشغيله للتو، يمكنك حفظه الآن في الأرشيف الرسمي للشركة:</div>', unsafe_allow_html=True)
                if st.button("💾 ترحيل واعتماد هذا الجرد رسمياً في السجل التاريخي"):
                    t = st.session_state.temp_audit
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("""INSERT INTO audit_logs (audit_date, total_cost_value, actual_cash_received, total_expenses, total_paid_suppliers, total_due_suppliers, net_profit, details)
                                 VALUES (?,?,?,?,?,?,?,?)""", (datetime.now().strftime("%Y-%m-%d %H:%M"), t['cost'], t['cash'], t['expenses'], t['paid_sups'], t['due_sups'], t['net'], t['details']))
                    
                    for index, row in st.session_state.audit_input.iterrows():
                        c.execute("UPDATE inventory SET total_received=?, current_stock=? WHERE id=?", 
                                  (row['الكمية الفردية الفعلية بالمحل حالياً'], row['الكمية الفردية الفعلية بالمحل حالياً'], row['id']))
                    conn.commit()
                    conn.close()
                    del st.session_state.temp_audit
                    st.success("تم ترحيل الجرد وحفظه بنجاح وتصفير الدورة المستندية لبدء فترة جديدة!")
                    st.rerun()
            
            st.markdown("### 📅 سجل عمليات الجرد السابقة والأرباح المؤرشفة")
            conn = sqlite3.connect(DB_FILE)
            audit_history_df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY id DESC", conn)
            top_products = pd.read_sql_query("SELECT product_name AS 'المنتج', SUM(quantity) AS 'إجمالي الكمية المسحوبة من الموردين' FROM purchase_invoices GROUP BY product_name ORDER BY SUM(quantity) DESC LIMIT 5", conn)
            conn.close()
            
            if audit_history_df.empty:
                st.info("لا توجد عمليات جرد مرحّلة ومحفوظة بعد.")
            else:
                st.dataframe(audit_history_df, use_container_width=True)
                
                st.markdown("### 🗓️ التحليل الزمني للمكاسب (شهري وسنوي):")
                audit_history_df['تاريخ الجرد'] = pd.to_datetime(audit_history_df['audit_date'])
                audit_history_df['الشهر'] = audit_history_df['تاريخ الجرد'].dt.to_period('M')
                
                monthly_perf = audit_history_df.groupby('الشهر')[['actual_cash_received', 'net_profit']].sum()
                st.write("إجمالي الكاش وصافي الأرباح الفعلية الفائضة مجمعة حسب الشهر:")
                st.dataframe(monthly_perf, use_container_width=True)
                
            st.markdown("---")
            st.markdown("### 🔥 تحليل المنتجات الأكثر سحباً وحركة:")
            if top_products.empty:
                st.info("لا توجد مبيعات أو مشتريات كافية لتوليد تحليل الأكثر مسحوباً.")
            else:
                st.dataframe(top_products, use_container_width=True)
