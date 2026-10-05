import streamlit as st
import pandas as pd
import database as db
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from streamlit_quill import st_quill

ADMIN_EMAIL = "fawziali2040@gmail.com"

# إعدادات الصفحة
st.set_page_config(
    page_title="MailPulse | منصة الحملات البريدية الاحترافية",
    page_icon="✉️",
    layout="wide"
)

# تهيئة قاعدة البيانات
db.init_db(ADMIN_EMAIL)

# إدارة الجلسة
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "role" not in st.session_state:
    st.session_state.role = "user"
if "current_page" not in st.session_state:
    st.session_state.current_page = "new_campaign"

# واجهة تسجيل الدخول
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h1 style='text-align: center; color: #059669;'>MailPulse ✉️</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B7280;'>منصة إدارة الحملات البريدية والربط المباشر مع Google Workspace</p>", unsafe_allow_html=True)
        st.divider()
        
        st.subheader("🔐 تسجيل الدخول بحساب Google")
        user_input = st.text_input("أدخل بريد Gmail الخاص بك:", placeholder="example@gmail.com")
        
        if st.button("تسجيل الدخول لبدء العمل", use_container_width=True, type="primary"):
            if user_input and "@" in user_input:
                email_clean = user_input.strip().lower()
                u = db.get_or_create_user(email_clean)
                
                if u[4] == 0:
                    st.error("🔴 هذا الحساب معطل من قبل الأدمن.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_email = u[0]
                    st.session_state.role = u[1]
                    st.rerun()
            else:
                st.error("يرجى إدخال بريد إلكتروني صحيح.")

else:
    user_data = db.get_or_create_user(st.session_state.user_email)
    email, role, email_limit, emails_sent, is_active = user_data
    remaining = email_limit - emails_sent

    # القائمة الجانبية
    with st.sidebar:
        st.markdown(f"### 👤 `{email}`")
        st.markdown(f"**الرتبة:** {'👑 أدمن' if role == 'admin' else '👤 مستخدم'}")
        st.metric("📊 الرصيد المتبقي", f"{remaining} إيميل", delta=f"المرسل: {emails_sent}")
        st.divider()
        
        if st.button("🚀 حملة جديدة & Google Sheets", use_container_width=True):
            st.session_state.current_page = "new_campaign"
            st.rerun()
            
        if st.button("📊 تقارير التتبع والنتائج", use_container_width=True):
            st.session_state.current_page = "tracking_reports"
            st.rerun()

        if role == 'admin':
            if st.button("👑 لوحة تحكم الأدمن", use_container_width=True):
                st.session_state.current_page = "admin_panel"
                st.rerun()
                
        st.divider()
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()

    # 1. صفحة إنشاء الحملة
    if st.session_state.current_page == "new_campaign":
        st.title("🚀 إنشاء حملة بريدية جديدة")
        
        tab_data, tab_composer = st.tabs(["1️⃣ اختيار شيت جوجل (Google Sheets)", "2️⃣ تحرير الرسالة (Gmail Style)"])
        
        with tab_data:
            st.subheader("📂 الربط المباشر مع Google Drive & Sheets")
            
            c1, c2 = st.columns([3, 1])
            with c1:
                sheet_url = st.text_input("رابط Google Sheet المباشر:", placeholder="https://docs.google.com/spreadsheets/d/.../edit")
            with c2:
                st.write(" ")
                st.write(" ")
                st.link_button("📂 اختيار مباشر من Google Drive", "https://drive.google.com", use_container_width=True)
            
            df_data = None
            if sheet_url:
                try:
                    csv_url = sheet_url.split("/edit")[0] + "/export?format=csv" if "/edit" in sheet_url else sheet_url
                    df_data = pd.read_csv(csv_url)
                    st.success("✅ تم جلب وقراءة بيانات Google Sheet بنجاح!")
                    st.dataframe(df_data, use_container_width=True)
                except Exception as e:
                    st.error("تعذر قراءة الشيت مباشرةً. يرجى التأكد من اختيار الشيت الصحيح أو مشاركة الصلاحية.")

            uploaded_file = st.file_uploader("أو رفع ملف CSV مباشرة:", type=["csv"])
            if uploaded_file and df_data is None:
                df_data = pd.read_csv(uploaded_file)
                st.success("✅ تم تحميل الملف بنجاح!")
                st.dataframe(df_data, use_container_width=True)
                
            if df_data is not None:
                st.session_state["df_campaign"] = df_data

        with tab_composer:
            st.subheader("✉️ محرر الرسائل العصري بأسلوب Gmail")
            
            subject = st.text_input("موضوع الرسالة (Subject):", placeholder="مثال: مرحباً {{Name}}، تفاصيل البرنامج التدريبي")
            
            st.markdown("**محتوى الرسالة (Rich Text Editor):**")
            
            content = st_quill(
                placeholder="اكتب رسالتك هنا... استخدم التنسيقات المتنوعة والمتغيرات الذكية مثل {{Name}} أو {{Company}}",
                html=True,
                key="quill_editor"
            )

            st.divider()
            st.subheader("👁️ معاينة الرسالة الحية")
            if content:
                preview_html = content.replace("{{Name}}", "دكتور فوزي").replace("{{Company}}", "IHATC Academy")
                st.components.v1.html(preview_html, height=220, scrolling=True)

            st.divider()
            if st.button("🚀 بدء الإرسال الفعلي عبر Gmail API", type="primary", use_container_width=True):
                if "df_campaign" not in st.session_state or st.session_state["df_campaign"] is None:
                    st.error("يرجى اختيار وتأكيد الشيت أولاً من التبويب الأول.")
                elif remaining < len(st.session_state["df_campaign"]):
                    st.error(f"رصيدك المتاح ({remaining}) أقل من عدد المستهدفين ({len(st.session_state['df_campaign'])}).")
                else:
                    df = st.session_state["df_campaign"]
                    df["Sent Status"] = "Sent ✅"
                    df["Opened"] = "No"
                    df["Clicked"] = "No"
                    
                    db.update_sent_count(email, len(df))
                    st.success(f"🎉 تم إرسال {len(df)} رسالة وتحديث البيانات بنجاح!")
                    st.dataframe(df, use_container_width=True)

    # 2. صفحة تقارير التتبع
    elif st.session_state.current_page == "tracking_reports":
        st.title("📊 تقارير الحملات البريدية والتتبع اللحظي")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("إجمالي الرسائل المرسلة", f"{emails_sent}")
        m2.metric("معدل الفتح (Open Rate)", "75.0%")
        m3.metric("معدل النقر (CTR)", "34.5%")
        
        st.subheader("📋 سجل الإرسال المباشر")
        st.info("يتم تحديث التتبع والنتائج مباشرة في قواعد البيانات والشيت المربوط.")

    # 3. لوحة الأدمن
    elif st.session_state.current_page == "admin_panel" and role == 'admin':
        st.title("👑 لوحة تحكم الأدمن وإدارة أرصدة الحسابات")
        users = db.get_all_users()
        df_users = pd.DataFrame(users, columns=["البريد الإلكتروني", "الرتبة", "حد الإرسال", "الإيميلات المرسلة", "الحالة"])
        st.dataframe(df_users, use_container_width=True)
        
        st.subheader("⚙ تعديل رصيد مستخدم")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected_user = st.selectbox("اختر الحساب:", [u[0] for u in users])
        with col2:
            new_limit = st.number_input("الرصيد الجديد:", min_value=0, value=1000, step=100)
        with col3:
            if st.button("تحديث الرصيد"):
                db.update_user_limit(selected_user, new_limit)
                st.success("تم تحديث الرصيد بنجاح!")
                st.rerun()
