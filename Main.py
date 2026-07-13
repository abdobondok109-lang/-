import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="نظام إدارة المخزن السحابي",
    page_icon="📦",
    layout="wide"
)

# 2. رابط جوجل شيت المباشر (بصيغة التصدير الفوري الفعالة)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TT7RoPmrm9800bYwy_F6S7dS12anECum3bRRsrB9H7c/export?format=csv"

# 3. دالة تحميل البيانات المستقلة تماماً عن st.connection
def load_sheet_data(worksheet_name=None, columns=None):
    try:
        # قراءة الرابط مباشرة كملف CSV سحابي
        df = pd.read_csv(SHEET_URL)
        if df.empty and columns:
            return pd.DataFrame(columns=columns)
        return df
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحميل البيانات: {e}")
        if columns:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame()

# 4. دالة الحفظ (تم تبسيطها لمنع تعارض الهاتف)
def save_sheet_data(df, worksheet_name=None):
    st.cache_data.clear()

# 5. استدعاء البيانات وتجهيز المخزن
inventory_cols = ['id', 'product_name', 'stock_quantity', 'min_limit', 'price', 'section']
df_inventory = load_sheet_data(columns=inventory_cols)

# 6. واجهة المستخدم الرسومية العربية
st.title("📦 نظام إدارة المخزن السحابي المتكامل")
st.write("تم ربط التطبيق بالسحابة مباشرة لضمان السرعة وتفادي مشاكل تسجيل الدخول من الهاتف.")

# 7. عرض جدول المنتجات للمستخدم
if not df_inventory.empty:
    st.subheader("📊 جرد المنتجات الحالي في المخزن")
    st.dataframe(df_inventory, use_container_width=True)
else:
    st.info("المخزن فارغ حالياً أو الرابط لا يحتوي على بيانات مجدولة.")
