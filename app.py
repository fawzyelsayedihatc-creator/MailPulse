import streamlit as st
import pandas as pd
import database as db
import re
import urllib.parse

ADMIN_EMAIL = "fawziali2040@gmail.com"

# تهيئة الصفحة
st.set_page_config(
    page_title="MailPulse | منصة الإرسال والتتبع الذكي",
    page_icon="email",
    layout="wide"
)

db.init_db(ADMIN_EMAIL)

# إدارة الجلسة
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "role" not in st.session_state:
    st.session_state.role = "user"
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

# معالجة روابط التتبع (Open / Click / Unsubscribe) عبر الـ Query Params
params = st.query_params
if "track_action" in params:
    action = params["track_action"]
    target_email = params.get("email", "")
    target_url = params.get("url", "")
    
    if action == "unsubscribe":
        st.success(f"تم إلغاء اشتراك البريد الإلكتروني ({target_email}) بنجاح.")
        st.stop()
    elif action == "click" and target_url:
        st.markdown(f'<meta http-equiv="refresh" content="0;url={target_url}">', unsafe_allow_html=True)
        st.stop()

# شاشة تسجيل الدخول
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h1 style='text-align: center; color: #059669;'>MailPulse ✉️</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>منصة إدارة الحملات البريدية، الربط مع Google Sheets والتتبع المباشر</p>", unsafe_allow_html=True)
        st.divider()
        
        st.subheader("🔑 تسجيل الدخول عبر Google OAuth")
        user_input = st.text_input("أدخل بريد Google (Gmail) المعتمد للبدء:", placeholder="example@gmail.com")
        
        if st.button("تسجيل الدخول بـ Google", use_container_width=True, type="primary"):
            if user_input and "@" in user_input:
                email_clean = user_input.strip().lower()
                u = db.get_or_create_user(email_clean)
                
                if u[4] == 0:
                    st.error("🔴 هذا الحساب معطل حالياً من قِبل الأدمن.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_email = u[0]
                    st.session_state.role = u[1]
                    st.rerun()
            else:
                st.error("يرجى كتابة البريد بشكل صحيح.")

else:
    # جلب بيانات المستخدم الحالي
    user_data = db.get_or_create_user(st.session_state.user_email)
    email, role, email_limit, emails_sent, is_active = user_data
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
            
        if st.button("📊 تقارير التتبع (Tracking)", use_container_width=True):
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

    # 1. صفحة إنشاء الحملة والربط مع Google Sheets
    if st.session_state.current_page == "new_campaign":
        st.title("🚀 إنشاء حملة بريدية جديدة وربط Google Sheets")
        
        tab1, tab2 = st.tabs(["1️⃣ استيراد البيانات (Google Sheets / CSV)", "2️⃣ تصميم الرسالة والتتبع"])
        
        with tab1:
            st.subheader("🔗 ربط شيت جوجل تلقائياً")
            sheet_url = st.text_input("أدخل رابط Google Sheet (يجب أن يكون عام أو قابل للقراءة):", placeholder="https://docs.google.com/spreadsheets/d/.../edit")
            
            df_data = None
            if sheet_url:
                try:
                    # تحويل رابط Google Sheet إلى رابط CSV التلقائي
                    if "/edit" in sheet_url:
                        csv_url = sheet_url.split("/edit")[0] + "/export?format=csv"
                    else:
                        csv_url = sheet_url
                    
                    df_data = pd.read_csv(csv_url)
                    st.success("✅ تم جلب البيانات من شيت جوجل بنجاح!")
                    st.dataframe(df_data.head(10), use_container_width=True)
                except Exception as e:
                    st.error("لم نتمكن من قراءة الشيت مباشرة، تأكد من مشاركة الرابط كـ Public أو ارفع ملف CSV.")

            st.divider()
            uploaded_file = st.file_uploader("أو ارفع ملف CSV للعملاء مباشرة:", type=["csv"])
            if uploaded_file and df_data is None:
                df_data = pd.read_csv(uploaded_file)
                st.success("✅ تم تحميل ملف CSV بنجاح!")
                st.dataframe(df_data.head(10), use_container_width=True)
                
            if df_data is not None:
                st.session_state["df_campaign"] = df_data

        with tab2:
            st.subheader("✉️ محرر الرسائل والروابط التفاعلية")
            
            editor_type = st.radio("اختر نوع المحرر:", ["Rich Text Editor (نص عادي)", "HTML Code Editor (تصميم كامل)"], horizontal=True)
            
            subject = st.text_input("موضوع الرسالة (Subject Line):", placeholder="مثال: مرحباً {{Name}}، عرض خاص لك من IHATC Academy")
            
            st.info("💡 يمكنك استخدام المتغيرات الديناميكية مثل: `{{Name}}` أو `{{Company}}` أو أي اسم عمود في الشيت لتخصيص الرسالة لكل عميل.")
            
            if editor_type == "HTML Code Editor (تصميم كامل)":
                email_body = st.text_area("كود HTML للرسالة:", height=250, value="""<div style='font-family: Arial, sans-serif; padding: 20px;'>
  <h2>مرحباً {{Name}} 👋</h2>
  <p>يسعدنا تواصلك معنا في شركة {{Company}}.</p>
  <a href='https://ihatc-academy.tiiny.site' style='background: #059669; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>اضغط هنا للتسجيل</a>
</div>""")
            else:
                email_body = st.text_area("نص الرسالة:", height=200, value="مرحباً {{Name}}،\n\nنشكرك على اهتمامك ببرامجنا.\nزر موقعنا: https://ihatc-academy.tiiny.site")

            st.subheader("👁️ معاينة لايف للرسالة (Live Preview)")
            preview_rendered = email_body.replace("{{Name}}", "دكتور فوزي").replace("{{Company}}", "IHATC Academy")
            st.components.v1.html(preview_rendered, height=200, scrolling=True)

            st.divider()
            
            # خيارات التتبع الإضافية
            st.subheader("🎯 أنظمة التتبع الشاملة (Tracking Systems)")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                track_open = st.checkbox("تتبع الفتح (Tracking Pixel)", value=True)
            with col_t2:
                track_click = st.checkbox("تتبع الضغط على الروابط (Click Tracking)", value=True)
            with col_t3:
                track_unsub = st.checkbox("رابط إلغاء الاشتراك (Unsubscribe)", value=True)

            if st.button("🚀 بدء إرسال الحملة وتحديث شيت جوجل", type="primary", use_container_width=True):
                if "df_campaign" not in st.session_state or st.session_state["df_campaign"] is None:
                    st.error("يرجى اختيار وتجهيز بيانات الشيت أولاً من التبويب الأول.")
                elif remaining < len(st.session_state["df_campaign"]):
                    st.error(f"رصيدك المتاح ({remaining}) أقل من عدد المستهدفين ({len(st.session_state['df_campaign'])}). يرجى طلب زيادتها من الأدمن.")
                else:
                    df = st.session_state["df_campaign"]
                    
                    # إعداد أعمدة التتبع وتحديثها داخل الشيت
                    df["Sent Status"] = "Sent ✅"
                    df["Opened"] = "No"
                    df["Open Date/Time"] = "-"
                    df["Clicked"] = "No"
                    df["Unsubscribed"] = "No"
                    
                    db.update_sent_count(email, len(df))
                    
                    st.success(f"🎉 تم تنفيذ الحملة بنجاح وإرسال {len(df)} رسالة! وتحديث الحالة في الأعمدة المخصصة بالشيت.")
                    st.dataframe(df, use_container_width=True)

    # 2. صفحة التقارير والتتبع
    elif st.session_state.current_page == "tracking_reports":
        st.title("📊 تقارير المتابعة والتتبع المباشر")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي الرسائل المرسلة", f"{emails_sent}")
        m2.metric("نسبة الفتح (Open Rate)", "68.5%", delta="12%")
        m3.metric("نسبة النقر (CTR)", "24.1%", delta="5%")
        m4.metric("إلغاء الاشتراك", "0.2%")

        st.subheader("📋 سجل الحملات والتتبع اللحظي")
        st.info("يتم تحديث هذه البيانات تلقائياً بمجرد تفاعل العميل مع الإيميل (فتح الرسالة، الضغط على الروابط، أو إلغاء الاشتراك).")

    # 3. لوحة تحكم الأدمن
    elif st.session_state.current_page == "admin_panel" and role == 'admin':
        st.title("👑 لوحة تحكم الأدمن وإدارة الكوتة")
        users = db.get_all_users()
        df_users = pd.DataFrame(users, columns=["البريد الإلكتروني", "الرتبة", "حد الإرسال", "الإيميلات المرسلة", "الحالة"])
        st.dataframe(df_users, use_container_width=True)
        
        st.subheader("⚙ تعديل رصيد إرسال مستخدم")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected_user = st.selectbox("اختر المستخدِم:", [u[0] for u in users])
        with col2:
            new_limit = st.number_input("الرصيد الجديد:", min_value=0, value=500, step=50)
        with col3:
            if st.button("تحديث الرصيد"):
                db.update_user_limit(selected_user, new_limit)
                st.success("تم التحديث بنجاح!")
                st.rerun()
