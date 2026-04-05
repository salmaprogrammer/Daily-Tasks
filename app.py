import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="مدير المهام اليومية", page_icon="📝", layout="wide")

# الصلاحيات
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gsheet_client():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = get_gsheet_client()
    # تأكد من وضع الـ ID الخاص بملفك هنا أو اسم الملف بدقة
    sheet = client.open("TaskTracker").sheet1
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    st.stop()

st.title("📝 نظام متابعة المهام")

# --- جزء إضافة مهمة جديدة ---
with st.expander("➕ إضافة مهمة جديدة", expanded=True):
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            task_date = st.date_input("التاريخ", datetime.now())
            task_name = st.text_input("المهمة")
        with col2:
            task_status = st.selectbox("الحالة", ["لم يتم", "تم"])
            task_cat = st.selectbox("التصنيف", ["يومية", "شهرية", "سنوية"])
        
        submit = st.form_submit_button("حفظ المهمة في Google Sheet")
        
        if submit:
            if task_name:
                # الترتيب الجديد: Date, Task, Status, Category
                new_row = [str(task_date), task_name, task_status, task_cat]
                sheet.append_row(new_row)
                st.success(f"✅ تم إضافة: {task_name}")
                st.rerun()
            else:
                st.error("الرجاء كتابة اسم المهمة")

st.divider()

# --- جزء عرض ومتابعة المهام ---
st.subheader("📊 جدول المتابعة")

try:
    data = sheet.get_all_values()
    if len(data) > 1:
        # تحويل البيانات لـ DataFrame مع تسمية الأعمدة حسب طلبك
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # فلاتر سريعة في الأعلي
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            q_cat = st.multiselect("تصفية حسب النوع", ["يومية", "شهرية", "سنوية"], default=["يومية", "شهرية", "سنوية"])
        with f_col2:
            q_status = st.multiselect("تصفية حسب الحالة", ["تم", "لم يتم"], default=["تم", "لم يتم"])
        
        # تطبيق التصفية
        mask = df['Category'].isin(q_cat) & df['Status'].isin(q_status)
        filtered_df = df[mask]
        
        # عرض الجدول مع تلوين الحالات (اختياري)
        def color_status(val):
            color = '#90ee90' if val == 'تم' else '#ffcccb'
            return f'background-color: {color}'

        st.dataframe(filtered_df.style.applymap(color_status, subset=['Status']), use_container_width=True)
        
        # إحصائيات بسيطة
        total = len(filtered_df)
        completed = len(filtered_df[filtered_df['Status'] == 'تم'])
        st.info(f"إحصائيات القائمة الحالية: إجمالي {total} | منجز {completed} | متبقي {total - completed}")
        
    else:
        st.info("الشيت فارغ حالياً، قم بإضافة أول مهمة.")
except Exception as e:
    st.warning("تأكد أن الصف الأول في Google Sheet يحتوي على العناوين: Date, Task, Status, Category")
