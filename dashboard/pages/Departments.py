import streamlit as st
import pandas as pd
import plotly.express as px
from theme import load_data

st.markdown("<h1>🏢 Department Performance Benchmarks</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 14px;'>Comparative analysis of active engineering branches</p>", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("⚠️ No data available. Run the ETL pipeline first.")
else:
    # Calculate Department Summary
    dept_groups = df.groupby("department")
    dept_summary_list = []
    
    # Sort order to maintain consistent presentation
    branches = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "IT"]
    
    for branch in branches:
        if branch in dept_groups.groups:
            group = dept_groups.get_group(branch)
            student_count = len(group)
            avg_marks = round(group["average_marks"].mean(), 2)
            pass_rate = round((group["result"] == "Pass").sum() / student_count * 100, 2)
            avg_att = round(group["attendance"].mean(), 2)
            
            dept_summary_list.append({
                "department": branch,
                "student_count": student_count,
                "average_marks": avg_marks,
                "pass_rate": pass_rate,
                "attendance": avg_att
            })
            
    # Render stylized cards in a grid layout
    cols = st.columns(3)
    card_styles = {
        "CSE": "cse", "ECE": "ece", "EEE": "eee",
        "MECH": "mech", "CIVIL": "civil", "IT": "it"
    }
    
    for i, data in enumerate(dept_summary_list):
        col = cols[i % 3]
        style = card_styles.get(data["department"], "cse")
        
        with col:
            st.markdown(f"""
                <div class="kpi-card {style}" style="margin-bottom:20px;">
                    <div style="font-weight:700; font-size:18px; color:var(--text-color); margin-bottom:12px;">{data['department']} Department</div>
                    <div style="display:flex; flex-direction:column; gap:6px; font-size:13px;">
                        <div style="display:flex; justify-content:space-between;">
                            <span>Total Students:</span>
                            <b>{data['student_count']}</b>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span>Average Marks:</span>
                            <b style="color:#2563eb;">{data['average_marks']}%</b>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span>Pass Percentage:</span>
                            <b style="color:#10b981;">{data['pass_rate']}%</b>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span>Avg Attendance:</span>
                            <b>{data['attendance']}%</b>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    # Visual Chart: Comparison of Marks vs Attendance by Department
    st.markdown("---")
    st.subheader("Visual Benchmarking: Marks vs Attendance")
    
    df_dept_summary = pd.DataFrame(dept_summary_list)
    
    # Reshape for multi-bar plotly chart
    df_long = df_dept_summary.melt(
        id_vars=["department"],
        value_vars=["average_marks", "attendance"],
        var_name="Metric",
        value_name="Percentage"
    )
    df_long["Metric"] = df_long["Metric"].map({
        "average_marks": "Average Marks",
        "attendance": "Attendance Average"
    })
    
    fig_comp = px.bar(
        df_long,
        x="department",
        y="Percentage",
        color="Metric",
        barmode="group",
        title="Branch Performance vs Attendance Averages Comparison",
        color_discrete_sequence=["#3b82f6", "#10b981"]
    )
    
    fig_comp.update_layout(
        font_family="Outfit",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#64748b" if not st.session_state.dark_mode else "#f8fafc",
        margin=dict(t=40, b=20, l=10, r=10),
        legend=dict(orientation="h", y=-0.15)
    )
    st.plotly_chart(fig_comp, use_container_width=True)
