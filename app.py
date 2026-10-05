import streamlit as st
import pandas as pd
import database as db
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_quill import st_quill

# مكتبات Google OAuth و Gmail API
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

ADMIN_EMAIL = "fawzy.elsayed.ihatc@gmail.com"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

# إعدادات الصفحة
st.set_page_config(
    page_title="MailPulse | منصة الحملات البريدية الاحترافية",
    page_icon="✉️",
    layout="wide"
)

# تهيئة قاعدة البيانات
db.init_db(ADMIN_EMAIL)

# إعداد OAuth Flow
def get_oauth_flow():
    client_id = st.secrets.get("google_oauth", {}).get("client_id", "758723171285-v83abei494261nbcsopqgm9omefrrm73.apps.googleusercontent.com")
    client_secret = st.secrets.get("google_oauth", {}).get("client_secret", "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")
    redirect_uri = st.secrets.get("google_oauth", {}).get("redirect_uri", "http://localhost:8501/")

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow

# دالة إرسال الإيميل المباشر عبر Gmail API مع تحديد الراسل صراحة
def send_email_via_gmail_api(credentials, to_email, subject, body_html):
    service = build('gmail', 'v1', credentials=credentials)
    
    # جلب البريد الإلكتروني للراسل (المستخدم المسجل)
    user_profile = service.users().getProfile(userId='me').execute()
    sender_email = user_profile.get('emailAddress')

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = to_email
    message['Subject'] = subject
    
    msg_text = MIMEText(body_html, 'html')
    message.attach(msg_text)
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    body = {'raw': raw_message}
    
    sent_message = service.users().messages().send(userId='me', body=body).execute()
    return sent_message

# إدارة الجلسة
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_credentials" not in st.session_state:
    st.session_state.user_credentials = None
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = "new_campaign"

# استقبال كود العودة من Google OAuth عبر URL
query_params = st.query_params
if "code" in query_params and not st.session_state.logged_in:
    code = query_params["code"]
    try:
        flow = get_oauth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # جلب بريد المستخدم المسجل
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        user_email = user_info.get("email").strip().lower()
        
        u = db.get_or_create_user(user_email)
        if u[4] == 0:
            st.error("🔴 هذا الحساب معطل من قبل الأدمن.")
        else:
            st.session_state.logged_in = True
            st.session_state.user_credentials = credentials
            st.session_state.user_email = user_email
            st.session_state.role = u[1]
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.error(f"خطأ في تسجيل الدخول عبر Google: {str(e)}")

# ----------------- الشاشة الرئيسية -----------------

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h1 style='text-align: center; color: #059669;'>MailPulse ✉️</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B7280;'>منصة إدارة الحملات البريدية والربط المباشر مع Google Workspace</p>", unsafe_allow_html=True)
        st.divider()
        
        st.subheader("🔐 تسجيل الدخول الآمن بحساب Google")
        st.info("سيمكنك تسجيل الدخول من إرسال الحملات البريدية مباشرة من حساب Gmail الخاص بك وباسمك.")
        
        try:
            flow = get_oauth_flow()
            # إجبار إظهار موافقة الصلاحيات (prompt='consent') لمنح صلاحية الإرسال الجديدة
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            st.link_button("🌐 Sign in with Google (تسجيل الدخول مع جوجل)", auth_url, type="primary", use_container_width=True)
        except Exception as ex:
            st.error("يرجى التأكد من ضبط إعدادات OAuth في Streamlit Secrets أولاً.")

else:
    user_data = db.get_or_create_user(st.session_state.user_email)
    
    email = user_data[0]
    role = user_data[1]
    email_limit = user_data[2]
    emails_sent = user_data[3]
    is_active = user_data[4]
    
    remaining = email_limit - emails_sent

    # القائمة الجانبية Sidebar
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
            st.session_state.user_credentials = None
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
            
            subject = st.text_input("موضوع الرسالة (Subject):", placeholder="مثال: مرحباً {{NAME}}، تفاصيل البرنامج التدريبي")
            
            content = st_quill(
                placeholder="اكتب رسالتك هنا... استخدم التنسيقات المتنوعة والمتغيرات الذكية مثل {{NAME}}",
                html=True,
                key="quill_editor"
            )

            st.divider()
            st.subheader("👁️ معاينة الرسالة الحية")
            if content:
                preview_html = content.replace("{{NAME}}", "دكتور فوزي")
                st.components.v1.html(preview_html, height=220, scrolling=True)

            st.divider()
            if st.button("🚀 بدء الإرسال الفعلي عبر Gmail API الخاص بـ جوجل", type="primary", use_container_width=True):
                if "df_campaign" not in st.session_state or st.session_state["df_campaign"] is None:
                    st.error("يرجى اختيار وتأكيد الشيت أولاً من التبويب الأول.")
                elif remaining < len(st.session_state["df_campaign"]):
                    st.error(f"رصيدك المتاح ({remaining}) أقل من عدد المستهدفين ({len(st.session_state['df_campaign'])}).")
                elif not st.session_state.user_credentials:
                    st.error("جلسة تسجيل الدخول انتهت، يرجى إعادة تسجيل الدخول عبر جوجل.")
                else:
                    df = st.session_state["df_campaign"]
                    sent_success = 0
                    status_list = []

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for index, row in df.iterrows():
                        recipient = row.get("NAME") or row.get("Email") or row.get("email")
                        if recipient and "@" in str(recipient):
                            try:
                                sub_personalized = subject.replace("{{NAME}}", str(recipient))
                                body_personalized = content.replace("{{NAME}}", str(recipient))
                                
                                # الإرسال الفعلي المباشر
                                send_email_via_gmail_api(
                                    st.session_state.user_credentials,
                                    str(recipient),
                                    sub_personalized,
                                    body_personalized
                                )
                                sent_success += 1
                                status_list.append("Sent ✅")
                            except Exception as ex:
                                st.error(f"خطأ أثناء الإرسال لـ {recipient}: {str(ex)}")
                                status_list.append(f"Failed ❌ ({str(ex)})")
                        else:
                            status_list.append("Failed ❌ (Invalid Email)")
                        
                        progress_bar.progress((index + 1) / len(df))
                        status_text.text(f"جاري إرسال الرسالة {index + 1} من {len(df)}...")

                    df["Sent Status"] = status_list
                    db.update_sent_count(email, sent_success)
                    st.success(f"🎉 تم إرسال {sent_success} رسالة حقيقية بنجاح مباشرة من حساب Gmail الخاص بك ({email})!")
                    st.dataframe(df, use_container_width=True)

    elif st.session_state.current_page == "tracking_reports":
        st.title("📊 تقارير الحملات البريدية والتتبع اللحظي")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("إجمالي الرسائل المرسلة", f"{emails_sent}")
        m2.metric("معدل الفتح (Open Rate)", "100%")
        m3.metric("معدل النقر (CTR)", "0%")
        
        st.subheader("📋 سجل الإرسال المباش
