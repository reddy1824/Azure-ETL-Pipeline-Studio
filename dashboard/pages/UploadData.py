import os
import subprocess
import pandas as pd
import streamlit as st
from theme import show_sidebar_status

st.markdown("<h1>📤 Ingest New Student Dataset</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 14px;'>Upload raw student records in CSV format to trigger the cleaning and loading ETL pipeline.</p>", unsafe_allow_html=True)

st.markdown("### Required CSV Columns Check")
st.markdown("""
Make sure your uploaded file contains the following column headers exactly:
`StudentID`, `Name`, `Department`, `Gender`, `Attendance`, `Mid1`, `Mid2`, `Assignment`, `FinalMarks`, `Result`, `Date`
""")

# File Uploader
uploaded_file = st.file_uploader("Choose Student CSV File", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Robust separator detection
        first_line = uploaded_file.readline()
        # Handle bytes or string representation
        if isinstance(first_line, bytes):
            first_line_str = first_line.decode('utf-8', errors='ignore')
        else:
            first_line_str = str(first_line)
            
        uploaded_file.seek(0)  # Reset pointer to start of file
        
        # Count potential delimiters
        delimiters = [',', ';', '\t', '|']
        counts = {d: first_line_str.count(d) for d in delimiters}
        sep = max(counts, key=counts.get)
        if counts[sep] == 0:
            sep = ',' # Fallback to comma
            
        # Load file into Pandas with detected separator
        df_upload = pd.read_csv(uploaded_file, sep=sep)
        
        # Clean column names (strip spaces and quotes)
        df_upload.columns = df_upload.columns.str.strip().str.replace('"', '').str.replace("'", "")
        original_cols = list(df_upload.columns)
        
        # Synonym mappings for automatic matching
        SYNONYMS = {
            "studentid": ["studentid", "student_id", "student id", "roll", "rollno", "roll number", "roll_number", "id", "uid"],
            "name": ["name", "student name", "student_name", "full name", "fullname", "full_name"],
            "department": ["department", "dept", "branch", "stream", "course", "major"],
            "gender": ["gender", "sex"],
            "attendance": ["attendance", "attendance (%)", "attendance_pct", "attendance_percentage", "att", "att_pct"],
            "mid1": ["mid1", "mid_1", "mid-term 1", "midterm 1", "midterm_1", "mid term 1", "mid 1"],
            "mid2": ["mid2", "mid_2", "mid-term 2", "midterm 2", "midterm_2", "mid term 2", "mid 2"],
            "assignment": ["assignment", "assignments", "assignment marks", "assignment_marks"],
            "finalmarks": ["finalmarks", "final marks", "final_marks", "final exam", "final_exam", "final semester exam", "semester exam", "marks"],
            "result": ["result", "status", "pass/fail", "pass_fail", "passfail", "remarks"],
            "date": ["date", "entry date", "date of entry", "date_of_entry", "timestamp"]
        }
        
        # Perform Auto-mapping
        mapped_cols = {}
        auto_mapped_info = []
        for target, syn_list in SYNONYMS.items():
            for col in original_cols:
                cleaned_col = col.strip().lower()
                if cleaned_col == target or cleaned_col in syn_list:
                    mapped_cols[col] = target
                    if col != target:
                        auto_mapped_info.append(f"'{col}' ➔ '{target}'")
                    break
        
        df_upload = df_upload.rename(columns=mapped_cols)
        
        # Auto-create missing columns with default mock data
        required_cols = ["studentid", "name", "department", "gender", "attendance", "mid1", "mid2", "assignment", "finalmarks", "result", "date"]
        
        auto_created_info = []
        import datetime
        import random
        
        for col in required_cols:
            if col not in df_upload.columns:
                # Generate defaults
                if col == "studentid":
                    df_upload[col] = [f"STU{1000 + i}" for i in range(len(df_upload))]
                elif col == "name":
                    df_upload[col] = [f"Student {1000 + i}" for i in range(len(df_upload))]
                elif col == "department":
                    df_upload[col] = "CSE"
                elif col == "gender":
                    df_upload[col] = [random.choice(["Male", "Female"]) for _ in range(len(df_upload))]
                elif col == "attendance":
                    df_upload[col] = 78.5
                elif col in ["mid1", "mid2", "assignment"]:
                    df_upload[col] = 75.0
                elif col == "finalmarks":
                    df_upload[col] = 78.0
                elif col == "result":
                    df_upload[col] = "Pass"
                elif col == "date":
                    df_upload[col] = datetime.datetime.now().strftime("%Y-%m-%d")
                auto_created_info.append(col)
                
        # Let's show a success notification that columns have been standardized
        st.success("✅ Dataset standardized successfully. Ready for processing!")
        
        if auto_mapped_info:
            st.info(f"🔄 Auto-mapped columns: {', '.join(auto_mapped_info)}")
        if auto_created_info:
            st.info(f"✨ Auto-generated missing columns with default parameters: {', '.join(auto_created_info)}")
            
        # Preview uploaded data
        st.write("### Dataset Preview (First 5 Rows)")
        display_df = df_upload[required_cols]
        st.dataframe(display_df.head(5), use_container_width=True)
        
        if st.button("🚀 Ingest Dataset & Run Pipeline", type="primary", use_container_width=True):
            # Save file, overwriting the raw student_data.csv
            data_path = os.path.join("data", "student_data.csv")
            os.makedirs(os.path.dirname(data_path), exist_ok=True)
            # Save only the required columns so the ETL is completely standardized
            display_df.to_csv(data_path, index=False)
            
            # Run ETL Pipeline script
            with st.spinner("Processing data pipeline (Extracting → Transforming → Loading SQLite → Backing up Azure)..."):
                try:
                    result = subprocess.run(
                        [".venv\\Scripts\\python", "run_etl.py"], 
                        capture_output=True, 
                        text=True
                    )
                    
                    if result.returncode == 0:
                        st.balloons()
                        st.success("🎉 Ingestion successful! The ETL pipeline loaded the database and refreshed reports.")
                        
                        # Log output print
                        with st.expander("ETL Execution log"):
                            st.code(result.stdout)
                            
                        # Rerun to refresh status and page
                        st.rerun()
                    else:
                        st.error("❌ Pipeline execution failed during loading.")
                        with st.expander("Stacktrace Details"):
                            st.code(result.stderr)
                            
                except Exception as e:
                    st.error(f"Error during execution: {str(e)}")
                    
    except Exception as e:
        st.error(f"Failed to read CSV: {str(e)}")
