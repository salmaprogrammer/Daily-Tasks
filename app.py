import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta

# --- إعدادات الصفحة ---
st.set_page_config(page_title="مدير المهام الاحترافي", page_icon="📅", layout="wide")

# --- 🔒 نظام حماية الدخول ---
def check_password():
    """دالة للتحقق من كلمة المرور"""
    def password_entered():
        # يمكنك تغيير كلمة المرور من هنا (بدل '1234')
        if st.session_state["password"] == "Asd12345@":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # مسح كلمة المرور من الذاكرة للأمان
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # شاشة الدخول لأول مرة
        st.title("🔐 تسجيل الدخول")
        st.text_input("أدخل كلمة المرور للوصول للنظام", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # في حال كانت كلمة المرور خطأ
        st.title("🔐 تسجيل الدخول")
        st.text_input("كلمة المرور غير صحيحة، حاول مجدداً", type="password", on_change=password_entered, key="password")
        st.error("❌ عذراً، كلمة المرور خاطئة")
        return False
    else:
        # كلمة المرور صحيحة
        return True

# إذا فشل التحقق من كلمة المرور، توقف عن تنفيذ باقي الكود
if not check_password():
    st.stop()

# --- قائمة المهام الأساسية الثابتة ---
DEFAULT_CORE_TASKS = [
    "صلاة الفجر", "صلاة الصبح", "صلاة الضحى", "صلاة الظهر",
    "صلاة العصر", "صلاة المغرب", "صلاة العشاء", "صلاة الوتر", "قراءة القرآن"
]

# --- الاتصال بـ Google Sheets ---
scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

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
    st.error("❌ لم يتم العثور على 'TaskTracker'. تأكد من وجود الملف ومشاركته.")
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

# --- واجهة المستخدم الرئيسية (تظهر بعد الدخول) ---
st.sidebar.success("تم تسجيل الدخول بنجاح ✅")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state["password_correct"] = False
    st.rerun()

st.title("📝 نظام متابعة المهام الذكي")

# --- 1. إضافة مهمة جديدة ---
with st.expander("➕ إضافة مهمة جديدة", expanded=False):
    with st.form("task_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2, 4, 2, 2])
        new_date = c1.date_input("التاريخ", datetime.now())
        new_task = c2.text_input("وصف المهمة")
        new_status = c3.selectbox("الحالة الابتدائية", ["ليس بعد", "لم يتم", "تم"])
        new_cat = c4.selectbox("التصنيف", ["يومية", "شهرية", "سنوية"])
        
        repeat_tomorrow = st.checkbox("🔄 تكرار هذه المهمة لليوم التالي تلقائياً؟")
        
        if st.form_submit_button("حفظ المهمة"):
            if new_task:
                sheet.append_row([str(new_date), new_task, new_status, new_cat])
                if repeat_tomorrow:
                    tomorrow_date = new_date + timedelta(days=1)
                    sheet.append_row([str(tomorrow_date), new_task, "ليس بعد", new_cat])
                st.success("تم الحفظ!")
                st.rerun()

st.divider()
df = load_data()

# --- 2. خيارات العرض ---
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

# --- 3. زر المهام الأساسية ---
if view_option == "تاريخ محدد":
    existing = filtered_df['Task'].tolist() if not filtered_df.empty else []
    missing = [t for t in DEFAULT_CORE_TASKS if t not in existing]
    if missing:
        if st.button(f"✨ إضافة المهام الروتينية لليوم ({len(missing)})"):
            rows = [[str(selected_date), t, "ليس بعد", "يومية"] for t in missing]
            sheet.append_rows(rows)
            st.rerun()

# --- 4. عرض الجدول النهائي ---
st.subheader(f"📋 قائمة المهام: {selected_date if view_option == 'تاريخ محدد' else 'الكل'}")

if not filtered_df.empty:
    status_options = ["ليس بعد", "لم يتم", "تم"]
    
    h1, h2, h3, h4, h5 = st.columns([2, 4, 2, 2, 3])
    h1.write("**التاريخ**")
    h2.write("**المهمة**")
    h3.write("**الحالة الحالية**")
    h4.write("**التصنيف**")
    h5.write("**تعديل الحالة / إجراء**")
    st.markdown("---")
    
    for _, row in filtered_df.iterrows():
        r1, r2, r3, r4, r5 = st.columns([2, 4, 2, 2, 3])
        r1.write(row['Date'])
        r2.write(f"**{row['Task']}**")
        
        curr_status = row['Status']
        if curr_status == "تم":
            r3.success("تم ✅")
        elif curr_status == "لم يتم":
            r3.error("لم يتم ❌")
        else:
            r3.warning("ليس بعد ⏳")
            
        r4.caption(row['Category'])
        
        with r5:
            col_sel, col_del = st.columns([3, 1])
            try:
                curr_index = status_options.index(curr_status)
            except:
                curr_index = 0

            chosen_status = col_sel.selectbox(
                "تغيير إلى:", 
                status_options, 
                index=curr_index, 
                key=f"sel_{row['row_idx']}",
                label_visibility="collapsed"
            )
            
            if chosen_status != curr_status:
                sheet.update_cell(int(row['row_idx']), 3, chosen_status)
                st.rerun()
            
            if col_del.button("🗑️", key=f"del_{row['row_idx']}"):
                sheet.delete_rows(int(row['row_idx']))
                st.rerun()
        
        st.markdown("<hr style='margin:0; padding:0; opacity:0.1'>", unsafe_allow_html=True)
else:
    st.info("لا توجد مهام معروضة حالياً.")
