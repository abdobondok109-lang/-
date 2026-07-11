import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# 1. إعدادات الواجهة الاحترافية والدعم الكامل للغة العربية (RTL)
st.set_page_config(page_title="تطبيق المخزن السحابي", layout="wide")

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

st.title("📦 نظام إدارة المخزن السحابي المتكامل")
st.write("تم ربط هذا التطبيق بحساب جوجل شيت لضمان عدم ضياع أي بيانات عند الاستخدام من الهاتف.")

# إنشاء الاتصال بجوجل شيت
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("⚠️ يرجى ضبط إعدادات الاتصال بجوجل شيت (Secrets) في لوحة تحكم Streamlit Cloud ليتمكن التطبيق من حفظ البيانات.")
    st.stop()

# دالة مساعدة لقراءة الجداول من جوجل شيت بـ تنظيف البيانات
def load_sheet_data(worksheet_name, columns):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df
    except:
        return pd.DataFrame(columns=columns)

# دالة مساعدة لتحديث الجداول في جوجل شيت
def save_sheet_data(df, worksheet_name):
    conn.update(worksheet=worksheet_name, data=df)
    st.cache_data.clear()

# تحميل البيانات سحابياً من جوجل شيت فوراً عند فتح التطبيق
inventory_cols = ['id', 'product_name', 'stock_qty', 'cost_price']
invoices_cols = ['invoice_num', 'product_name', 'qty_added', 'cost_price', 'total_cost', 'invoice_date']
funds_cols = ['id', 'amount', 'source_details', 'fund_date']
credits_cols = ['id', 'customer_name', 'initial_credit', 'final_credit', 'record_date']
expenses_cols = ['id', 'amount', 'notes', 'expense_date']
archive_cols = ['id', 'audit_date', 'cost_of_sold', 'cash_counted', 'credit_diff', 'period_expenses', 'net_profit', 'log_details']

inventory_df = load_sheet_data("inventory", inventory_cols)
invoices_df = load_sheet_data("invoices", invoices_cols)
funds_df = load_sheet_data("incoming_funds", funds_cols)
credits_df = load_sheet_data("credit_accounts", credits_cols)
expenses_df = load_sheet_data("expenses", expenses_cols)
archive_df = load_sheet_data("audit_archive", archive_cols)

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
    st.subheader("📋 كشف الوارد التاريخي الشامل من السحابة")
    if invoices_df.empty:
        st.info("لا توجد أي فواتير واردة مسجلة حالياً.")
    else:
        st.dataframe(invoices_df, use_container_width=True)

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
            st.dataframe(df_temp, use_container_width=True)
            
            if st.button("💾 حفظ الفاتورة نهائياً على جوجل شيت وتحديث المخزن"):
                # تحديث جدول الفواتير
                new_invoices = pd.DataFrame(st.session_state.invoice_items)
                updated_invoices = pd.concat([invoices_df, new_invoices], ignore_index=True)
                save_sheet_data(updated_invoices, "invoices")
                
                # تحديث المخزن الحالي
                for item in st.session_state.invoice_items:
                    idx_match = inventory_df[inventory_df['product_name'] == item['product_name']].index
                    if not idx_match.empty:
                        inventory_df.at[idx_match[0], 'stock_qty'] = int(inventory_df.at[idx_match[0], 'stock_qty']) + int(item['qty'])
                        inventory_df.at[idx_match[0], 'cost_price'] = item['cost']
                    else:
                        new_id = len(inventory_df) + 1
                        new_row = pd.DataFrame([{"id": new_id, "product_name": item['product_name'], "stock_qty": item['qty'], "cost_price": item['cost']}])
                        inventory_df = pd.concat([inventory_df, new_row], ignore_index=True)
                        
                save_sheet_data(inventory_df, "inventory")
                st.session_state.last_saved_invoice = st.session_state.invoice_items.copy()
                st.session_state.invoice_items = []
                st.success("🎯 تم الحفظ السحابي بنجاح وتحديث المخزن!")
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
    st.subheader("💵 سجل المبالغ والأموال الواردة السحابي")
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        f_amount = st.number_input("قيمة المبلغ التوريدي (ج.م)", min_value=0.0, step=50.0)
        f_source = st.text_input("البيان / مصدر التوريد")
        f_date = st.date_input("تاريخ ورود المبلغ").strftime("%Y-%m-%d")
        if st.button("تسجيل وتجميع المبلغ في السحابة"):
            if f_amount > 0:
                new_id = len(funds_df) + 1
                new_fund = pd.DataFrame([{"id": new_id, "amount": f_amount, "source_details": f_source, "fund_date": f_date}])
                funds_df = pd.concat([funds_df, new_fund], ignore_index=True)
                save_sheet_data(funds_df, "incoming_funds")
                st.success("تم قيد المبلغ سحابياً بنجاح.")
                st.rerun()
    with col_f2:
        total_incoming_cash = pd.to_numeric(funds_df['amount']).sum() if not funds_df.empty else 0.0
        st.markdown(f"### 💰 إجمالي الكاش الفعلي المتجمع حالياً: `{total_incoming_cash:,.2f} ج.م`")
        st.dataframe(funds_df, use_container_width=True)

# ==================== 4️⃣ صفحة الآواجل الخارجية ====================
with tabs[3]:
    st.subheader("📑 حساب الآواجل الخارجية والديون المستحقة عند العملاء")
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        c_name = st.text_input("اسم العميل أو الحساب").strip()
        c_init = st.number_input("الآجل في بداية فترة العمل (ج.م)", min_value=0.0, step=50.0)
        c_final = st.number_input("الآجل في نهاية فترة العمل (ج.م)", min_value=0.0, step=50.0)
        c_date = st.date_input("التاريخ المسجل لحساب العميل").strftime("%Y-%m-%d")
        if st.button("حفظ حساب العميل سحابياً"):
            if c_name:
                new_id = len(credits_df) + 1
                new_credit = pd.DataFrame([{"id": new_id, "customer_name": c_name, "initial_credit": c_init, "final_credit": c_final, "record_date": c_date}])
                credits_df = pd.concat([credits_df, new_credit], ignore_index=True)
                save_sheet_data(credits_df, "credit_accounts")
                st.success("تم قيد بيانات العميل سحابياً.")
                st.rerun()
    with col_c2:
        t_init_c = pd.to_numeric(credits_df['initial_credit']).sum() if not credits_df.empty else 0.0
        t_final_c = pd.to_numeric(credits_df['final_credit']).sum() if not credits_df.empty else 0.0
        net_credit_diff = t_init_c - t_final_c
        st.markdown(f"📊 آجل البداية: `{t_init_c:,.2f}` | آجل النهاية: `{t_final_c:,.2f}`")
        st.markdown(f"➡️ **صافي فارق الآواجل لعملية الجرد:** `{net_credit_diff:,.2f} ج.م`")
        st.dataframe(credits_df, use_container_width=True)

# ==================== 5️⃣ كشف المسحوبات والمصروفات ====================
with tabs[4]:
    st.subheader("💸 إدارة النفقات والمصروفات النقدية")
    col_exp1, col_exp2 = st.columns([1, 2])
    with col_exp1:
        exp_amount = st.number_input("قيمة مبلغ المصروف (ج.م)", min_value=0.0, step=10.0)
        exp_notes = st.text_input("سبب الصرف / البيان")
        exp_date = st.date_input("تاريخ الصرف الحركي").strftime("%Y-%m-%d")
        if st.button("قيد بند المصروف سحابياً"):
            if exp_amount > 0:
                new_id = len(expenses_df) + 1
                new_exp = pd.DataFrame([{"id": new_id, "amount": exp_amount, "notes": exp_notes, "expense_date": exp_date}])
                expenses_df = pd.concat([expenses_df, new_exp], ignore_index=True)
                save_sheet_data(expenses_df, "expenses")
                st.success("تم قيد المصروف في حساب جوجل.")
                st.rerun()
    with col_exp2:
        total_exp = pd.to_numeric(expenses_df['amount']).sum() if not expenses_df.empty else 0.0
        st.markdown(f"### إجمالي النفقات الجارية الحالية: `{total_exp:,.2f} ج.م`")
        st.dataframe(expenses_df, use_container_width=True)

# ==================== 6️⃣ صفحة الجرد المستقلة الدورية ====================
with tabs[5]:
    st.subheader("🧮 شاشة معالجة الجرد الختامي الدوري واحتساب الأرباح الحقيقية")
    total_cash_auto = pd.to_numeric(funds_df['amount']).sum() if not funds_df.empty else 0.0
    t_init_c = pd.to_numeric(credits_df['initial_credit']).sum() if not credits_df.empty else 0.0
    t_final_c = pd.to_numeric(credits_df['final_credit']).sum() if not credits_df.empty else 0.0
    net_credit_diff = t_init_c - t_final_c
    total_exp_current = pd.to_numeric(expenses_df['amount']).sum() if not expenses_df.empty else 0.0
    
    st.info(f"💡 المحاسب السحابي سحب المخرجات: الكاش الفعلي المتجمع = {total_cash_auto:,.2f} ج.م | فارق الآواجل = {net_credit_diff:,.2f} ج.م")
    
    if inventory_df.empty:
        st.warning("المخزن فارغ حالياً، يرجى تسجيل فواتير واردة أولاً.")
    else:
        if "audit_df_v5" not in st.session_state or len(st.session_state.audit_df_v5) != len(inventory_df):
            inventory_df['الكمية المتبقية (العد الفعلي)'] = inventory_df['stock_qty'].astype(int)
            st.session_state.audit_df_v5 = inventory_df.copy()
            
        editable_table = st.data_editor(
            st.session_state.audit_df_v5[['id', 'product_name', 'stock_qty', 'cost_price', 'الكمية المتبقية (العد الفعلي)']],
            use_container_width=True, disabled=['id', 'product_name', 'stock_qty', 'cost_price']
        )
        
        if st.button("📊 معالجة واستخراج تقرير حجم المكسب الفعلي الحقيقي"):
            total_cost_sold = 0.0
            log_lines = []
            for idx, row in editable_table.iterrows():
                qty_sold = int(row['stock_qty']) - int(row['الكمية المتبقية (العد الفعلي)'])
                item_cost_sold = qty_sold * float(row['cost_price'])
                total_cost_sold += item_cost_sold
                log_lines.append(f"صنف: {row['product_name']} | المباع: {qty_sold} | تكلفة الشراء: {item_cost_sold}")
                
            final_real_profit = total_cash_auto + net_credit_diff - total_cost_sold
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.markdown(f"""
                <div class="report-card">
                    <h3>🏆 تقرير الأرباح وحجم المكسب الفعلي الحقيقي</h3>
                    <p>🔹 إجمالي الكاش السحابي المتجمع: <b>{total_cash_auto:,.2f} ج.م</b></p>
                    <p>🔹 صافي فارق حساب الآواجل: <b>{net_credit_diff:,.2f} ج.م</b></p>
                    <p>🔹 تكلفة الشراء للبضاعة المباعة: <b>{total_cost_sold:,.2f} ج.م</b></p>
                    <hr>
                    <h4>💵 حجم المكسب الفعلي النهائي: {final_real_profit:,.2f} ج.م</h4>
                </div>
                """, unsafe_allow_html=True)
            with col_res2:
                st.markdown(f"""
                <div class="expense-card">
                    <h3>⚠️ حجم المصروفات المسجلة</h3>
                    <p>📍 إجمالي مصروفات الفترة الجارية: <b>{total_exp_current:,.2f} ج.م</b></p>
                </div>
                """, unsafe_allow_html=True)
                
            st.session_state.pending_audit_v5 = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "cost_sold": total_cost_sold,
                "cash": total_cash_auto, "credit_diff": net_credit_diff, "expenses": total_exp_current,
                "net": final_real_profit, "log": "\n".join(log_lines), "table": editable_table
            }
            
        if "pending_audit_v5" in st.session_state:
            if st.button("💾 ترحيل واعتماد الجلسة (تصفير الأرصدة في جوجل شيت لبدء فترة جديدة)"):
                pa = st.session_state.pending_audit_v5
                
                # إضافة لأرشيف الجرد
                new_arch_id = len(archive_df) + 1
                new_archive_row = pd.DataFrame([{
                    "id": new_arch_id, "audit_date": pa['date'], "cost_of_sold": pa['cost_sold'],
                    "cash_counted": pa['cash'], "credit_diff": pa['credit_diff'], "period_expenses": pa['expenses'],
                    "net_profit": pa['net'], "log_details": pa['log']
                }])
                archive_df = pd.concat([archive_df, new_archive_row], ignore_index=True)
                save_sheet_data(archive_df, "audit_archive")
                
                # تحديث كميات الرفوف بالمخزن
                for _, r in pa['table'].iterrows():
                    idx_match = inventory_df[inventory_df['id'] == r['id']].index
                    if not idx_match.empty:
                        inventory_df.at[idx_match[0], 'stock_qty'] = r['الكمية المتبقية (العد الفعلي)']
                save_sheet_data(inventory_df, "inventory")
                
                # تصفير الجداول المؤقتة للفترة الجديدة في جوجل شيت
                save_sheet_data(pd.DataFrame(columns=funds_cols), "incoming_funds")
                save_sheet_data(pd.DataFrame(columns=credits_cols), "credit_accounts")
                save_sheet_data(pd.DataFrame(columns=expenses_cols), "expenses")
                
                del st.session_state.pending_audit_v5
                st.success("🎯 تم الاعتماد والترحيل السحابي وتصفير الدورة بنجاح!")
                st.rerun()

# ==================== 7️⃣ صفحة تقارير المخزن والجرد المسبق ====================
with tabs[6]:
    st.subheader("📊 إدارة المخزون المتقدمة وسجلات الجرد السابقة")
    st.markdown("### 📦 تعديل أسعار وكميات بضاعة المستودع الحالية مباشرة")
    
    if not inventory_df.empty:
        edited_stock_table = st.data_editor(inventory_df, use_container_width=True, disabled=['id', 'product_name'])
        if st.button("💾 حفظ تعديلات المخزن سحابياً فوراً"):
            save_sheet_data(edited_stock_table, "inventory")
            st.success("🎯 تم التعديل في جوجل شيت بنجاح!")
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 🗄️ سجلات جميع عمليات الجرد والتقارير المعتمدة السابقة")
    st.dataframe(archive_df, use_container_width=True)

    # التصفير العام للحماية
    st.markdown("---")
    st.markdown("### ⚙️ إدارة النظام المتقدمة")
    confirm_reset = st.checkbox("أوافق على تصفير ومسح كافة البيانات من جوجل شيت والبدء من الصفر.")
    if st.button("⚠️ تصفير قاعدة البيانات بالكامل"):
        if confirm_reset:
            save_sheet_data(pd.DataFrame(columns=inventory_cols), "inventory")
            save_sheet_data(pd.DataFrame(columns=invoices_cols), "invoices")
            save_sheet_data(pd.DataFrame(columns=funds_cols), "incoming_funds")
            save_sheet_data(pd.DataFrame(columns=credits_cols), "credit_accounts")
            save_sheet_data(pd.DataFrame(columns=expenses_cols), "expenses")
            save_sheet_data(pd.DataFrame(columns=archive_cols), "audit_archive")
            st.success("💥 تم تصفير كافة الجداول في جوجل شيت بنجاح!")
            st.rerun()
