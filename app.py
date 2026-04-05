import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import os

# --- إعدادات الصفحة ---
st.set_page_config(page_title="مخطط المهام الذكي", page_icon="🎯", layout="wide")

# استايل CSS بسيط لتحسين المظهر
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stCheckbox { font-size: 20px; padding: 10px; border-radius: 10px; background: white; margin-bottom: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    creds_path = os.path.join(current_dir, 'credentials.json')
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    return client.open("Daily_Tasks").sheet1

sheet = init_connection()

def get_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
    return df

# --- واجهة المستخدم الرئيسية ---
st.title("☀️ مخطط يومي ذكي")
st.subheader(f"اليوم: {datetime.now().strftime('%A, %d %B %Y')}")

# --- قسم إضافة مهمة جديدة (في صدر الصفحة) ---
with st.container():
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_task = st.text_input("", placeholder="اكتب مهمة جديدة هنا...", label_visibility="collapsed")
    with col_btn:
        if st.button("➕ إضافة المهمة", use_container_width=True):
            if new_task:
                today = datetime.now().strftime("%Y-%m-%d")
                sheet.append_row([today, new_task, "FALSE"])
                st.toast("تمت إضافة المهمة بنجاح!", icon='✅')
                st.rerun()

st.divider()

# جلب البيانات
df = get_data()

# --- تقسيم الصفحة لمتابعة المهام ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### 📝 مهام اليوم")
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_tasks = df[df['Date'].dt.strftime("%Y-%m-%d") == today_str] if not df.empty else pd.DataFrame()

    if not today_tasks.empty:
        for index, row in today_tasks.iterrows():
            current_status = str(row['Status']).upper() == "TRUE"
            # عرض المهمة مع Checkbox
            checked = st.checkbox(row['Task'], value=current_status, key=f"task_{index}")
            
            if checked != current_status:
                # تحديث الحالة في جوجل شيت فوراً
                real_row_in_sheet = index + 2
                sheet.update_cell(real_row_in_sheet, 3, str(checked).upper())
                st.rerun()
    else:
        st.info("قائمتك فارغة لليوم. ابدأ بإضافة مهامك!")

with col_right:
    st.markdown("### 📊 ملخص الأداء")
    if not df.empty:
        # إحصائية سريعة للأسبوع
        last_7_days = datetime.now() - timedelta(days=7)
        weekly_df = df[df['Date'] >= last_7_days]
        
        done = (weekly_df['Status'].astype(str).str.upper() == "TRUE").sum()
        total = len(weekly_df)
        
        st.metric("مهام مكتملة (هذا الأسبوع)", f"{done} من {total}")
        
        progress = (done / total) if total > 0 else 0
        st.progress(progress)
        
        if progress == 1:
            st.balloons()
            st.success("عمل رائع! أنجزت كل مهام الأسبوع!")
    
    st.markdown("---")
    st.markdown("### 📅 نظرة على الأيام السابقة")
    if not df.empty:
        # عرض آخر 5 مهام تمت إضافتها تاريخياً
        history = df.sort_values(by='Date', ascending=False).head(5)
        for _, h_row in history.iterrows():
            status_icon = "✅" if str(h_row['Status']).upper() == "TRUE" else "⏳"
            st.caption(f"{status_icon} {h_row['Date'].strftime('%d/%m')} - {h_row['Task']}")