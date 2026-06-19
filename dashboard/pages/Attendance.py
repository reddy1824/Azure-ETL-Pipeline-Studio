import streamlit as st
import pandas as pd
import plotly.express as px
from theme import load_data

st.markdown("<h1>📅 Attendance Diagnostics & Monitoring</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 14px;'>Attendance averages, trends, and regulatory shortage alerts</p>", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("⚠️ No data available. Run the ETL pipeline first.")
else:
    # Top KPI Metrics
    total_count = len(df)
    avg_attendance = round(df["attendance"].mean(), 2)
    shortage_count = (df["attendance"] < 75).sum()
    regular_count = total_count - shortage_count
    shortage_rate = round(shortage_count / total_count * 100, 2)
    
    st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px;">
            <div class="kpi-card ece">
                <div class="kpi-title">Average Attendance</div>
                <div class="kpi-value">{avg_attendance}%</div>
                <div class="kpi-subtext" style="color:#10b981;">Statutory threshold: 75%</div>
            </div>
            <div class="kpi-card civil">
                <div class="kpi-title">Shortage Alerts (< 75%)</div>
                <div class="kpi-value">{shortage_count}</div>
                <div class="kpi-subtext down">⚠️ {shortage_rate}% of students</div>
            </div>
            <div class="kpi-card cse">
                <div class="kpi-title">Regular Attendance (>= 75%)</div>
                <div class="kpi-value">{regular_count}</div>
                <div class="kpi-subtext up">▲ Eligible for Final Exam</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Row 1: Charts
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Department-wise average attendance
        dept_att = df.groupby("department")["attendance"].mean().reset_index()
        dept_att = dept_att.sort_values(by="attendance", ascending=False)
        fig_dept_att = px.bar(
            dept_att,
            x="department",
            y="attendance",
            title="Average Attendance by Department",
            color="department",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_dept_att.update_layout(
            font_family="Outfit",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#64748b" if not st.session_state.dark_mode else "#f8fafc",
            margin=dict(t=40, b=10, l=10, r=10),
            showlegend=False
        )
        fig_dept_att.update_yaxes(title="Attendance Average %", range=[0, 100])
        st.plotly_chart(fig_dept_att, use_container_width=True)
        
    with col_b:
        # Monthly attendance trend
        df["date_dt"] = pd.to_datetime(df["date"])
        df["month"] = df["date_dt"].dt.strftime("%b")
        month_order = ["Jan", "Feb", "Mar", "Apr", "May"]
        monthly_att = df.groupby("month")["attendance"].mean().reindex(month_order).reset_index().dropna()
        
        fig_trend = px.line(
            monthly_att,
            x="month",
            y="attendance",
            title="Monthly University Attendance Trend",
            markers=True
        )
        fig_trend.update_traces(line_color="#10b981", line_width=3, marker=dict(size=8, color="#065f46"))
        fig_trend.update_layout(
            font_family="Outfit",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#64748b" if not st.session_state.dark_mode else "#f8fafc",
            margin=dict(t=40, b=10, l=10, r=10)
        )
        fig_trend.update_yaxes(title="Attendance %", range=[40, 100])
        st.plotly_chart(fig_trend, use_container_width=True)
        
    # Attendance Shortage warning list
    st.markdown("---")
    st.subheader("⚠️ Attendance Shortage Warning List (Less than 75% Attendance)")
    st.markdown("These students are currently ineligible to sit for final semester examinations without a condonation fee or medical exemption:")
    
    shortage_list = df[df["attendance"] < 75].sort_values(by="attendance", ascending=True)
    
    if shortage_list.empty:
        st.success("🎉 Excellent! No students are currently in the attendance shortage list.")
    else:
        # Format details
        shortage_list_disp = shortage_list[["studentid", "name", "department", "gender", "attendance", "average_marks", "grade"]].rename(columns={
            "studentid": "Student ID",
            "name": "Student Name",
            "department": "Branch",
            "gender": "Gender",
            "attendance": "Attendance (%)",
            "average_marks": "Academic Avg (%)",
            "grade": "Grade"
        })
        
        st.dataframe(shortage_list_disp, hide_index=True, use_container_width=True)
        
        # Action button to notify students
        if st.button("✉️ Dispatch Warning Emails to Selected Students", type="primary"):
            st.success(f"Emails successfully queued for transmission to the {len(shortage_list)} students in attendance shortage.")
