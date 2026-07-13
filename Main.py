import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# إعداد الصفحة الأساسي والمستقر سحابياً
st.set_page_config(page_title="نظام الجرد الدوري", layout="centered")

DB_FILE = "system_database.json"

# إدارة حفظ البيانات بشكل آمن لضمان عدم ضياع المدخلات
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "products": [{"كود": "101", "الاسم": "منتج تجريبي", "سعر_الشراء": 100.0, "الالكمية_قبل_الجرد": 10}],
        "cash_in": [],
        "debts": [],
        "expenses": [],
        "archive": []
    }

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_data()

db = st.session_state.db

st.title("🧮 سيستم الحسبة والجرد الدوري")

# إنشاء علامات التبويب السبعة المستقرة
tabs = st.tabs([
    "📥 الوارد التاريخي", 
    "📝 تسجيل فواتير", 
    "💵 الأموال (الكاش)", 
    "📑 الآواجل والديون", 
    "💸 المصروفات", 
    "🧮 شاشة الجرد الدوري", 
    "📊 الأرشيف والتصفير"
])

# 1. سجل الوارد التاريخي
with tabs[0]:
    st.subheader("📥 سجل البضائع والوارد التاريخي")
    df_p = pd.DataFrame(db["products"])
    st.dataframe(df_p, use_container_width=True, hide_index=True)

# 2. تسجيل المشتريات
with tabs[1]:
    st.subheader("📝 تسجيل المشتريات الجديدة")
    with st.form("p_form", clear_on_submit=True):
        p_code = st.text_input("كود المنتج")
        p_name = st.text_input("اسم المنتج")
        p_price = st.number_input("سعر الشراء الفعلي (التكلفة)", min_value=0.0, step=1.0)
        p_qty = st.number_input("الكمية الواردة", min_value=0, step=1)
        if st.form_submit_button("حفظ"):
            if p_code and p_name:
                exists = False
                for p in db["products"]:
                    if p["كود"] == p_code:
                        p["الالكمية_قبل_الجرد"] += p_qty
                        p["سعر_الشراء"] = p_price
                        p["الاسم"] = p_name
                        exists = True
                        break
                if not exists:
                    db["products"].append({"كود": p_code, "الاسم": p_name, "سعر_الشراء": p_price, "الالكمية_قبل_الجرد": p_qty})
                save_data(db)
                st.success("تم الحفظ!")
                st.rerun()

# 3. الأموال الواردة
with tabs[2]:
    st.subheader("💵 سجل المقبوضات والأموال الواردة")
    with st.form("c_form", clear_on_submit=True):
        c_amount = st.number_input("المبلغ كاش", min_value=0.0, step=1.0)
        c_note = st.text_input("البيان")
        if st.form_submit_button("تسجيل الكاش"):
            if c_amount > 0:
                db["cash_in"].append({"التاريخ": str(datetime.now().date()), "البيان": c_note, "المبلغ": c_amount})
                save_data(db)
                st.success("تم التسجيل!")
                st.rerun()
    if db["cash_in"]:
        st.dataframe(pd.DataFrame(db["cash_in"]), use_container_width=True, hide_index=True)

# 4. الآواجل والديون
with tabs[3]:
    st.subheader("📑 ديون وآواجل العملاء الخارجية")
    with st.form("d_form", clear_on_submit=True):
        d_client = st.text_input("اسم العميل")
        d_start = st.number_input("الأجل بداية الفترة", min_value=0.0, step=1.0)
        d_end = st.number_input("الأجل نهاية الفترة", min_value=0.0, step=1.0)
        if st.form_submit_button("حفظ الحساب"):
            if d_client:
                db["debts"].append({"اسم العميل": d_client, "الأجل بداية الفترة": d_start, "الأجل نهاية الفترة": d_end, "الفرق": (d_start - d_end)})
                save_data(db)
                st.success("تم الحفظ")
                st.rerun()
    if db["debts"]:
        st.dataframe(pd.DataFrame(db["debts"]), use_container_width=True, hide_index=True)

# 5. المصروفات
with tabs[4]:
    st.subheader("💸 كشف المصروفات والنثريات (منفصلة)")
    with st.form("e_form", clear_on_submit=True):
        e_amount = st.number_input("المبلغ", min_value=0.0, step=1.0)
        e_note = st.text_input("البند")
        if st.form_submit_button("تسجيل المصروف"):
            if e_amount > 0:
                db["expenses"].append({"التاريخ": str(datetime.now().date()), "بند المصروف": e_note, "القيمة": e_amount})
                save_data(db)
                st.success("تم القيد!")
                st.rerun()
    if db["expenses"]:
        st.dataframe(pd.DataFrame(db["expenses"]), use_container_width=True, hide_index=True)

# 6. شاشة الجرد الدوري والمعادلة الذكية
with tabs[5]:
    st.subheader("🧮 احتساب المكسب الفعلي الدوري")
    total_cost_of_sold = 0.0
    
    for p in db["products"]:
        st.write(f"📦 **{p['الاسم']}** | المتوفر حالياً بالنظام: {p['الالكمية_قبل_الجرد']}")
        actual_qty = st.number_input(
            f"العد الفعلي المتبقي لـ {p['الاسم']}", 
            min_value=0, 
            max_value=int(p['الالكمية_قبل_الجرد']),
            value=int(p['الالكمية_قبل_الجرد']), 
            key=f"jard_{p['كود']}"
        )
        sold_qty = p['الالكمية_قبل_الجرد'] - actual_qty
        total_cost_of_sold += (sold_qty * p['sعر_الشراء'] if 'sعر_الشراء' in p else sold_qty * p['سعر_الشراء'])

    st.markdown("---")
    total_cash = sum(item["المبلغ"] for item in db["cash_in"])
    total_debt_diff = sum(item["الفرق"] for item in db["debts"])
    total_expenses = sum(item["القيمة"] for item in db["expenses"])
    
    # حساب صافي المكسب الفعلي المعتمد على سعر الشراء
    net_profit = (total_cash + total_debt_diff) - total_cost_of_sold - total_expenses
    
    st.metric("💵 إجمالي الكاش المتوفر", f"{total_cash} ج.م")
    st.metric("📑 صافي حركة الآواجل", f"{total_debt_diff} ج.م")
    st.metric("📉 تكلفة البضاعة المباعة (سعر الشراء)", f"{total_cost_of_sold} ج.م")
    st.metric("🛑 إجمالي المصروفات (للبيان فقط)", f"{total_expenses} ج.م")
    st.markdown("---")
    st.subheader(f"🎯 صافي المكسب الفعلي النهائي: {net_profit} ج.م")

# 7. الأرشيف والتصفير الدوري
with tabs[6]:
    st.subheader("📊 أرشيف الجلسات والترحيل الشامل")
    if st.button("🚀 ترحيل هذه الفترة وتصفير البيانات لبدء جرد جديد"):
        archive_entry = {
            "رقم_الجلسة": len(db["archive"]) + 1,
            "تاريخ_الجرد": str(datetime.now().strftime("%Y-%m-%d %H:%M")),
            "الكاش": total_cash,
            "الآواجل": total_debt_diff,
            "المصروفات": total_expenses,
            "تكلفة_المباع": total_cost_of_sold,
            "صافي_المكسب": net_profit
        }
        db["archive"].append(archive_entry)
        db["cash_in"] = []
        db["debts"] = []
        db["expenses"] = []
        
        for p in db["products"]:
            actual_qty_from_state = st.session_state.get(f"jard_{p['كود']}", p['الالكمية_قبل_الجرد'])
            p['الالكمية_قبل_الجرد'] = int(actual_qty_from_state)
            
        save_data(db)
        st.success("تم التصفير والترحيل بنجاح!")
        st.rerun()
        
    if db["archive"]:
        st.dataframe(pd.DataFrame(db["archive"]), use_container_width=True, hide_index=True)
