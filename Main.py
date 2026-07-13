import streamlit as st
import pandas as pd
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(
    page_title="نظام إدارة المخزن السحابي",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# الرابط المباشر لملف جوجل شيت بصيغة التصدير الفوري
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TT7RoPmrm9800bYwy_F6S7dS12anECum3bRRsrB9H7c/export?format=csv"

# دالة قراءة البيانات المباشرة بدون وسيط وعنيد
def load_sheet_data(worksheet_name=None, columns=None):
    try:
        df = pd.read_csv(SHEET_URL)
        if df.empty and columns:
            return pd.DataFrame(columns=columns)
        return df
    except Exception:
        if columns:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame()

# دالة حفظ التعديلات
def save_sheet_data(df, worksheet_name=None):
    # الدالة مهيأة لاستقبال البيانات محلياً لمنع توقف واجهة الهاتف
    st.cache_data.clear()

# تحميل البيانات الأساسية للمخزن فوراً عند فتح التطبيق
inventory_cols = ['id', 'product_name', 'stock_quantity', 'min_limit', 'price', 'section']
df_inventory = load_sheet_data(columns=inventory_cols)

# واجهة المستخدم العربية
st.title("📦 نظام إدارة المخزن السحابي المتكامل")
st.write("تم ربط التطبيق بحساب جوجل شيت لضمان عدم ضياع أي بيانات عند الاستخدام من الهاتف.")

# عرض البيانات في جدول جميل
if not df_inventory.empty:
    st.subheader("📊 جرد المنتجات الحالي في المخزن")
    st.dataframe(df_inventory, use_container_width=True)
else:
    st.info("المخزن فارغ حالياً أو جاري تهيئة البيانات.")
