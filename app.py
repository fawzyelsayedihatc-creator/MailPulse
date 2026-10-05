import os
import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# إعدادات الصفحة
st.set_page_config(page_title="MailPulse", page_icon="✉️", layout="wide")

# نطاقات الصلاحيات المطلوبة
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly"
]

def get_oauth_flow():
    """إنشاء تدفق OAuth باستخدام بيانات الاعتماد من Secrets بشكل آمن"""
    # استخدام .get لتجنب خطأ KeyError في حال وجود مفاتيح مفقودة
    oauth_secrets = st.secrets.get("google_oauth", {})
    
    client_config = {
        "web": {
            "client_id": oauth_secrets.get("client_id"),
            "client_secret": oauth_secrets.get("client_secret"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [oauth_secrets.get("redirect_uri")]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=oauth_secrets.get("redirect_uri")
    )
    return flow

# واجهة المستخدم الرئيسية
st.title("✉️ تطبيق MailPulse")

# إدارة الجلسة
if "credentials" not in st.session_state:
    st.session_state.credentials = None

# التقاط كود التحقق من الرابط
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
        st.error(f"حدث خطأ أثناء تسجيل الدخول: {e}")

# عرض الواجهة بناءً على حالة تسجيل الدخول
if st.session_state.credentials is None:
    st.info("مرحباً بك! يرجى تسجيل الدخول باستخدام حساب جوجل للبدء.")
    
    try:
        flow = get_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        st.markdown(
            f'<a href="{authorization_url}" target="_self" style="display:inline-block; text-decoration:none; background-color:#4285F4; color:white; padding:12px 24px; border-radius:6px; font-weight:bold; font-size:16px;">🔑 تسجيل الدخول باستخدام Google</a>', 
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"يرجى التأكد من ضبط st.secrets في Streamlit Cloud: {e}")

else:
    st.success("تم تسجيل الدخول بنجاح! 🎉")
    
    try:
        service = build('oauth2', 'v2', credentials=st.session_state.credentials)
        user_info = service.userinfo().get().execute()
        
        st.write(f"**البريد الإلكتروني:** {user_info.get('email')}")
        st.write(f"**الاسم:** {user_info.get('name')}")
        
        if user_info.get('picture'):
            st.image(user_info.get('picture'), width=80)
            
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات: {e}")

    if st.button("تسجيل الخروج"):
        st.session_state.credentials = None
        st.rerun()
