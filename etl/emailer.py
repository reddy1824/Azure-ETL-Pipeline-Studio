import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Template
from dotenv import load_dotenv
from etl.logger import setup_logger

load_dotenv()
logger = setup_logger("emailer")

class StudentEmailer:
    """
    Handles rendering and sending HTML email notifications with attachments.
    Supports a mock mode for local testing without SMTP credentials.
    """
    def __init__(self):
        self.sender = os.getenv("EMAIL_SENDER", "sender@example.com")
        self.password = os.getenv("EMAIL_PASSWORD", "your-app-password")
        self.receiver = os.getenv("EMAIL_RECEIVER", "receiver@example.com")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.mock_mode = os.getenv("USE_MOCK_EMAIL", "True").lower() == "true"
        
        if self.sender == "sender@example.com" or self.password == "your-app-password":
            logger.warning("Email credentials not configured in .env. Enforcing Mock Mode.")
            self.mock_mode = True

    def render_template(self, context):
        """
        Renders the HTML email template with provided context variables.
        """
        template_path = os.path.join("etl", "templates", "email_template.html")
        if not os.path.exists(template_path):
            # Fallback inline template in case file is missing
            logger.warning("Email template file not found. Using inline fallback.")
            return f"<h3>Pipeline Status: {context['run_status']}</h3><p>Processed {context['total_students']} records.</p>"
            
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
            
        template = Template(template_content)
        return template.render(context)

    def send_report(self, df, quality_metrics, run_status="SUCCESS", error_msg=None, attachments=None):
        """
        Gathers metrics, renders HTML email, and sends it (or simulates sending in mock mode).
        
        Args:
            df (pd.DataFrame): Transformed student dataframe.
            quality_metrics (dict): Quality metrics.
            run_status (str): "SUCCESS" or "FAILED".
            error_msg (str, optional): Error message.
            attachments (list, optional): List of local file paths to attach.
            
        Returns:
            bool: True if successful (or successfully mocked).
        """
        logger.info("Preparing email notification...")
        
        # Calculate summary metrics for the email context
        if df is not None and len(df) > 0:
            total_students = len(df)
            avg_marks = round(df["average_marks"].mean(), 2)
            pass_rate = round((df["result"] == "Pass").sum() / len(df) * 100, 2)
            max_score = round(df["average_marks"].max(), 2)
        else:
            total_students = 0
            avg_marks = 0.0
            pass_rate = 0.0
            max_score = 0.0
            
        context = {
            "run_status": run_status,
            "status_class": "success" if run_status == "SUCCESS" else "failed",
            "execution_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "CSV / Local File" if not error_msg else "System Error",
            "quality_score": quality_metrics.get("data_quality_score", 0.0) if quality_metrics else 0.0,
            "total_students": total_students,
            "avg_marks": avg_marks,
            "pass_rate": pass_rate,
            "max_score": max_score,
            "error_msg": error_msg
        }
        
        html_content = self.render_template(context)
        
        if self.mock_mode:
            logger.info("[MOCK EMAIL] Simulating email transmission...")
            logger.info(f"[MOCK EMAIL] From: {self.sender} | To: {self.receiver}")
            logger.info(f"[MOCK EMAIL] Subject: Student Performance ETL Status - {run_status}")
            
            # Save the rendered HTML locally for verification
            mock_email_path = os.path.join("reports", "mock_email.html")
            os.makedirs(os.path.dirname(mock_email_path), exist_ok=True)
            with open(mock_email_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"[MOCK EMAIL] Saved simulation HTML report to {mock_email_path} for visual inspection.")
            return True
            
        # Real SMTP Transmission
        try:
            logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}...")
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = self.receiver
            msg["Subject"] = f"Student Performance ETL Status - {run_status}"
            
            msg.attach(MIMEText(html_content, "html"))
            
            # Process attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        logger.info(f"Attaching file: {filepath}")
                        filename = os.path.basename(filepath)
                        with open(filepath, "rb") as attachment:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename= {filename}",
                            )
                            msg.attach(part)
                            
            # Connect and Send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email notification successfully sent to {self.receiver}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            logger.warning("Saving email locally as fallback due to SMTP error.")
            # Fallback to saving file
            mock_email_path = os.path.join("reports", "mock_email.html")
            with open(mock_email_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return True  # Return True to avoid breaking the pipeline execution
