import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- 1. إعدادات الصفحة وواجهة الهاتف ---
st.set_page_config(page_title="سيستم الحسبة والجرد الدوري", layout="centered", initial_sidebar_state="collapsed")

# إجبار الواجهة على دعم القراءة من اليمين لليسار لتناسب اللغة العربية
st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 600px; padding-top: 2rem; }
    div[data-testid="stBlock"] { direction: rtl !important; text-align: right !important; }
    p, h1, h2, h3, h4, label, th, td { text-align: right !important; direction: rtl !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "system_database.json"

# --- 2. دالة إدارة الخزنة الحديدية (حفظ البيانات تلقائياً) ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "products": [{"كود": "101", "الاسم": "منتج تجريبي أ", "سعر_الشراء": 100.0, "الكمية_قبل_الجرد": 50}],
        "cash_in": [],
        "debts": [],
        "expenses": [],
        "archive": []
    }

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل البيانات في الذاكرة الحية المستقرة للتطبيق
if "db" not in st.session_state:
    st.session_state.db = load_data()

db = st.session_state.db

# --- 3. تصميم شاشات النظام السبعة ---
st.title("🧮 سيستم الحسبة والجرد الدوري الفعلي")
tabs = st.tabs([
    "📥 الوارد التاريخي", 
    "📝 تسجيل فواتير", 
    "💵 الأموال (الكاش)", 
    "📑 الآواجل والديون", 
    "💸 المصروفات", 
    "🧮 شاشة الجرد الدوري", 
    "📊 الأرشيف والتصفير"
])

# --- الشاشة 1: سجل الوارد التاريخي ---
with tabs[0]:
    st.header("📥 سجل البضائع والوارد التاريخي")
    df_prod = pd.DataFrame(db["products"])
    if not df_prod.empty:
        st.dataframe(df_prod, use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد منتجات مسجلة حالياً.")

# --- الشاشة 2: تسجيل المشتريات والمشاركة ---
with tabs[1]:
    st.header("📝 تسجيل المشتريات الجديدة")
    with st.form("prod_form", clear_on_submit=True):
        p_code = st.text_input("كود المنتج")
        p_name = st.text_input("اسم المنتج")
        p_price = st.number_input("سعر الشراء الفعلي (التكلفة)", min_value=0.0, step=1.0)
        p_qty = st.number_input("الكمية الواردة قبل الجرد", min_value=0, step=1)
        submit_p = st.form_submit_button("📥 حفظ المنتج في النظام")
        
        if submit_p and p_code and p_name:
            # تحديث الكمية إذا كان الكود موجوداً، أو إضافة منتج جديد
            exists = False
            for p in db["products"]:
                if p["كود"] == p_code:
                    p["الكمية_قبل_الجرد"] += p_qty
                    p["سعر_الشراء"] = p_price
                    p["الاسم"] = p_name
                    exists = True
                    break
            if not exists:
                db["products"].append({"كود": p_code, "الاسم": p_name, "سعر_الشراء": p_price, "الكمية_قبل_الجرد": p_qty})
            save_data(db)
            st.success(f"تم تسجيل {p_name} بنجاح!")
            
            # ميزة نص مشاركة الواتساب الجاهز
            wa_text = f"تم تسجيل فاتورة جديدة:\nالمنتج: {p_name}\nالكمية: {p_qty}\nالتكلفة: {p_price}"
            st.code(wa_text, language="text")
            st.caption("💡 يمكنك نسخ النص أعلاه ومشاركته عبر واتساب فوراً.")

# --- الشاشة 3: الأموال الواردة (الكاش) ---
with tabs[2]:
    st.header("💵 سجل المقبوضات والأموال الواردة")
    with st.form("cash_form", clear_on_submit=True):
        c_amount = st.number_input("المبلغ المقبوض كاش", min_value=0.0, step=10.0)
        c_note = st.text_input("البيان / مصدر المال (مثال: مبيعات نقدية، سداد عميل)")
        submit_c = st.form_submit_button("💰 تسجيل الكاش")
        
        if submit_c and c_amount > 0:
            db["cash_in"].append({"التاريخ": str(datetime.now().date()), "البيان": c_note, "المبلغ": c_amount})
            save_data(db)
            st.success("تم قيد الكاش في الخزينة بنجاح!")
    
    st.subheader("📊 حركات الكاش للفترة الحالية")
    if db["cash_in"]:
        st.dataframe(pd.DataFrame(db["cash_in"]), use_container_width=True, hide_index=True)

# --- الشاشة 4: الآواجل الخارجية (الديون) ---
with tabs[3]:
    st.header("📑 ديون وآواجل العملاء الخارجية")
    with st.form("debt_form", clear_on_submit=True):
        d_client = st.text_input("اسم العميل")
        d_start = st.number_input("الأجل في بداية الفترة", min_value=0.0, step=10.0)
        d_end = st.number_input("الأجل في نهاية الفترة", min_value=0.0, step=10.0)
        submit_d = st.form_submit_button("📌 حفظ حساب العميل")
        
        if submit_d and d_client:
            # فرق الآواجل = بداية الفترة - نهاية الفترة (إذا قل الدين يعني كاش دخل إليك، وإذا زاد يعني بضاعة خرجت ولم تُقبض)
            diff = d_start - d_end
            db["debts"].append({
                "اسم العميل": d_client, 
                "الأجل بداية الفترة": d_start, 
                "الأجل نهاية الفترة": d_end, 
                "الفرق": diff
            })
            save_data(db)
            st.success(f"تم تسجيل حساب {d_client}")
            
    if db["debts"]:
        st.dataframe(pd.DataFrame(db["debts"]), use_container_width=True, hide_index=True)

# --- الشاشة 5: المصروفات والنثريات ---
with tabs[4]:
    st.header("💸 كشف المصروفات والنثريات (منفصلة)")
    with st.form("exp_form", clear_on_submit=True):
        e_amount = st.number_input("قيمة المصروف المالية", min_value=0.0, step=5.0)
        e_note = st.text_input("بند المصروف (مثال: إيجار، نقل، كهرباء)")
        submit_e = st.form_submit_button("❌ تسجيل المصروف")
        
        if submit_e and e_amount > 0:
            db["expenses"].append({"التاريخ": str(datetime.now().date()), "بند المصروف": e_note, "القيمة": e_amount})
            save_data(db)
            st.success("تم تسجيل بند المصروف بنجاح!")
            
    if db["expenses"]:
        st.dataframe(pd.DataFrame(db["expenses"]), use_container_width=True, hide_index=True)

# --- الشاشة 6: شاشة الجرد الدوري (القلب النابض للحسبة) ---
with tabs[5]:
    st.header("🧮 احتساب المكسب الفعلي الدوري")
    st.write("قم بإدخال **الكمية المتبقية فعلياً في المخزن بالعد اليدوي** لكل منتج لإتمام الحسبة:")
    
    total_cost_of_sold = 0.0
    jard_entries = []
    
    # تفادي خطأ الحلقات البرمجية بجعل مدخلات العد الفعلي مستقرة وثابتة
    for idx, p in enumerate(db["products"]):
        st.subheader(f"📦 المنتج: {p['الاسم']} (كود: {p['كود']})")
        st.caption(f"الكمية المفترضة بالنظام قبل الجرد: {p['الكمية_قبل_الجرد']} | سعر الشراء للتكلفة: {p['سعر_الشراء']} ج.م")
        
        # حقل الإدخال السحري الحاسم للعد الفعلي
        actual_qty = st.number_input(
            f"أدخل الكمية الفعلية المتبقية بعد العد لـ {p['الاسم']}", 
            min_value=0, 
            max_value=int(p['الكمية_قبل_الجرد']),
            value=int(p['الكمية_قبل_الجرد']), 
            key=f"jard_{p['كود']}"
        )
        
        sold_qty = p['الكمية_قبل_الجرد'] - actual_qty
        cost_of_sold = sold_qty * p['سعر_الشراء']
        total_cost_of_sold += cost_of_sold
        
        jard_entries.append({
            "كود": p['كود'],
            "الاسم": p['الاسم'],
            "الكمية قبل الجرد": p['الكمية_قبل_الجرد'],
            "العد الفعلي المتبقي": actual_qty,
            "الكمية المباعة فعلياً": sold_qty,
            "تكلفة البضاعة المباعة": cost_of_sold
        })
    
    st.markdown("---")
    st.subheader("📊 تقرير الجرد الختامي للفترة الحالية")
    
    # حساب المجاميع المالية آلياً وبدون تأخير
    total_cash = sum(item["المبلغ"] for item in db["cash_in"])
    total_debt_diff = sum(item["الفرق"] for item in db["debts"])
    total_expenses = sum(item["القيمة"] for item in db["expenses"])
    
    # المعادلة الكبرى المصممة لك: صافي المكسب الفعلي النهائي
    # الفائض المالي (الكاش الفعلي المتوفر + فرق الآواجل) مطروحاً منه تكلفة الشراء للبضاعة المباعة والمصروفات
    net_profit = (total_cash + total_debt_diff) - total_cost_of_sold - total_expenses
    
    # عرض النتائج في بطاقات عرض واضحة وجذابة على الهاتف
    col1, col2 = st.columns(2)
    col1.metric("💵 إجمالي الكاش المتوفر", f"{total_cash} ج.م")
    col2.metric("📑 صافي حركة الديون والآواجل", f"{total_debt_diff} ج.م")
    
    col3, col4 = st.columns(2)
    col3.metric("📉 تكلفة البضاعة المباعة (بسعر الشراء)", f"{total_cost_of_sold} ج.م")
    col4.metric("🛑 إجمالي المصروفات (للإيضاح فقط)", f"{total_expenses} ج.م")
    
    st.markdown("---")
    if net_profit >= 0:
        st.success(f"🎯 **صافي المكسب الفعلي النهائي للفترة: {net_profit} ج.م**")
    else:
        st.error(f"🚨 **صافي الخسارة الفعلية للفترة: {net_profit} ج.م**")

# --- الشاشة 7: الأرشيف وتصفير الجلسات وبدء جرد جديد ---
with tabs[6]:
    st.header("📊 أرشيف الجلسات والترحيل الشامل")
    
    # زر ترحيل وتصفير الفترة لحل مشكلة بدء جرد جديد جذرياً
    if st.button("🚀 ترحيل هذه الفترة وتصفير البيانات لبدء جرد جديد"):
        session_id = len(db["archive"]) + 1
        archive_entry = {
            "رقم_الجلسة": session_id,
            "تاريخ_الجرد": str(datetime.now().strftime("%Y-%m-%d %H:%M")),
            "الكاش_الفعلي": total_cash,
            "صافي_الآواجل": total_debt_diff,
            "إجمالي_المصروفات": total_expenses,
            "تكلفة_البضاعة_المباعة": total_cost_of_sold,
            "المكسب_الفعلي_النهائي": net_profit
        }
        
        # 1. دفع البيانات للأرشيف الموثق لعدم ضياع التاريخ
        db["archive"].append(archive_entry)
        
        # 2. تصفير الكاش، الديون، المصروفات تماماً لبدء دورة نظيفة
        db["cash_in"] = []
        db["debts"] = []
        db["expenses"] = []
        
        # 3. تحديث كميات البضاعة لتصبح الكمية المفترضة القادمة هي المتبقية حالياً بعد العد
        for idx, p in enumerate(db["products"]):
            actual_qty_from_state = st.session_state.get(f"jard_{p['كود']}", p['الكمية_قبل_الجرد'])
            p['الكمية_قبل_الجرد'] = int(actual_qty_from_state)
            
        save_data(db)
        st.balloons()
        st.success("تم ترحيل الفترة الحالية للأرشيف بنجاح، وتصفير شاشات العمل لبدء فترة جرد جديدة ونظيفة كلياً!")
        st.rerun()
        
    st.markdown("---")
    st.subheader("📜 أرشيف الجلسات السابقة التاريخي")
    if db["archive"]:
        st.dataframe(pd.DataFrame(db["archive"]), use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد جلسات مؤرشفة سابقة حتى الآن.")
