import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="مدير المهام الذكي", page_icon="📅", layout="wide")

# --- الاتصال بـ Google Sheets ---
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error("❌ فشل في تحميل بيانات الاعتماد من Secrets.")
        st.stop()

client = get_gsheet_client()

try:
    sheet = client.open("TaskTracker").sheet1
except Exception as e:
    st.error(f"❌ لم يتم العثور على ملف باسم 'TaskTracker'.")
    st.stop()

# --- دالة لجلب البيانات وتجهيزها ---
def load_data():
    raw_data = sheet.get_all_values()
    if len(raw_data) > 1:
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df['row_idx'] = range(2, len(df) + 2)
        # تحويل عمود التاريخ لنوع تاريخ فعلي لتسهيل المقارنة
        df['Date_DT'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=['Date', 'Task', 'Status', 'Category'])

# --- واجهة المستخدم ---
st.title("📝 نظام متابعة المهام المتطور")

# --- 1. قسم إضافة مهمة جديدة ---
with st.expander("➕ إضافة مهمة جديدة", expanded=False):
    with st.form("task_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
        with col1:
            new_date = st.date_input("التاريخ", datetime.now())
        with col2:
            new_task = st.text_input("وصف المهمة")
        with col3:
            new_status = st.selectbox("الحالة", ["لم يتم", "تم"])
        with col4:
            new_cat = st.selectbox("التصنيف", ["يومية", "شهرية", "سنوية"])
        
        submit = st.form_submit_button("حفظ المهمة")
        
        if submit:
            if new_task:
                sheet.append_row([str(new_date), new_task, new_status, new_cat])
                st.success(f"✅ تم إضافة: {new_task}")
                st.rerun()

st.divider()

# --- 2. عرض البيانات والتحكم بها ---
df = load_data()

if not df.empty:
    # --- فلاتر القائمة الجانبية ---
    st.sidebar.header("🔍 خيارات العرض")
    
    # فلتر التاريخ الجديد
    view_option = st.sidebar.radio("عرض المهام لـ:", ["كل التواريخ", "تاريخ محدد"])
    
    selected_date = None
    if view_option == "تاريخ محدد":
        selected_date = st.sidebar.date_input("اختر التاريخ المطلوب", datetime.now())

    # الفلاتر الإضافية
    filter_cat = st.sidebar.multiselect("التصنيف", options=df['Category'].unique(), default=df['Category'].unique())
    filter_stat = st.sidebar.multiselect("الحالة", options=df['Status'].unique(), default=df['Status'].unique())

    # --- تطبيق التصفية ---
    mask = df['Category'].isin(filter_cat) & df['Status'].isin(filter_stat)
    
    if view_option == "تاريخ محدد":
        mask = mask & (df['Date_DT'] == selected_date)
    
    filtered_df = df[mask]

    # --- الإحصائيات ---
    c1, c2, c3 = st.columns(3)
    c1.metric("المهام المعروضة", len(filtered_df))
    c2.metric("منجزة ✅", len(filtered_df[filtered_df['Status'] == 'تم']))
    c3.metric("متبقية ⏳", len(filtered_df[filtered_df['Status'] == 'لم يتم']))

    st.subheader(f"📋 قائمة المهام ({'الكل' if not selected_date else selected_date})")
    
    if filtered_df.empty:
        st.warning("تعذر العثور على مهام لهذا التاريخ أو بهذه الفلاتر.")
    else:
        # عرض المهام
        h1, h2, h3, h4, h5 = st.columns([2, 4, 2, 2, 3])
        h1.write("**التاريخ**")
        h2.write("**المهمة**")
        h3.write("**الحالة**")
        h4.write("**التصنيف**")
        h5.write("**إجراءات**")
        st.markdown("---")

        for index, row in filtered_df.iterrows():
            r1, r2, r3, r4, r5 = st.columns([2, 4, 2, 2, 3])
            r1.write(row['Date'])
            r2.write(f"**{row['Task']}**")
            
            if row['Status'] == "تم":
                r3.success("تم")
            else:
                r3.error("لم يتم")
                
            r4.caption(row['Category'])
            
            with r5:
                btn_col1, btn_col2 = st.columns(2)
                toggle_label = "↩️" if row['Status'] == "تم" else "✅"
                if btn_col1.button(toggle_label, key=f"tgl_{row['row_idx']}"):
                    new_stat = "لم يتم" if row['Status'] == "تم" else "تم"
                    sheet.update_cell(int(row['row_idx']), 3, new_stat)
                    st.rerun()
                
                if btn_col2.button("🗑️", key=f"del_{row['row_idx']}"):
                    sheet.delete_rows(int(row['row_idx']))
                    st.rerun()
            st.markdown("<hr style='margin:0; padding:0; opacity:0.1'>", unsafe_allow_html=True)

else:
    st.info("💡 القائمة فارغة حالياً.")
