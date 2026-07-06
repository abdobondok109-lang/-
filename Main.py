import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. إعدادات الصفحة والواجهة الاحترافية المتناسقة (RTL)
st.set_page_config(page_title="تطبيق المخزن", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}
    body {direction: rtl; text-align: right;}
    div.stButton > button {width: 100%; font-weight: bold; background-color: #047857; color: white; border-radius: 8px; padding: 10px;}
    div.stButton > button:hover {background-color: #059669; color: white;}
    .stTabs [data-baseweb="tab"] {font-size: 16px; font-weight: bold; color: #065F46;}
    .report-card {padding: 20px; border-radius: 8px; background-color: #F0FDF4; border-right: 6px solid #10B981; margin-bottom: 15px;}
    .expense-card {padding: 20px; border-radius: 8px; background-color: #FFFBEB; border-right: 6px solid #F59E0B; margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

DB_NAME = "makhzan_ultra_v3.db"

# 2. إنشاء وتأسيس قاعدة البيانات والجداول المطلوبة
def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # جدول المستودع الرئيسي
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT UNIQUE NOT NULL,
        stock_qty INTEGER DEFAULT 0,
        cost_price REAL DEFAULT 0
    )""")
    
    # جدول الفواتير (الوارد)
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
    
    # جدول المصروفات والنفقات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        notes TEXT,
        expense_date TEXT NOT NULL
    )""")
    
    # جدول أرشيف عمليات الجرد السابقة
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_date TEXT NOT NULL,
        cost_of_sold REAL NOT NULL,
        cash_counted REAL NOT NULL,
        period_expenses REAL NOT NULL,
        net_profit REAL NOT NULL,
        log_details TEXT
    )""")
    
    conn.commit()
    conn.close()

init_database()

# عنوان التطبيق الرئيسي
st.title("📦 تطبيق المخزن الرقمي")
st.write("نظام مبسط يعتمد على فواتير الوارد والجرد الدوري واستنتاج المكاسب الفعلية يدوياً.")

# إنشاء الصفحات الأربعة المطلوبة بدقة بناءً على طلبك
tabs = st.tabs([
    "📥 صفحة الوارد (تسجيل الفواتير)", 
    "🧮 صفحة الجرد الحالي", 
    "💸 كشف المسحوبات والمصروفات",
    "📊 التقارير وجلسات الجرد السابقة"
])

# ==================== 1️⃣ صفحة الوارد (تسجيل الفواتير كـ مجموعات) ====================
with tabs[0]:
    st.subheader("🧾 تسجيل فاتورة بضاعة واردة جديدة")
    st.write("يمكنك هنا تسجيل أكثر من صنف دفعة واحدة تحت نفس رقم الفاتورة والتاريخ.")
    
    if "invoice_items" not in st.session_state:
        st.session_state.invoice_items = []
        
    col_inv1, col_inv2 = st.columns([1, 2])
    
    with col_inv1:
        st.markdown("### ➕ إضافة صنف للفاتورة")
        inv_id = st.text_input("رقم الفاتورة", value="2")
        inv_date = st.date_input("تاريخ الفاتورة").strftime("%Y-%m-%d")
        
        prod_name = st.text_input("اسم الصنف / المنتج").strip()
        prod_qty = st.number_input("الكمية المشتراة", min_value=1, step=1)
        prod_cost = st.number_input("سعر الشراء للقطعة (ج.م)", min_value=0.0, step=1.0)
        
        if st.button("اضف هذا الصنف إلى الفاتورة"):
            if prod_name:
                st.session_state.invoice_items.append({
                    "invoice_num": inv_id,
                    "invoice_date": inv_date,
                    "product_name": prod_name,
                    "qty": prod_qty,
                    "cost": prod_cost,
                    "total": prod_qty * prod_cost
                })
                st.success(f"تمت إضافة {prod_name} للسلة بنجاح.")
            else:
                st.error("الرجاء إدخال اسم الصنف أولاً!")
                
    with col_inv2:
        st.markdown("### 🛒 الأصناف المدرجة في الفاتورة الحالية")
        if st.session_state.invoice_items:
            df_temp = pd.DataFrame(st.session_state.invoice_items)
            df_temp.columns = ["رقم الفاتورة", "التاريخ", "اسم الصنف", "الكمية", "سعر الشراء", "الإجمالي"]
            st.dataframe(df_temp, use_container_width=True)
            
            if st.button("💾 حفظ الفاتورة بالكامل وتحديث المخزن"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                for item in st.session_state.invoice_items:
                    c.execute("""INSERT INTO invoices (invoice_num, product_name, qty_added, cost_price, total_cost, invoice_date) 
                                 VALUES (?, ?, ?, ?, ?, ?)""", 
                              (item['invoice_num'], item['product_name'], item['qty'], item['cost'], item['total'], item['invoice_date']))
                    
                    c.execute("SELECT stock_qty FROM inventory WHERE product_name = ?", (item['product_name'],))
                    row = c.fetchone()
                    if row:
                        new_qty = row[0] + item['qty']
                        c.execute("UPDATE inventory SET stock_qty = ?, cost_price = ? WHERE product_name = ?", (new_qty, item['cost'], item['product_name']))
                    else:
                        c.execute("INSERT INTO inventory (product_name, stock_qty, cost_price) VALUES (?, ?, ?)", (item['product_name'], item['qty'], item['cost']))
                
                conn.commit()
                conn.close()
                st.session_state.invoice_items = [] 
                st.success("🎯 تم حفظ الفاتورة بالكامل وتحديث كميات المخزن بنجاح!")
                st.rerun()
        else:
            st.info("لم تقم بإضافة أي أصناف للفاتورة الحالية بعد.")

# ==================== 2️⃣ صفحة الجرد الحالي وعمل الحسبة المخصصة ====================
with tabs[1]:
    st.subheader("🧮 إجراء جرد المخزن الفعلي واحتساب الأرباح")
    
    conn = sqlite3.connect(DB_NAME)
    inv_data = pd.read_sql_query("SELECT id, product_name, stock_qty, cost_price FROM inventory", conn)
    total_exp = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0
    conn.close()
    
    st.write("قم بعد البضاعة الموجودة في المحل يدوياً ثم اكتب الكمية المتبقية أمام كل صنف:")
    
    if "audit_df" not in st.session_state or len(st.session_state.audit_df) != len(inv_data):
        inv_data['الكمية المتبقية (العد الفعلي بالرف)'] = inv_data['stock_qty']
        st.session_state.audit_df = inv_data.copy()
        
    editable_table = st.data_editor(
        st.session_state.audit_df[['id', 'product_name', 'stock_qty', 'cost_price', 'الكمية المتبقية (العد الفعلي بالرف)']],
        use_container_width=True,
        disabled=['id', 'product_name', 'stock_qty', 'cost_price']
    )
    
    st.markdown("---")
    st.markdown("### 💰 مطابقة الأموال السائلة بالخزينة")
    actual_cash = st.number_input("أدخل إجمالي الأموال النقدية المتوفرة معك حالياً في درج المحل (ج.م)", min_value=0.0, value=0.0, step=100.0)
    
    if st.button("📊 تشغيل ومعالجة تقرير الجرد الختامي"):
        total_cost_sold = 0.0
        log_lines = []
        
        for idx, row in editable_table.iterrows():
            qty_before = row['stock_qty']
            qty_after = row['الكمية المتبقية (العد الفعلي بالرف)']
            qty_sold = qty_before - qty_after 
            
            item_cost_sold = qty_sold * row['cost_price'] 
            total_cost_sold += item_cost_sold
            log_lines.append(f"الصنف: {row['product_name']} | المباع: {qty_sold} | تكلفة الشراء: {item_cost_sold:,.2f} ج.م")
            
        net_actual_profit = actual_cash - total_cost_sold
        
        st.markdown("### 📋 النتائج المالية المعتمدة")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.markdown(f"""
            <div class="report-card">
                <h3>💰 تقرير الأرباح الحقيقية</h3>
                <p>🔹 إجمالي تكلفة البضاعة المباعة (الكمية × سعر الشراء): <b>{total_cost_sold:,.2f} ج.م</b></p>
                <p>🔹 إجمالي الكاش الفعلي المتوفر بالدرج: <b>{actual_cash:,.2f} ج.م</b></p>
                <hr>
                <h4>💵 صافي المكسب الفعلي الفائض: {net_actual_profit:,.2f} ج.م</h4>
            </div>
            """, unsafe_allow_html=True)
            
        with col_res2:
            st.markdown(f"""
            <div class="expense-card">
                <h3>⚠️ حجم المصروفات والنفقات الحالية</h3>
                <p>📍 إجمالي المصروفات المسجلة لهذه الفترة: <b>{total_exp:,.2f} ج.م</b></p>
                <small>*ملاحظة: هذا الرقم معروض للعلم فقط ولم يتم جمعه أو طرحه من الأرباح بناءً على طلبك.</small>
            </div>
            """, unsafe_allow_html=True)
            
        st.session_state.pending_audit = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "cost_sold": total_cost_sold,
            "cash": actual_cash,
            "expenses": total_exp,
            "net": net_actual_profit,
            "log": "\n".join(log_lines),
            "table": editable_table
        }
        
    if "pending_audit" in st.session_state:
        if st.button("💾 ترحيل واعتماد هذا الجرد وتحديث المخزن لبدء فترة جديدة"):
            pa = st.session_state.pending_audit
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            c.execute("""INSERT INTO audit_archive (audit_date, cost_of_sold, cash_counted, period_expenses, net_profit, log_details) 
                         VALUES (?, ?, ?, ?, ?, ?)""", 
                      (pa['date'], pa['cost_sold'], pa['cash'], pa['expenses'], pa['net'], pa['log']))
            
            for _, r in pa['table'].iterrows():
                c.execute("UPDATE inventory SET stock_qty = ? WHERE id = ?", (r['الكمية المتبقية (العد الفعلي بالرف)'], r['id']))
                
            c.execute("DELETE FROM expenses")
            
            conn.commit()
            conn.close()
            del st.session_state.pending_audit
            st.success("🎯 تم اعتماد وترحيل الجرد بنجاح، وتم تصفير المصروفات لبدء دورة عمل جديدة!")
            st.rerun()

# ==================== 3️⃣ كشف المسحوبات والمصروفات ====================
with tabs[2]:
    st.subheader("💸 إدارة النفقات والمصروفات النقدية")
    
    col_exp1, col_exp2 = st.columns([1, 2])
    
    with col_exp1:
        st.markdown("### 📥 تسجيل مصروف جديد")
        with st.form("add_expense_form", clear_on_submit=True):
            exp_amount = st.number_input("قيمة المبلغ المنصرف (ج.م)", min_value=0.0, step=10.0)
            exp_notes = st.text_input("البيان / سبب الصرف (مثل: كهرباء، نقل بضاعة، نثريات)")
            exp_date = st.date_input("تاريخ الصرف").strftime("%Y-%m-%d")
            submit_exp = st.form_submit_button("تسجيل وخصم الكاش")
            
            if submit_exp and exp_amount > 0:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO expenses (amount, notes, expense_date) VALUES (?, ?, ?)", (exp_amount, exp_notes, exp_date))
                conn.commit()
                conn.close()
                st.success("تم تسجيل بند المصروف بنجاح.")
                st.rerun()
                
    with col_exp2:
        st.markdown("### 📑 قائمة المصروفات الجارية خلال فترة الجرد")
        conn = sqlite3.connect(DB_NAME)
        expenses_df = pd.read_sql_query("SELECT id AS 'كود المصروف', amount AS 'المبلغ (ج.م)', notes AS 'البيان/السبب', expense_date AS 'التاريخ' FROM expenses", conn)
        conn.close()
        st.dataframe(expenses_df, use_container_width=True)

# ==================== 4️⃣ صفحة التقارير وحالة بضاعة المستودع والأرشيف ====================
with tabs[3]:
    st.subheader("📊 الأرشيف العام وحركة المخزن الحالية")
    
    col_rep1, col_rep2 = st.columns(2)
    
    with col_rep1:
        st.markdown("### 📦 حالة بضاعة المستودع الحالية (المخزون المتاح)")
        conn = sqlite3.connect(DB_NAME)
        stock_df = pd.read_sql_query("SELECT id AS 'كود الصنف', product_name AS 'اسم المنتج', stock_qty AS 'الكمية الحالية بالرف', cost_price AS 'سعر الشراء (ج.م)' FROM inventory", conn)
        conn.close()
        st.dataframe(stock_df, use_container_width=True)
        
    with col_rep2:
        st.markdown("### 📜 فواتير البضائع التي يتم شراؤها (الوارد)")
        conn = sqlite3.connect(DB_NAME)
        all_invoices_df = pd.read_sql_query("SELECT invoice_num AS 'رقم الفاتورة', product_name AS 'اسم الصنف', qty_added AS 'الكمية الواردة', cost_price AS 'سعر الشراء', total_cost AS 'الإجمالي', invoice_date AS 'التاريخ' FROM invoices ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(all_invoices_df, use_container_width=True)
        
    st.markdown("---")
    st.markdown("### 🗄️ سجلات جميع عمليات الجرد التي تمت مسبقاً (التقارير السابقة)")
    conn = sqlite3.connect(DB_NAME)
    archive_df = pd.read_sql_query("SELECT id AS 'رقم الجلسة', audit_date AS 'تاريخ الجرد', cost_of_sold AS 'تكلفة البضاعة المباعة', cash_counted AS 'الكاش الفعلي الموجود', period_expenses AS 'حجم المصروفات المتزامنة', net_profit AS 'صافي المكسب الفعلي الفائض' FROM audit_archive ORDER BY id DESC", conn)
    conn.close()
    
    if archive_df.empty:
        st.info("لا توجد عمليات جرد مرحلة ومؤرشفة بعد.")
    else:
        st.dataframe(archive_df, use_container_width=True)

    # 🚨 نظام تصفير قاعدة البيانات بالكامل والبدء من جديد
    st.markdown("---")
    st.markdown("### ⚙️ إدارة النظام المتقدمة")
    st.write("إذا كنت تريد مسح كل البيانات الحالية وتصفير المحل بالكامل لبدء نشاط جديد، اضغط على الزر أدناه:")
    
    # استخدام زر حماية تأكيدي لعدم المسح بالخطأ
    confirm_reset = st.checkbox("أوافق على مسح كافة الفواتير والمخزون وجلسات الجرد السابقة نهائياً ولا يمكن استرجاعها.")
    if st.button("⚠️ إعادة ضبط وتصفير قاعدة البيانات بالكامل"):
        if confirm_reset:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS inventory")
            c.execute("DROP TABLE IF EXISTS invoices")
            c.execute("DROP TABLE IF EXISTS expenses")
            c.execute("DROP TABLE IF EXISTS audit_archive")
            conn.commit()
            conn.close()
            st.success("💥 تم تصفير المخزن بالكامل ومسح جميع الجداول! يرجى تحديث الصفحة للبدء من الصفر.")
            init_database()
            st.rerun()
        else:
            st.error("الرجاء تحديد خانة الموافقة أولاً لتفعيل زر التصفير وحمايتك من المسح غير المقصود!")
