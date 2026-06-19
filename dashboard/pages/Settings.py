import streamlit as st
import subprocess
from theme import show_sidebar_status

st.markdown("<h1>⚙️ System Administration Settings</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 14px;'>Configure ETL integrations, notifications, and portal aesthetics</p>", unsafe_allow_html=True)

# 1. Configurations Section
st.subheader("ETL Ingestion & Notification Settings")

azure_toggle = st.toggle("Enable Azure Blob Storage Uploads", value=st.session_state.azure_enabled)
if azure_toggle != st.session_state.azure_enabled:
    st.session_state.azure_enabled = azure_toggle
    st.success(f"Azure Uploads set to: {azure_toggle}")
    st.rerun()

email_toggle = st.toggle("Enable Gmail SMTP Notifications", value=st.session_state.email_enabled)
if email_toggle != st.session_state.email_enabled:
    st.session_state.email_enabled = email_toggle
    st.success(f"SMTP Notifications set to: {email_toggle}")
    st.rerun()

st.markdown("---")
st.subheader("Portal Interface Theme")

theme_toggle = st.toggle("Force Dark Mode Theme Overrides", value=st.session_state.dark_mode)
if theme_toggle != st.session_state.dark_mode:
    st.session_state.dark_mode = theme_toggle
    st.success("Theme preference saved. Refreshing workspace...")
    st.rerun()

refresh_toggle = st.toggle("Enable Automatic Page Refresh (30s intervals)", value=st.session_state.auto_refresh)
if refresh_toggle != st.session_state.auto_refresh:
    st.session_state.auto_refresh = refresh_toggle
    st.success(f"Auto Refresh set to: {refresh_toggle}")
    st.rerun()

st.markdown("---")
st.subheader("Manual Pipeline Orchestration")
st.markdown("Force execution of the extraction, cleaning, SQLite load, Azure upload, and emailing pipeline:")

if st.button("🚀 Trigger ETL Pipeline Execution", type="primary", use_container_width=True):
    with st.spinner("Executing ETL Pipeline Orchestration (Extract → Clean → Load SQLite → Azure → Email)..."):
        try:
            # Trigger run_etl.py as a subprocess
            # We pass environment configurations using os overrides or arguments if necessary, 
            # but since .env governs it, it runs automatically. We can pass flags to disable/mock 
            # if session states dictate, but standard is fine.
            # Let's run it!
            result = subprocess.run(
                [".venv\\Scripts\\python", "run_etl.py"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                st.balloons()
                st.success("🎉 ETL Pipeline execution completed successfully!")
                # Show stdout snippet
                with st.expander("Show Execution log output"):
                    st.code(result.stdout)
                st.rerun()
            else:
                st.error("❌ ETL Pipeline execution failed.")
                with st.expander("Show Failure stacktrace"):
                    st.code(result.stderr)
        except Exception as e:
            st.error(f"Failed to execute ETL process: {str(e)}")
