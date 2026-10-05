import os
import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# إعدادات الصفحة
st.set_page_config(page_title="MailPulse", page_icon="✉️", layout="wide")

# نطاقات الصلاحيات المطلوبة (تأكد من اختيار الأساسيات فقط)
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly"
]

def get_oauth_flow():
    """إنشاء تدفق OAuth باستخدام البيانات المسجلة في Secrets"""
    oauth_secrets = st.secrets.get("google_oauth", {})
    
    # التأكد من وجود البيانات الأساسية
    client_id = oauth_secrets.get("client_id")
    client_secret = oauth_secrets.get("client_secret")
    redirect_uri = oauth_secrets.get("redirect_uri")

    if not client_id or not client_secret or not redirect_uri:
        st.error("⚠️ بيانات google_oauth مفقودة في st.secrets! يرجى مراجعة الإعدادات.")
        st.stop()

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [redirect_uri]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow

# عنوان التطبيق
st.title("✉️ تطبيق MailPulse")

# إدارة الجلسة (Session State)
if "credentials" not in st.session_state:
    st.session_state.credentials = None

# التقاط كود التحقق من الـ URL بعد توثيق المستخدم
query_params = st.query_params
if "code" in query_params and st.session_state.credentials is None:
    code = query_params["code"]
    try:
        flow = get_oauth_flow()
        flow.fetch_token(code=code)
        st.session_state.credentials = flow.credentials
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"حدث خطأ أثناء استبدال رمز التوثيق: {e}")

# واجهة المستخدم بناءً على حالة التوثيق
if st.session_state.credentials is None:
    st.info("مرحباً بك! يرجى تسجيل الدخول باستخدام حساب جوجل للبدء.")
    
    try:
        flow = get_oauth_flow()
        # استخدام prompt='select_account consent' لتفادي حظر 403 وإجبار جوجل على اختيار الحساب
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account consent'
        )
        
        st.markdown(
            f'<a href="{authorization_url}" target="_self" style="display:inline-block; text-decoration:none; background-color:#4285F4; color:white; padding:12px 24px; border-radius:6px; font-weight:bold; font-size:16px;">🔑 تسجيل الدخول باستخدام Google</a>', 
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"خطأ في تهيئة رابط التوثيق: {e}")

else:
    st.success("تم تسجيل الدخول بنجاح! 🎉")
    
    try:
        # جلب معلومات بريد وفك شفرة معلومات البروفايل
        service = build('oauth2', 'v2', credentials=st.session_state.credentials)
        user_info = service.userinfo().get().execute()
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if user_info.get('picture'):
                st.image(user_info.get('picture'), width=90)
        with col2:
            st.write(f"**الاسم:** {user_info.get('name')}")
            st.write(f"**البريد الإلكتروني:** {user_info.get('email')}")
            
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب بيانات البريد: {e}")

    st.divider()
    
    if st.button("تسجيل الخروج"):
        st.session_state.credentials = None
        st.rerun()
