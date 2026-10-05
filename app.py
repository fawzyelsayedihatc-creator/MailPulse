import streamlit as st
import pandas as pd
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import googleapiclient.discovery
from email.mime.text import MIMEText
import base64

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتنسيق الرئيسي
# ---------------------------------------------------------
st.set_page_config(page_title="MailPulse", page_icon="✉️", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 36px; font-weight: bold; color: #008080; text-align: center; }
    .sub-title { font-size: 18px; color: #555; text-align: center; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>MailPulse ✉️</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>منصة إدارة الحملات البريدية والربط المباشر مع Google Workspace</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. إعدادات OAuth والنطاقات المطلوبة
# ---------------------------------------------------------
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.send",
]

def get_oauth_flow():
    """توليد كائن OAuth Flow من Secrets"""
    client_config = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    redirect_uri = st.secrets["google_oauth"]["redirect_uri"]
    
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

def handle_login():
    """إدارة عملية تسجيل الدخول وتخزين الجلسة"""
    query_params = st.query_params
    
    # إذا كانت بيانات الاعتماد محفوظة سابقاً في الـ Session
    if "credentials" in st.session_state:
        return True

    # التعامل مع الكود القادم من إعادة توجيه جوجل
    if "code" in query_params:
        auth_code = query_params["code"]
        
        if "oauth_flow" in st.session_state:
            flow = st.session_state["oauth_flow"]
        else:
            flow = get_oauth_flow()
            flow.code_verifier = None  # تعطيل PKCE لمنع خطأ missing code verifier

        try:
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            # حفظ التوكن في Session State لثبات الجلسة
            st.session_state["credentials"] = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes
            }
            
            # الحصول على البريد الإلكتروني للمستخدم
            user_info_service = googleapiclient.discovery.build('oauth2', 'v2', credentials=credentials)
            user_info = user_info_service.userinfo().get().execute()
            st.session_state["user_email"] = user_info.get("email", "المستخدم")

            st.query_params.clear()
            st.rerun()
            return True
        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة تسجيل الدخول: {e}")
            st.query_params.clear()
            return False

    return False

# ---------------------------------------------------------
# 3. دالة إرسال البريد الإلكتروني عبر Gmail API
# ---------------------------------------------------------
def send_email_via_gmail(creds, to_email, subject, body_html):
    try:
        service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)
        message = MIMEText(body_html, 'html')
        message['to'] = to_email
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        return True, None
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------
# 4. واجهة التطبيق والتحكم
# ---------------------------------------------------------
is_logged_in = handle_login()

if is_logged_in:
    creds = Credentials(**st.session_state["credentials"])
    user_email = st.session_state.get("user_email", "المستخدم")

    # شريط علوي للمستخدم
    col1, col2 = st.columns([4, 1])
    with col1:
        st.success(f"مرحباً بك يا دكتور! متصل حالياً بالحساب: **{user_email}**")
    with col2:
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            del st.session_state["credentials"]
            if "user_email" in st.session_state:
                del st.session_state["user_email"]
            st.rerun()

    st.markdown("---")

    # نموذج إنشاء وإرسال الحملة
    st.subheader("📊 إنشاء حملة بريدية جديدة")

    uploaded_file = st.file_uploader("رفع قائمة المستلمين (ملف Excel أو CSV):", type=["csv", "xlsx"])
    
    col_sub, col_name = st.columns(2)
    with col_sub:
        subject = st.text_input("موضوع البريد الإلكتروني:")
    with col_name:
        sender_title = st.text_input("اسم المرسل الظاهر:", value="MailPulse Team")

    body_content = st.text_area("محتوى الرسالة (يدعم تنسيق HTML):", height=200, value="<p>مرحباً بك،</p><p>هذه رسالة تجريبية من منصة MailPulse.</p>")

    if st.button("🚀 إرسال الحملة الآن", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("يرجى رفع ملف القائمة البريدية أولاً.")
        elif not subject:
            st.error("يرجى كتابة موضوع البريد الإلكتروني.")
        else:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                # البحث عن عمود البريد الإلكتروني
                email_col = None
                for col in df.columns:
                    if 'email' in col.lower() or 'بريد' in col.lower() or 'الايميل' in col.lower():
                        email_col = col
                        break

                if not email_col:
                    st.error("لم يتم العثور على عمود يحتوي على البريد الإلكتروني (مثل Email أو البريد) في الملف.")
                else:
                    recipients = df[email_col].dropna().unique()
                    st.info(f"جاري إرسال الحملة إلى {len(recipients)} مستلم...")
                    
                    progress_bar = st.progress(0)
                    success_count = 0
                    fail_count = 0

                    for idx, email in enumerate(recipients):
                        success, err = send_email_via_gmail(creds, email, subject, body_content)
                        if success:
                            success_count += 1
                        else:
                            fail_count += 1
                        progress_bar.progress((idx + 1) / len(recipients))

                    st.balloons()
                    st.success(f"اكتملت العملية! تم الإرسال بنجاح إلى {success_count} مستلم. (فشل: {fail_count})")

            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

else:
    st.warning("يرجى تسجيل الدخول باستخدام حساب Google المعتمد للبدء.")
    
    if st.button("🔑 تسجيل الدخول عبر Google", type="primary", use_container_width=True):
        flow = get_oauth_flow()
        auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
        st.session_state["oauth_flow"] = flow
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
        st.link_button("اضغط هنا إذا لم يتم تحويلك تلقائياً", auth_url)
