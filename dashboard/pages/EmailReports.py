import os
import sys
# Add project root directory to sys.path to resolve etl package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from dotenv import load_dotenv
from etl.emailer import StudentEmailer
from theme import load_data

load_dotenv()

st.markdown("<h1>✉️ Email Reports Dispatcher</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 14px;'>Manually compile student performance summaries and dispatch email alerts to administrators.</p>", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("⚠️ No data available in database. Run the ETL pipeline first.")
else:
    st.subheader("Notification Details")
    
    sender_email = os.getenv("EMAIL_SENDER", "sender@example.com")
    receiver_email = st.text_input("Receiver Email Address", value=os.getenv("EMAIL_RECEIVER", "receiver@example.com"))
    
    # Check mock status
    mock_mode = os.getenv("USE_MOCK_EMAIL", "True").lower() == "true" or sender_email == "sender@example.com"
    
    if mock_mode:
        st.info("ℹ️ System is running in **Mock Mode**. Clicking send will generate and save the HTML email locally to `reports/mock_email.html` for layout testing, skipping the external SMTP connection.")
    else:
        st.success("✅ SMTP configurations detected. Real email transmission is active.")
        
    if st.button("✉️ Compile and Send Report", type="primary", use_container_width=True):
        with st.spinner("Compiling HTML template and attachments (report.html & summary.png)..."):
            try:
                # Initialize Emailer
                emailer = StudentEmailer()
                # Overwrite receiver if custom inputted
                emailer.receiver = receiver_email
                
                # Fetch attachments
                html_path = "reports/report.html"
                png_path = "reports/summary.png"
                attachments = []
                if os.path.exists(html_path):
                    attachments.append(html_path)
                if os.path.exists(png_path):
                    attachments.append(png_path)
                    
                # Read runs details
                from etl.loader import StudentLoader
                loader = StudentLoader()
                last_run = loader.get_last_run()
                quality_metrics = last_run.get("details", {}) if last_run else {}
                
                success = emailer.send_report(
                    df, 
                    quality_metrics, 
                    run_status="SUCCESS", 
                    attachments=attachments
                )
                
                if success:
                    st.success(f"📧 Notification processed successfully!")
                    if mock_mode:
                        st.markdown(f"**Mock Output:** Visual HTML newsletter output generated and saved at `reports/mock_email.html`.")
                        # Render mock email preview link or button
                        with open("reports/mock_email.html", "r", encoding="utf-8") as f:
                            mail_html = f.read()
                        with st.expander("Preview Rendered Newsletter HTML"):
                            st.components.v1.html(mail_html, height=450, scrolling=True)
                    else:
                        st.success(f"Email successfully delivered to {receiver_email} via SMTP relay.")
                else:
                    st.error("Failed to process email report.")
                    
            except Exception as e:
                st.error(f"Error compiling notification: {str(e)}")
