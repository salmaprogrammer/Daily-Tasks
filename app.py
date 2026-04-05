import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta

# --- إعدادات الصفحة ---
st.set_page_config(page_title="مدير المهام الاحترافي", page_icon="📅", layout="wide")

# --- قائمة المهام الأساسية الثابتة ---
DEFAULT_CORE_TASKS = ["صلاة الفجر", "قراءة القرآن", "الورد اليومي", "ممارسة الرياضة"]

# --- الاتصال بـ Google Sheets ---
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error("❌ فشل في تحميل بيانات الاعتماد.")
        st.stop()

client = get_gsheet_client()
try:
    sheet = client.open("TaskTracker").sheet1
except:
    st.error("❌ لم يتم العثور على 'TaskTracker'.")
    st.stop()

# --- دالة لجلب البيانات ---
def load_data():
    raw_data = sheet.get_all_values()
    if len(raw_data) > 1:
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df['row_idx'] = range(2, len(df) + 2)
        df['Date_DT'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        return df
    return pd.DataFrame(columns=['Date', 'Task', 'Status', 'Category'])

# --- واجهة المستخدم ---
st.title("📝 نظام متابعة المهام الذكي")

# --- 1. إضافة مهمة جديدة مع خيار التكرار ---
with st.expander("➕ إضافة مهمة جديدة", expanded=False):
    with st.form("task_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2, 4, 2, 2])
        new_date = c1.date_input("التاريخ", datetime.now())
        new_task = c2.text_input("وصف المهمة")
        new_status = c3.selectbox("الحالة", ["ليس بعد", "لم يتم", "تم"])
        new_cat = c4.selectbox("التصنيف", ["يومية", "شهرية", "سنوية"])
        
        # ميزة التكرار لليوم التالي
        repeat_tomorrow = st.checkbox("🔄 تكرار هذه المهمة لليوم التالي تلقائياً؟")
        
        if st.form_submit_button("حفظ المهمة"):
            if new_task:
                # إضافة المهمة الأصلية
                sheet.append_row([str(new_date), new_task, new_status, new_cat])
                
                # إضافة نسخة لليوم التالي إذا تم تفعيل الخيار
                if repeat_tomorrow:
                    tomorrow_date = new_date + timedelta(days=1)
                    sheet.append_row([str(tomorrow_date), new_task, "ليس بعد", new_cat])
                    st.info(f"تم جدولة نسخة لليوم التالي: {tomorrow_date}")
                
                st.success("تم الحفظ بنجاح!")
                st.rerun()

st.divider()
df = load_data()

# --- 2. فلاتر العرض ---
st.sidebar.header("🔍 خيارات العرض")
view_option = st.sidebar.radio("المدى الزمني:", ["كل التواريخ", "تاريخ محدد"])
selected_date = datetime.now().date()
if view_option == "تاريخ محدد":
    selected_date = st.sidebar.date_input("اختر اليوم", datetime.now())

if not df.empty:
    mask = pd.Series([True] * len(df))
    if view_option == "تاريخ محدد":
        mask = mask & (df['Date_DT'] == selected_date)
    filtered_df = df[mask]
else:
    filtered_df = pd.DataFrame()

# --- 3. زر المهام الأساسية السريع ---
if view_option == "تاريخ محدد":
    existing = filtered_df['Task'].tolist() if not filtered_df.empty else []
    missing = [t for t in DEFAULT_CORE_TASKS if t not in existing]
    if missing:
        if st.button(f"✨ إضافة المهام الروتينية لليوم ({len(missing)})"):
            rows = [[str(selected_date), t, "ليس بعد", "يومية"] for t in missing]
            sheet.append_rows(rows)
            st.rerun()

# --- 4. عرض الجدول النهائي ---
st.subheader(f"📋 قائمة مهام: {selected_date if view_option == 'تاريخ محدد' else 'الكل'}")

if not filtered_df.empty:
    # ترتيب الحالات لسهولة التغيير
    status_order = ["ليس بعد", "لم يتم", "تم"]
    
    # رؤوس الأعمدة
    h1, h2, h3, h4, h5 = st.columns([2, 4, 2, 2, 3])
    h1.write("**التاريخ**")
    h2.write("**المهمة**")
    h3.write("**الحالة**")
    h4.write("**التصنيف**")
    h5.write("**إجراءات**")
    
    for _, row in filtered_df.iterrows():
        r1, r2, r3, r4, r5 = st.columns([2, 4, 2, 2, 3])
        r1.write(row['Date'])
        r2.write(f"**{row['Task']}**")
        
        # تنسيق لون الحالة
        current_status = row['Status']
        if current_status == "تم":
            r3.success("تم ✅")
        elif current_status == "لم يتم":
            r3.error("لم يتم ❌")
        else:
            r3.warning("ليس بعد ⏳")
            
        r4.caption(row['Category'])
        
        with r5:
            c_next, c_del = st.columns(2)
            # زر التبديل الدوري بين الحالات
            current_idx = status_order.index(current_status) if current_status in status_order else 0
            next_status = status_order[(current_idx + 1) % len(status_order)]
            
            if c_next.button(f"➔ {next_status}", key=f"nxt_{row['row_idx']}"):
                sheet.update_cell(int(row['row_idx']), 3, next_status)
                st.rerun()
            
            if c_del.button("🗑️", key=f"del_{row['row_idx']}"):
                sheet.delete_rows(int(row['row_idx']))
                st.rerun()
        st.markdown("---")
else:
    st.info("لا توجد مهام حالياً.")
