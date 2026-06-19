import os
import sys
import streamlit as st

# Add project root directory to sys.path to resolve etl package imports in subpages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from theme import apply_theme, show_sidebar_status

# Configure the Streamlit page
st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State Variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "azure_enabled" not in st.session_state:
    st.session_state.azure_enabled = True
if "email_enabled" not in st.session_state:
    st.session_state.email_enabled = True
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

# Logout Callback
def logout():
    st.session_state.logged_in = False
    st.success("Logged out successfully!")
    st.rerun()

# Apply CSS Theme Overrides
apply_theme()

# Custom stylesheet injection for light/dark mode and login card
if st.session_state.dark_mode:
    # Inject Dark Mode specific CSS
    st.markdown("""
        <style>
        /* Global Background overrides for Dark Mode */
        .stApp {
            background-color: #0f172a; /* Slate 900 */
            color: #f8fafc; /* Slate 50 */
        }
        .kpi-card {
            background-color: #1e293b !important; /* Slate 800 */
            border-color: #334155 !important;
            color: #f8fafc !important;
        }
        .kpi-value {
            color: #ffffff !important;
        }
        .kpi-title {
            color: #94a3b8 !important;
        }
        .sidebar-status {
            background-color: #1e293b !important;
            border-color: #334155 !important;
        }
        .profile-header {
            background-color: #1e293b !important;
            border-color: #334155 !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #f8fafc !important;
        }
        /* Style secondary items in tabs */
        .stTabs button {
            color: #94a3b8 !important;
        }
        .stTabs button[aria-selected="true"] {
            color: #3b82f6 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Login Page Layout
if not st.session_state.logged_in:
    # Stylized Login Form Container
    st.markdown("""
        <style>
        .login-wrapper {
            max-width: 450px;
            margin: 80px auto;
            padding: 40px;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
            border: 1px solid #e2e8f0;
            text-align: center;
        }
        .login-wrapper h2 {
            color: #1e3a8a;
            margin-bottom: 5px;
            font-weight: 700;
        }
        .login-wrapper p {
            color: #64748b;
            font-size: 14px;
            margin-bottom: 30px;
        }
        .login-logo {
            font-size: 50px;
            margin-bottom: 15px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # CSS injection for dark mode login box
    if st.session_state.dark_mode:
        st.markdown("""
            <style>
            .login-wrapper {
                background-color: #1e293b !important;
                border-color: #334155 !important;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3) !important;
            }
            .login-wrapper h2 {
                color: #f8fafc !important;
            }
            .login-wrapper p {
                color: #94a3b8 !important;
            }
            </style>
        """, unsafe_allow_html=True)

    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo">🎓</div>', unsafe_allow_html=True)
    st.markdown('<h2>Student Analytics Studio</h2>', unsafe_allow_html=True)
    st.markdown('<p>Cloud-Based ETL & Data Management Portal</p>', unsafe_allow_html=True)
    
    # Render Login Form Fields inside columns to align neatly
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        username = st.text_input("Username", placeholder="Enter admin username", key="login_user")
        password = st.text_input("Password", type="password", placeholder="Enter admin password", key="login_pass")
        st.write("")
        login_btn = st.button("Log In", use_container_width=True, type="primary")
        
        if login_btn:
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.success("Successfully authenticated!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
                
    st.markdown('</div>', unsafe_allow_html=True)

# Main Multi-Page App Navigation
else:
    # Define absolute paths to each page script inside pages/ subdirectory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pages_dir = os.path.join(base_dir, "pages")
    
    home_page = st.Page(os.path.join(pages_dir, "Home.py"), title="Dashboard", icon="📊", default=True)
    upload_page = st.Page(os.path.join(pages_dir, "UploadData.py"), title="Upload Data", icon="📤")
    view_page = st.Page(os.path.join(pages_dir, "ViewRecords.py"), title="View Records", icon="📋")
    quality_page = st.Page(os.path.join(pages_dir, "DataQuality.py"), title="Data Quality", icon="🔍")
    email_page = st.Page(os.path.join(pages_dir, "EmailReports.py"), title="Email Reports", icon="✉️")
    download_page = st.Page(os.path.join(pages_dir, "DownloadCenter.py"), title="Download Center", icon="💾")
    logout_page = st.Page(logout, title="Log Out", icon="🚪")
    
    # Custom Sidebar Logo & Details
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 10px 0;'>
            <h2 style='margin: 0; color: #3b82f6;'>🎓 EduAnalytics</h2>
            <small style='color: #64748b;'>Student Data Operations</small>
        </div>
    """, unsafe_allow_html=True)
    
    # Configure multipage navigation sections under DATA MANAGEMENT category
    pg = st.navigation({
        "DATA MANAGEMENT": [home_page, upload_page, view_page, quality_page, email_page, download_page, logout_page]
    })
    
    # Render pipeline status in the sidebar
    show_sidebar_status()
    
    # Run the current subpage
    pg.run()
