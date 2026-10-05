import streamlit as st
import pandas as pd
import database as db

# تعيين إيميلك كأدمن
ADMIN_EMAIL = fawziali2040@gmail.com

st.set_page_config(
    page_title=MailPulse Dashboard,
    page_icon=✉️,
    layout=wide
)

# تهيئة قاعدة البيانات
db.init_db(ADMIN_EMAIL)

# تثبيت جلسة تسجيل الدخول حتى لو المستخدِم عمل Refresh
if logged_in not in st.session_state
    st.session_state.logged_in = False
if user_email not in st.session_state
    st.session_state.user_email = 
if role not in st.session_state
    st.session_state.role = user
if current_page not in st.session_state
    st.session_state.current_page = dashboard

# استعادة الجلسة من الـ Query Params عند عمل Refresh
query_params = st.query_params
if not st.session_state.logged_in and user in query_params
    saved_user = query_params[user]
    u = db.get_or_create_user(saved_user)
    if u and u[4] == 1
        st.session_state.logged_in = True
        st.session_state.user_email = u[0]
        st.session_state.role = u[1]

# واجهة تسجيل الدخول
if not st.session_state.logged_in
    _, col, _ = st.columns([1, 2, 1])
    with col
        st.markdown(h1 style='text-align center; color #059669;'✉️ MailPulseh1, unsafe_allow_html=True)
        st.markdown(p style='text-align center;'منصة إدارة الحملات البريدية وتحديد رصيد المستخدمينp, unsafe_allow_html=True)
        
        user_input = st.text_input(أدخل بريد Google الخاص بك للبدء, placeholder=example@gmail.com)
        
        if st.button(تسجيل الدخول بـ Google, use_container_width=True)
            if user_input and @ in user_input
                email_clean = user_input.strip().lower()
                u = db.get_or_create_user(email_clean)
                
                if u[4] == 0
                    st.error(🔴 الحساب معطل حالياً من الأدمن.)
                else
                    st.session_state.logged_in = True
                    st.session_state.user_email = u[0]
                    st.session_state.role = u[1]
                    st.query_params[user] = u[0]
                    st.rerun()
            else
                st.error(يرجى كتابة البريد بشكل صحيح.)

# بعد تسجيل الدخول
else
    user_data = db.get_or_create_user(st.session_state.user_email)
    email, role, email_limit, emails_sent, is_active = user_data
    remaining = email_limit - emails_sent

    with st.sidebar
        st.markdown(f### 👤 `{email}`)
        st.markdown(fالرتبة {'👑 أدمن' if role == 'admin' else '👤 مستخدم'})
        st.metric(📊 الرصيد المتبقي, f{remaining} إيميل, delta=fالمرسل {emails_sent})
        
        if st.button(🚀 حملة إرسال جديدة, use_container_width=True)
            st.session_state.current_page = new_campaign
            st.rerun()
            
        if role == 'admin'
            if st.button(👑 لوحة تحكم الأدمن, use_container_width=True)
                st.session_state.current_page = admin_panel
                st.rerun()
                
        if st.button(🚪 تسجيل الخروج, use_container_width=True)
            st.session_state.logged_in = False
            st.session_state.user_email = 
            st.query_params.clear()
            st.rerun()

    # صفحة الأدمن
    if st.session_state.current_page == admin_panel and role == 'admin'
        st.title(👑 لوحة تحكم الأدمن وإدارة كوتة المستخدمين)
        users = db.get_all_users()
        df_users = pd.DataFrame(users, columns=[البريد الإلكتروني, الرتبة, حد الإرسال, الإيميلات المرسلة, الحالة])
        st.dataframe(df_users, use_container_width=True)
        
        st.subheader(⚙️ تعديل رصيد إرسال مستخدم)
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1
            selected_user = st.selectbox(اختر المستخدِم, [u[0] for u in users])
        with col2
            new_limit = st.number_input(الرصيد الجديد, min_value=0, value=500, step=50)
        with col3
            if st.button(تحديث الرصيد)
                db.update_user_limit(selected_user, new_limit)
                st.success(تم التحديث بنجاح!)
                st.rerun()
    else
        st.title(🚀 إنشاء حملة إرسال جديدة)
        st.info(fرصيدك الماليالإرسالي المتاح حالياً هو {remaining} إيميل.)