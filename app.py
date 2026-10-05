import os
import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# إعدادات الصفحة
st.set_page_config(page_title="MailPulse", page_icon="✉️", layout="wide")

# نطاقات الصلاحيات المطلوبة (Scope)
# تم اختيار نطاق القراءة فقط لتقليل قيود Google OAuth
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly"
]

def get_oauth_flow():
    """إنشاء تدفق OAuth باستخدام بيانات الاعتماد المسجلة في Streamlit Secrets أو متغيرات البيئة"""
    client_config = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "project_id": st.secrets["google_oauth"]["project_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
    )
    return flow

# واجهة المستخدم الرئيسية
st.title("✉️ تطبيق MailPulse")

# إدارة الجلسة (Session State)
if "credentials" not in st.session_state:
    st.session_state.credentials = None

# التقاط كود التحقق من الرابط بعد إعادة التوجيه
query_params = st.query_params
if "code" in query_params and st.session_state.credentials is None:
    code = query_params["code"]
    try:
        flow = get_oauth_flow()
        flow.fetch_token(code=code)
        st.session_state.credentials = flow.credentials
        # إزالة الكود من URL بعد النجاح
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"حدث خطأ أثناء تسجيل الدخول: {e}")

# عرض محتوى التطبيق بناءً على حالة تسجيل الدخول
if st.session_state.credentials is None:
    st.info("مرحباً بك! يرجى تسجيل الدخول باستخدام حساب جوجل للبدء.")
    
    if st.button("🔑 تسجيل الدخول باستخدام Google"):
        flow = get_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        st.markdown(f'<a href="{authorization_url}" target="_self" style="text-decoration:none; background-color:#4285F4; color:white; padding:10px 20px; border-radius:5px; font-weight:bold;">اضغط هنا لتسجيل الدخول عبر Google</a>', unsafe_unsafe_html=True)

else:
    st.success("تم تسجيل الدخول بنجاح! 🎉")
    
    # جلب معلومات المستخدم
    try:
        service = build('oauth2', 'v2', credentials=st.session_state.credentials)
        user_info = service.userinfo().get().execute()
        
        st.write(f"**البريد الإلكتروني:** {user_info.get('email')}")
        st.write(f"**الاسم:** {user_info.get('name')}")
        
        if user_info.get('picture'):
            st.image(user_info.get('picture'), width=100)
            
    except Exception as e:
        st.error(f"فشل جلب بيانات البريد: {e}")

    # زر تسجيل الخروج
    if st.button("تسجيل الخروج"):
        st.session_state.credentials = None
        st.rerun()
