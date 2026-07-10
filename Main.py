import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# 1. إعدادات الواجهة الاحترافية والدعم الكامل للغة العربية (RTL)
st.set_page_config(page_title="تطبيق المخزن المتكامل", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}
    body {direction: rtl; text-align: right;}
    div.stButton > button {width: 100%; font-weight: bold; background-color: #047857; color: white; border-radius: 8px; padding: 10px;}
    div.stButton > button:hover {background-color: #059669; color: white;}
    .stTabs [data-baseweb="tab"] {font-size: 15px; font-weight: bold; color: #065F46;}
    .report-card {padding: 20px; border-radius: 8px; background-color: #F0FDF4; border-right: 6px solid #10B981; margin-bottom: 15px;}
    .expense-card {padding: 20px; border-radius: 8px; background-color: #FFFBEB; border-right: 6px solid #F59E0B; margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

DB_NAME = "makhzan_ultra_v4.db"

# 2. تأسيس قاعدة البيانات والجداول المحاسبية الجديدة
def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # المخزون
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT UNIQUE NOT NULL,
        stock_qty INTEGER DEFAULT 0,
        cost_price REAL DEFAULT 0
    )""")
    
    # الفواتير
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_num TEXT NOT NULL,
        product_name TEXT NOT NULL,
        qty_added INTEGER NOT NULL,
        cost_price REAL NOT NULL,
        total_cost REAL NOT NULL,
        invoice_date TEXT NOT NULL
    )""")
    
    # الأموال الواردة
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incoming_funds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        source_details TEXT,
        fund_date TEXT NOT NULL
    )""")
    
    # الآواجل الخارجية
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS credit_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        initial_credit REAL DEFAULT 0,
        final_credit REAL DEFAULT 0,
        record_date TEXT NOT NULL
    )""")
    
    # المصروفات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        notes TEXT,
        expense_date TEXT NOT NULL
    )""")
    
    # أرشيف الجرد
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_date TEXT NOT NULL,
        cost_of_sold REAL NOT NULL,
        cash_counted REAL NOT NULL,
        credit_diff REAL NOT NULL,
        period_expenses REAL NOT NULL,
        net_profit REAL NOT NULL,
        log_details TEXT
    )""")
    
    conn.commit()
    conn.close()

init_database()

st.title("📦 نظام إدارة المخزن والمالية المتكامل")
st.write("نظام محاسبي باللغة العربية مخصص لمتابعة الوارد، الكاش الفعلي، الآواجل، والجرد الدوري.")

# إنشاء السبع صفحات المطلوبة بدقة
tabs = st.tabs([
    "📥 صفحة الوارد (السجلات التاريخية)",
    "🧾 تسجيل الفواتير والمشاركة",
    "💵 صفحة الأموال الواردة",
    "📑 صفحة الآواجل الخارجية",
    "💸 كشف المسحوبات والمصروفات",
    "🧮 صفحة الجرد المستقلة",
    "📊 تقارير المخزن والجرد المسبق"
])

# ==================== 1️⃣ صفحة الوارد (السجلات التاريخية) ====================
with tabs[0]:
    st.subheader("📋 كشف الوارد التاريخي الشامل")
    conn = sqlite3.connect(DB_NAME)
    all_invoices_df = pd.read_sql_query("""
        SELECT invoice_num AS 'رقم الفاتورة', product_name AS 'اسم الصنف', qty_added AS 'الالكمية الواردة', 
               cost_price AS 'سعر الشراء للوحدة', total_cost AS 'إجمالي التكلفة', invoice_date AS 'تاريخ الفاتورة' 
        FROM invoices ORDER BY id DESC
    """, conn)
    conn.close()
    
    if all_invoices_df.empty:
        st.info("لا توجد أي فواتير واردة مسجلة حالياً.")
    else:
        st.dataframe(all_invoices_df, use_container_width=True)

# ==================== 2️⃣ صفحة تسجيل الفواتير والمشاركة ====================
with tabs[1]:
    st.subheader("🧾 تسجيل فاتورة بضاعة جديدة ومشاركتها")
    if "invoice_items" not in st.session_state:
        st.session_state.invoice_items = []
        
    col_inv1, col_inv2 = st.columns([1, 2])
    with col_inv1:
        inv_id = st.text_input("رقم الفاتورة الحالية", value="1")
        inv_date = st.date_input("تاريخ الفاتورة الحالية").strftime("%Y-%m-%d")
        prod_name = st.text_input("اسم الصنف المشتري").strip()
        prod_qty = st.number_input("الكمية المشتراة الحالية", min_value=1, step=1)
        prod_cost = st.number_input("سعر الشراء الحالي للقطعة (ج.م)", min_value=0.0, step=1.0)
        
        if st.button("إضافة الصنف إلى القائمة المؤقتة"):
            if prod_name:
                st.session_state.invoice_items.append({
                    "invoice_num": inv_id, "invoice_date": inv_date, "product_name": prod_name,
                    "qty": prod_qty, "cost": prod_cost, "total": prod_qty * prod_cost
                })
                st.success(f"تمت إضافة {prod_name}")
                st.rerun()
                
    with col_inv2:
        if st.session_state.invoice_items:
            df_temp = pd.DataFrame(st.session_state.invoice_items)
            df_temp.columns = ["رقم الفاتورة", "التاريخ", "اسم الصنف", "الكمية", "سعر الشراء", "الإجمالي"]
            st.dataframe(df_temp, use_container_width=True)
            
            if st.button("💾 حفظ الفاتورة نهائياً وتحديث كميات المخزن"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                for item in st.session_state.invoice_items:
                    c.execute("INSERT INTO invoices (invoice_num, product_name, qty_added, cost_price, total_cost, invoice_date) VALUES (?,?,?,?,?,?)",
                              (item['invoice_num'], item['product_name'], item['qty'], item['cost'], item['total'], item['invoice_date']))
                    c.execute("SELECT stock_qty FROM inventory WHERE product_name = ?", (item['product_name'],))
                    row = c.fetchone()
                    if row:
                        c.execute("UPDATE inventory SET stock_qty = ?, cost_price = ? WHERE product_name = ?", (row[0] + item['qty'], item['cost'], item['product_name']))
                    else:
                        c.execute("INSERT INTO inventory (product_name, stock_qty, cost_price) VALUES (?, ?, ?)", (item['product_name'], item['qty'], item['cost']))
                conn.commit()
                conn.close()
                st.session_state.last_saved_invoice = st.session_state.invoice_items.copy()
                st.session_state.invoice_items = []
                st.success("🎯 تم الحفظ بنجاح وتحديث المخزن!")
                st.rerun()
        
        if "last_saved_invoice" in st.session_state and st.session_state.last_saved_invoice:
            st.markdown("---")
            st.markdown("### 📲 مشاركة الفاتورة الأخيرة المقيدة عبر واتساب")
            msg = "📋 *فاتورة شراء واردة جديدة*\n"
            for x in st.session_state.last_saved_invoice:
                msg += f"▪️ {x['product_name']} | كمية: {x['qty']} | سعر: {x['cost']} ج.م\n"
            
            encoded_msg = urllib.parse.quote(msg)
            whatsapp_url = f"https://wa.me/?text={encoded_msg}"
            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; width:100%; font-weight:bold; border:none; padding:10px; border-radius:8px; cursor:pointer;">🟢 إرسال تفاصيل الفاتورة عبر واتساب</button></a>', unsafe_allow_html=True)

# ==================== 3️⃣ صفحة الأموال الواردة ====================
with tabs[2]:
    st.subheader("💵 سجل المبالغ والأموال الواردة (الكاش الفعلي)")
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        st.markdown("### 📥 تسجيل مبلغ وارد")
        f_amount = st.number_input("قيمة المبلغ التوريدي (ج.م)", min_value=0.0, step=50.0)
        f_source = st.text_input("البيان / مصدر التوريد")
        f_date = st.date_input("تاريخ ورود المبلغ").strftime("%Y-%m-%d")
        if st.button("تسجيل وتجميع المبلغ"):
            if f_amount > 0:
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO incoming_funds (amount, source_details, fund_date) VALUES (?, ?, ?)", (f_amount, f_source, f_date))
                conn.commit()
                conn.close()
                st.success("تم قيد المبلغ بنجاح.")
                st.rerun()
    with col_f2:
        conn = sqlite3.connect(DB_NAME)
        funds_df = pd.read_sql_query("SELECT id AS 'كود', amount AS 'المبلغ', source_details AS 'البيان', fund_date AS 'التاريخ' FROM incoming_funds", conn)
        total_incoming_cash = conn.execute("SELECT SUM(amount) FROM incoming_funds").fetchone()[0] or 0.0
        conn.close()
        st.markdown(f"### 💰 إجمالي الكاش الفعلي المتجمع للفترة الحالية: `{total_incoming_cash:,.2f} ج.م`")
        st.dataframe(funds_df, use_container_width=True)

# ==================== 4️⃣ صفحة الآواجل الخارجية ====================
with tabs[3]:
    st.subheader("📑 حساب الآواجل الخارجية والديون المستحقة عند العملاء")
    st.write("أدخل الديون الخاصة بالعملاء من بداية فترة الشراء والعمل، والآجل القائم في نهاية فترة العمل ليقوم النظام باحتساب الفارق التلقائي ودبجه في الجرد.")
    
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        st.markdown("### ➕ قيد حساب آجل لعميل")
        c_name = st.text_input("اسم العميل أو الحساب").strip()
        c_init = st.number_input("الآجل في بداية فترة العمل (ج.م)", min_value=0.0, step=50.0)
        c_final = st.number_input("الآجل في نهاية فترة العمل (ج.م)", min_value=0.0, step=50.0)
        c_date = st.date_input("التاريخ المسجل لحساب العميل").strftime("%Y-%m-%d")
        if st.button("حفظ حساب العميل"):
            if c_name:
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO credit_accounts (customer_name, initial_credit, final_credit, record_date) VALUES (?, ?, ?, ?)", (c_name, c_init, c_final, c_date))
                conn.commit()
                conn.close()
                st.success("تم قيد بيانات العميل.")
                st.rerun()
    with col_c2:
        conn = sqlite3.connect(DB_NAME)
        credits_df = pd.read_sql_query("SELECT id AS 'كود العميل', customer_name AS 'اسم العميل', initial_credit AS 'الآجل بالبداية', final_credit AS 'الآجل بالنهاية', (initial_credit - final_credit) AS 'فارق الآجل المستحق', record_date AS 'التاريخ' FROM credit_accounts", conn)
        total_init_credit = conn.execute("SELECT SUM(initial_credit) FROM credit_accounts").fetchone()[0] or 0.0
        total_final_credit = conn.execute("SELECT SUM(final_credit) FROM credit_accounts").fetchone()[0] or 0.0
        conn.close()
        
        credit_diff_total = total_init_credit - total_final_credit
        st.markdown(f"📊 إجمالي آجل البداية: `{total_init_credit:,.2f}` | إجمالي آجل النهاية: `{total_final_credit:,.2f}`")
        st.markdown(f"➡️ **صافي فارق الآواجل المحتسب لعملية الجرد:** `{credit_diff_total:,.2f} ج.م`")
        st.dataframe(credits_df, use_container_width=True)

# ==================== 5️⃣ كشف المسحوبات والمصروفات ====================
with tabs[4]:
    st.subheader("💸 إدارة النفقات والمصروفات النقدية")
    col_exp1, col_exp2 = st.columns([1, 2])
    with col_exp1:
        exp_amount = st.number_input("قيمة مبلغ المصروف (ج.م)", min_value=0.0, step=10.0)
        exp_notes = st.text_input("سبب الصرف / البيان")
        exp_date = st.date_input("تاريخ الصرف الحركي").strftime("%Y-%m-%d")
        if st.button("قيد بند المصروف"):
            if exp_amount > 0:
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO expenses (amount, notes, expense_date) VALUES (?, ?, ?)", (exp_amount, exp_notes, exp_date))
                conn.commit()
                conn.close()
                st.success("تم قيد المصروف.")
                st.rerun()
    with col_exp2:
        conn = sqlite3.connect(DB_NAME)
        expenses_df = pd.read_sql_query("SELECT id AS 'كود', amount AS 'المبلغ', notes AS 'البيان', expense_date AS 'التاريخ' FROM expenses", conn)
        total_exp = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0
        conn.close()
        st.markdown(f"### إجمالي النفقات الجارية الحالية: `{total_exp:,.2f} ج.م`")
        st.dataframe(expenses_df, use_container_width=True)

# ==================== 6️⃣ صفحة الجرد المستقلة الدورية ====================
with tabs[5]:
    st.subheader("🧮 شاشة معالجة الجرد الختامي الدوري واحتساب الأرباح الحقيقية")
    
    conn = sqlite3.connect(DB_NAME)
    inv_data = pd.read_sql_query("SELECT id, product_name, stock_qty, cost_price FROM inventory", conn)
    total_cash_auto = conn.execute("SELECT SUM(amount) FROM incoming_funds").fetchone()[0] or 0.0
    t_init_c = conn.execute("SELECT SUM(initial_credit) FROM credit_accounts").fetchone()[0] or 0.0
    t_final_c = conn.execute("SELECT SUM(final_credit) FROM credit_accounts").fetchone()[0] or 0.0
    total_exp_current = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0
    conn.close()
    
    net_credit_diff = t_init_c - t_final_c
    
    st.info(f"💡 المحاسب الآلي سحب المخرجات الحالية: الكاش الفعلي المتجمع = {total_cash_auto:,.2f} ج.م | فارق الآواجل المستحق = {net_credit_diff:,.2f} ج.م")
    st.write("قم بإدخال كميات العد الفعلي على الرفوف بالجدول أدناه لاستخراج المكسب:")
    
    if "audit_df_v4" not in st.session_state or len(st.session_state.audit_df_v4) != len(inv_data):
        inv_data['الكمية المتبقية (العد الفعلي)'] = inv_data['stock_qty']
        st.session_state.audit_df_v4 = inv_data.copy()
        
    editable_table = st.data_editor(
        st.session_state.audit_df_v4[['id', 'product_name', 'stock_qty', 'cost_price', 'الكمية المتبقية (العد الفعلي)']],
        use_container_width=True, disabled=['id', 'product_name', 'stock_qty', 'cost_price']
    )
    
    if st.button("📊 معالجة واستخراج تقرير حجم المكسب الفعلي الحقيقي"):
        total_cost_sold = 0.0
        log_lines = []
        for idx, row in editable_table.iterrows():
            qty_sold = row['stock_qty'] - row['الكمية المتبقية (العد الفعلي)']
            item_cost_sold = qty_sold * row['cost_price']
            total_cost_sold += item_cost_sold
            log_lines.append(f"صنف: {row['product_name']} | المباع: {qty_sold} | تكلفة الشراء: {item_cost_sold}")
            
        # المعادلة الجديدة المتكاملة بناء على طلبك
        final_real_profit = total_cash_auto + net_credit_diff - total_cost_sold
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.markdown(f"""
            <div class="report-card">
                <h3>🏆 تقرير الأرباح وحجم المكسب الفعلي</h3>
                <p>🔹 إجمالي الكاش الفعلي المتجمع (من صفحة الأموال الواردة): <b>{total_cash_auto:,.2f} ج.م</b></p>
                <p>🔹 صافي فارق حساب الآواجل للعملاء: <b>{net_credit_diff:,.2f} ج.م</b></p>
                <p>🔹 إجمالي تكلفة الشراء للبضاعة المباعة فعلياً: <b>{total_cost_sold:,.2f} ج.م</b></p>
                <hr>
                <h4>💵 حجم المكسب الفعلي النهائي الحقيقي: {final_real_profit:,.2f} ج.م</h4>
            </div>
            """, unsafe_allow_html=True)
        with col_res2:
            st.markdown(f"""
            <div class="expense-card">
                <h3>⚠️ حجم المصروفات المسجلة</h3>
                <p>📍 إجمالي مصروفات الفترة الجارية: <b>{total_exp_current:,.2f} ج.م</b></p>
                <small>*معروضة كبيان استرشادي منفصل بناءً على رغبتك.</small>
            </div>
            """, unsafe_allow_html=True)
            
        st.session_state.pending_audit_v4 = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "cost_sold": total_cost_sold,
            "cash": total_cash_auto, "credit_diff": net_credit_diff, "expenses": total_exp_current,
            "net": final_real_profit, "log": "\n".join(log_lines), "table": editable_table
        }
        
    if "pending_audit_v4" in st.session_state:
        if st.button("💾 اعتماد وترحيل جلسة الجرد نهائياً (تحديث المخزن وتصفير الكاش والآواجل والمصروفات)"):
            pa = st.session_state.pending_audit_v4
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            c.execute("""INSERT INTO audit_archive (audit_date, cost_of_sold, cash_counted, credit_diff, period_expenses, net_profit, log_details) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                      (pa['date'], pa['cost_sold'], pa['cash'], pa['credit_diff'], pa['expenses'], pa['net'], pa['log']))
            
            for _, r in pa['table'].iterrows():
                c.execute("UPDATE inventory SET stock_qty = ? WHERE id = ?", (r['الكمية المتبقية (العد الفعلي)'], r['id']))
                
            # التصفير التلقائي لبدء فترة زمنية جديدة بنجاح
            c.execute("DELETE FROM incoming_funds")
            c.execute("DELETE FROM credit_accounts")
            c.execute("DELETE FROM expenses")
            
            conn.commit()
            conn.close()
            del st.session_state.pending_audit_v4
            st.success("🎯 تم ترحيل الجلسة بنجاح وتصفير الأرصدة المؤقتة لبدء فترة عمل جديدة!")
            st.rerun()

# ==================== 7️⃣ صفحة تقارير المخزن والجرد المسبق ====================
with tabs[6]:
    st.subheader("📊 إدارة المخزون المتقدمة وسجلات الجرد السابقة")
    
    st.markdown("### 📦 تعديل أسعار وكميات بضاعة المستودع الحالية مباشرة")
    st.write("يمكنك النقر مباشرة على خلايا الجدول أدناه لتعديل أسعار الشراء أو كمية الرف، ثم الضغط على زر الحفظ:")
    
    conn = sqlite3.connect(DB_NAME)
    stock_df = pd.read_sql_query("SELECT id, product_name AS 'اسم المنتج', stock_qty AS 'الكمية المتاحة', cost_price AS 'سعر الشراء (ج.م)' FROM inventory", conn)
    conn.close()
    
    edited_stock_table = st.data_editor(stock_df, use_container_width=True, disabled=['id', 'اسم المنتج'])
    
    if st.button("💾 حفظ تعديلات أسعار الموديلات أو المنتجات الحالية بالمخزن"):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        for _, row in edited_stock_table.iterrows():
            c.execute("UPDATE inventory SET stock_qty = ?, cost_price = ? WHERE id = ?", (row['الكمية المتاحة'], row['سعر الشراء (ج.م)'], row['id']))
        conn.commit()
        conn.close()
        st.success("🎯 تم تحديث وتعديل أسعار المنتجات وكمياتها بنجاح!")
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🗄️ سجلات جميع عمليات الجرد والتقارير المعتمدة السابقة")
    conn = sqlite3.connect(DB_NAME)
    archive_df = pd.read_sql_query("""
        SELECT id AS 'رقم الجلسة', audit_date AS 'تاريخ الجرد', cost_of_sold AS 'تكلفة المبيعات', 
               cash_counted AS 'الكاش المرحل', credit_diff AS 'فارق الآواجل', 
               period_expenses AS 'المصروفات', net_profit AS 'حجم المكسب الفعلي' 
        FROM audit_archive ORDER BY id DESC
    """, conn)
    conn.close()
    
    if archive_df.empty:
        st.info("لا توجد جلسات جرد سابقة معتمدة ومرحلة بعد.")
    else:
        st.dataframe(archive_df, use_container_width=True)

    # التصفير العام للحماية
    st.markdown("---")
    st.markdown("### ⚙️ إدارة النظام المتقدمة")
    confirm_reset = st.checkbox("أوافق على مسح كافة الجداول، الفواتير، الآواجل والبيانات بالكامل لبدء نشاط من الصفر.")
    if st.button("⚠️ إعادة ضبط وتصفير قاعدة البيانات بالكامل"):
        if confirm_reset:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS inventory"); c.execute("DROP TABLE IF EXISTS invoices")
            c.execute("DROP TABLE IF EXISTS incoming_funds"); c.execute("DROP TABLE IF EXISTS credit_accounts")
            c.execute("DROP TABLE IF EXISTS expenses"); c.execute("DROP TABLE IF EXISTS audit_archive")
            conn.commit(); conn.close()
            st.success("💥 تم تصفير المخزن بالكامل! يرجى إعادة تنشيط الصفحة.")
            init_database()
            st.rerun()
