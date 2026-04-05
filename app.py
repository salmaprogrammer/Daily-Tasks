import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="مدير المهام", page_icon="✅")

# الصلاحيات المطلوبة للوصول لملفات جوجل
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# دالة الاتصال الآمنة
@st.cache_resource
def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error("فشل في تحميل بيانات الاعتماد من Secrets")
        st.stop()

# الاتصال وفتح الملف
try:
    client = get_gsheet_client()
    # تأكد أن اسم الملف في جوجل شيت هو "TaskTracker" بالضبط
    sheet = client.open("TaskTracker").sheet1
except Exception as e:
    st.error(f"خطأ: لم نتمكن من العثور على ملف Google Sheet. تأكد من تسميته 'TaskTracker' ومشاركته مع الإيميل البرمجي. التفاصيل: {e}")
    st.stop()

st.title("📝 متابعة المهام")

# --- إضافة مهمة ---
with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form"):
        task_name = st.text_input("المهمة")
        category = st.selectbox("النوع", ["يومية", "شهرية", "سنوية"])
        date = st.date_input("التاريخ")
        
        if st.form_submit_button("حفظ"):
            if task_name:
                sheet.append_row([task_name, category, str(date)])
                st.success("تم الحفظ!")
                st.rerun() # لإعادة تحديث القائمة فوراً

# --- عرض المهام ---
data = sheet.get_all_records()
if data:
    df = pd.DataFrame(data)
    st.subheader("📋 قائمة المهام")
    
    col1, col2 = st.columns(2)
    with col1:
        cat_filter = st.multiselect("تصفية", ["يومية", "شهرية", "سنوية"], default=["يومية", "شهرية", "سنوية"])
    
    filtered_df = df[df['Category'].isin(cat_filter)]
    st.table(filtered_df)
else:
    st.info("لا توجد بيانات حالياً.")
