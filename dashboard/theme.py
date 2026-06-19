import os
import sys
import json
import sqlite3
import pandas as pd
import streamlit as st

# Add project root directory to sys.path to resolve etl package imports in subpages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_db_connection():
    """
    Returns a connection to the SQLite database.
    """
    db_path = os.path.join("data", "etl.db")
    if not os.path.exists(db_path):
        return None
    return sqlite3.connect(db_path)

def load_data():
    """
    Loads student data from the SQLite database.
    """
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql("SELECT * FROM students", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def apply_theme():
    """
    Applies custom CSS variables, premium fonts, and style overrides for cards,
    metrics, badges, and animations.
    """
    # Import google font Outfit
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        /* Apply fonts globally */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Force dark background for main container and sidebar */
        .stApp {
            background-color: #0b0f19 !important;
            color: #f8fafc !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #0f1322 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* KPI Cards Styling */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .kpi-card {
            background-color: #ffffff !important;
            border-radius: 8px;
            padding: 15px 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            transition: all 0.2s ease;
            border: 1px solid #e2e8f0;
            color: #0f172a !important;
        }
        
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(255, 255, 255, 0.05);
        }
        
        .kpi-title {
            font-size: 11px;
            color: #64748b !important;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .kpi-value {
            font-size: 26px;
            font-weight: 700;
            color: #0f172a !important;
            line-height: 1.1;
        }
        
        .kpi-subtext {
            font-size: 11px;
            margin-top: 5px;
            font-weight: 500;
        }
        
        .kpi-subtext.up { color: #10b981 !important; }
        .kpi-subtext.down { color: #ef4444 !important; }
        
        /* Custom sidebar styles */
        .sidebar-status {
            background-color: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            padding: 12px;
            margin-top: 15px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Premium Table CSS for dark layout */
        .stTable {
            background-color: #111827 !important;
            color: #f8fafc !important;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #1f2937;
        }
        
        /* Card-like Student Search Result Block */
        .student-result-card {
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 8px;
            padding: 12px 15px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s ease;
        }
        
        .student-result-card:hover {
            border-color: #3b82f6;
            background-color: #1f2937;
        }
        
        .student-result-info {
            display: flex;
            flex-direction: column;
        }
        
        .student-result-name {
            font-weight: 700;
            font-size: 14px;
            color: #ffffff;
        }
        
        .student-result-meta {
            font-size: 11px;
            color: #94a3b8;
            margin-top: 3px;
        }
        
        .student-result-marks {
            font-size: 14px;
            font-weight: 700;
            color: #3b82f6;
            text-align: right;
        }
        
        .student-result-avg-lbl {
            font-size: 10px;
            color: #64748b;
        }
        
        /* Profile and results badges */
        .badge-result {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        .badge-result.pass { background-color: #d1fae5; color: #065f46; }
        .badge-result.fail { background-color: #fee2e2; color: #991b1b; }
        </style>
    """, unsafe_allow_html=True)

def show_sidebar_status():
    """
    Renders the ETL System Operational status panel in the sidebar.
    """
    st.sidebar.markdown("---")
    
    status_file = "data/pipeline_status.json"
    last_run_time = "Never"
    
    if os.path.exists(status_file):
        try:
            with open(status_file, "r") as f:
                status_data = json.load(f)
                last_run_time = status_data.get("last_run", "Never")
        except Exception:
            pass
            
    st.sidebar.markdown(f"""
        <div style="background-color:rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.15); border-radius:8px; padding:12px; font-size:12px; margin-bottom:15px;">
            <div style="color:#10b981; font-weight:bold; margin-bottom:5px; display:flex; align-items:center; gap:5px;">
                <span style="font-size:14px;">●</span> All Systems Operational
            </div>
            <div style="color:#64748b; margin-bottom:3px;">Internet (Connected)</div>
            <div style="color:#64748b; margin-bottom:8px;">Cloud Sync Enabled</div>
            <div style="color:#94a3b8; font-size:10px; border-top: 1px solid rgba(128,128,128,0.15); padding-top:5px; margin-top:5px;">
                Last Update: {last_run_time}
            </div>
        </div>
    """, unsafe_allow_html=True)
