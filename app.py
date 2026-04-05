import streamlit as st
from gspread_streamlit import gspread_connect
import pandas as pd
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Task Tracker", page_icon="✅")

# الاتصال بـ Google Sheets باستخدام Secrets
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # سيتم جلب بيانات الـ JSON من إعدادات Streamlit Cloud لاحقاً
    client = gspread_connect(st.secrets["gcp_service_account"])
    sheet = client.open("TaskTracker").sheet1
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    st.stop()

# عنوان التطبيق
st.title("📝 مدير المهام الذكي")
st.markdown("متابعة المهام اليومية، الشهرية، والسنوية")

# --- إضافة مهمة جديدة ---
with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form", clear_on_submit=True):
        task_name = st.text_input("اسم المهمة")
        category = st.selectbox("التصنيف", ["يومية", "شهرية", "سنوية"])
        date = st.date_input("التاريخ", datetime.now())
        
        submit_button = st.form_submit_button("حفظ المهمة")
        
        if submit_button:
            if task_name:
                sheet.append_row([task_name, category, str(date)])
                st.success("تم حفظ المهمة بنجاح!")
            else:
                st.warning("يرجى إدخال اسم المهمة")

# --- عرض البيانات ---
st.divider()
st.subheader("📋 قائمة المهام المسجلة")

# جلب البيانات وتحويلها لـ DataFrame
data = sheet.get_all_records()
if data:
    df = pd.DataFrame(data)
    
    # فلاتر العرض
    filter_cat = st.multiselect("تصفية حسب التصنيف", ["يومية", "شهرية", "سنوية"], default=["يومية", "شهرية", "سنوية"])
    filtered_df = df[df['Category'].isin(filter_cat)]
    
    st.dataframe(filtered_df, use_container_width=True)
    
    # إحصائيات سريعة
    st.sidebar.metric("إجمالي المهام", len(df))
    st.sidebar.metric("مهام اليوم", len(df[df['Category'] == "يومية"]))
else:
    st.info("لا توجد مهام مضافة بعد.")
