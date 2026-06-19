import os
import json
import datetime
import pandas as pd
# py:ignore [missing-import]
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from jinja2 import Template

# Import our ETL modules
from etl.logger import setup_logger
from etl.extractor import StudentExtractor
from etl.transformer import StudentTransformer
from etl.loader import StudentLoader
from etl.azure_loader import AzureBlobLoader
from etl.viz import generate_summary_charts
from etl.emailer import StudentEmailer

load_dotenv()
logger = setup_logger("run_etl")

def run_pipeline():
    """
    Executes the end-to-end Student Performance ETL pipeline.
    Tracks success of individual steps and writes state to data/pipeline_status.json.
    """
    logger.info("=========================================")
    logger.info("Starting Student Performance ETL Pipeline")
    logger.info("=========================================")
    
    status = {
        "last_run": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "extract": "Pending",
        "transform": "Pending",
        "load": "Pending",
        "azure_upload": "Pending",
        "email_report": "Pending",
        "quality_score": 0.0,
        "total_records": 0
    }
    
    # Save initial pending status
    os.makedirs("data", exist_ok=True)
    with open("data/pipeline_status.json", "w") as f:
        json.dump(status, f, indent=4)
        
    df_raw = None
    df_clean = None
    quality_metrics = None
    
    # 1. Extraction
    try:
        extractor = StudentExtractor()
        # Fallback parameters or azure SQL server if configured
        df_raw = extractor.run(source_type="CSV")
        status["extract"] = "Success"
        logger.info("Extraction step completed successfully.")
    except Exception as e:
        status["extract"] = "Failed"
        logger.error(f"Extraction step failed: {str(e)}")
        save_status(status)
        return False
        
    # 2. Transformation
    try:
        transformer = StudentTransformer()
        df_clean, quality_metrics = transformer.transform(df_raw)
        status["transform"] = "Success"
        status["quality_score"] = quality_metrics["data_quality_score"]
        status["total_records"] = len(df_clean)
        logger.info("Transformation step completed successfully.")
    except Exception as e:
        status["transform"] = "Failed"
        logger.error(f"Transformation step failed: {str(e)}")
        save_status(status)
        return False
        
    # 3. Loading
    try:
        loader = StudentLoader()
        loader.load(df_clean, quality_metrics)
        status["load"] = "Success"
        logger.info("Loading step completed successfully.")
    except Exception as e:
        status["load"] = "Failed"
        logger.error(f"Loading step failed: {str(e)}")
        save_status(status)
        return False
        
    # 4. Generate Reports (Visual and HTML)
    logger.info("Generating report files...")
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    summary_chart_path = os.path.join(reports_dir, "summary.png")
    html_report_path = os.path.join(reports_dir, "report.html")
    
    # Generate Matplotlib chart
    try:
        generate_summary_charts(df_clean, summary_chart_path)
    except Exception as e:
        logger.error(f"Failed to generate summary charts: {str(e)}")
        
    # Generate HTML Report
    try:
        compile_html_report(df_clean, quality_metrics, html_report_path)
        logger.info("HTML Report compiled successfully.")
    except Exception as e:
        logger.error(f"Failed to compile HTML report: {str(e)}")
        
    # 5. Azure Storage Upload
    try:
        # Default behavior checks Settings in Streamlit, but in headless CLI we read .env
        # Verify if disabled or enabled. Let's upload if credentials exist or mock mode is on.
        azure_loader = AzureBlobLoader()
        # Upload data CSV
        azure_loader.upload_file("data/student_data.csv", "raw_student_data.csv")
        # Upload HTML report
        azure_loader.upload_file(html_report_path, "reports/report.html")
        # Upload Summary Chart
        azure_loader.upload_file(summary_chart_path, "reports/summary.png")
        status["azure_upload"] = "Success"
        logger.info("Azure Upload step completed successfully.")
    except Exception as e:
        status["azure_upload"] = "Failed"
        logger.error(f"Azure Upload step failed: {str(e)}")
        
    # 6. Email Report
    try:
        emailer = StudentEmailer()
        attachments = [html_report_path, summary_chart_path]
        emailer.send_report(
            df_clean, 
            quality_metrics, 
            run_status="SUCCESS", 
            attachments=attachments
        )
        status["email_report"] = "Success"
        logger.info("Email Report step completed successfully.")
    except Exception as e:
        status["email_report"] = "Failed"
        logger.error(f"Email Report step failed: {str(e)}")
        
    save_status(status)
    logger.info("=========================================")
    logger.info("ETL Pipeline Execution Completed Status:")
    logger.info(f"Extract: {status['extract']}")
    logger.info(f"Transform: {status['transform']}")
    logger.info(f"Load: {status['load']}")
    logger.info(f"Azure Upload: {status['azure_upload']}")
    logger.info(f"Email Report: {status['email_report']}")
    logger.info("=========================================")
    return True

def save_status(status):
    """
    Saves the pipeline run status to data/pipeline_status.json
    """
    with open("data/pipeline_status.json", "w") as f:
        json.dump(status, f, indent=4)

def compile_html_report(df, quality_metrics, output_path):
    """
    Renders the HTML report template using student metrics.
    """
    template_path = os.path.join("etl", "templates", "report_template.html")
    if not os.path.exists(template_path):
        logger.error("HTML report template missing. Cannot compile report.")
        return
        
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    # Calculate stats
    total_students = len(df)
    avg_marks = round(df["average_marks"].mean(), 2)
    pass_rate = round((df["result"] == "Pass").sum() / len(df) * 100, 2)
    
    # Department summary stats
    dept_stats = []
    for dept, group in df.groupby("department"):
        dept_stats.append({
            "Department": dept,
            "Total_Students": len(group),
            "Average_Marks": round(group["average_marks"].mean(), 2),
            "Pass_Rate": round((group["result"] == "Pass").sum() / len(group) * 100, 2)
        })
    # Sort departments alphabetically
    dept_stats = sorted(dept_stats, key=lambda x: x["Department"])
    
    # Top 10 students
    top_10 = df.sort_values(by="average_marks", ascending=False).head(10)
    top_students_list = []
    for idx, row in top_10.iterrows():
        top_students_list.append({
            "StudentID": row["studentid"],
            "Name": row["name"],
            "Department": row["department"],
            "Final_Marks": row["finalmarks"],
            "Attendance": row["attendance"],
            "Grade": row["grade"]
        })
        
    template = Template(template_content)
    rendered_html = template.render(
        execution_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_students=total_students,
        avg_marks=avg_marks,
        pass_rate=pass_rate,
        quality_score=quality_metrics.get("data_quality_score", 100.0),
        dept_summary=dept_stats,
        top_students=top_students_list
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

if __name__ == "__main__":
    run_pipeline()
