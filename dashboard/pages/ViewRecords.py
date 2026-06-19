import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from theme import load_data

st.markdown("<h1>📋 Student Academic Records</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 14px;'>Browse and search individual student files, grades, and historical logs.</p>", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("⚠️ No data available. Run the ETL pipeline or upload a dataset first.")
else:
    # Quick filter controls
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        dept_list = ["All"] + sorted(df["department"].unique().tolist())
        sel_dept = st.selectbox("Department Filter", dept_list)
    with col_f2:
        search_name = st.text_input("Search Name / Student ID", placeholder="Search by name or STU...")
        
    df_filtered = df.copy()
    if sel_dept != "All":
        df_filtered = df_filtered[df_filtered["department"] == sel_dept]
        
    if search_name:
        df_filtered = df_filtered[
            df_filtered["name"].str.contains(search_name, case=False) |
            df_filtered["studentid"].str.contains(search_name, case=False)
        ]
        
    # Main records grid
    st.markdown(f"**Showing {len(df_filtered)} student files**")
    st.dataframe(
        df_filtered[["studentid", "name", "department", "gender", "attendance", "average_marks", "grade", "result"]].rename(columns={
            "studentid": "Student ID",
            "name": "Full Name",
            "department": "Department",
            "gender": "Gender",
            "attendance": "Attendance (%)",
            "average_marks": "Weighted Average (%)",
            "grade": "Grade",
            "result": "Result"
        }),
        use_container_width=True
    )
    
    # Detailed profile section
    st.markdown("---")
    st.subheader("🔍 Individual File Inspector")
    
    if not df_filtered.empty:
        selected_student_id = st.selectbox(
            "Select student to inspect details",
            df_filtered["studentid"].tolist()
        )
        
        student_data = df_filtered[df_filtered["studentid"] == selected_student_id].iloc[0]
        
        # Profile details card
        st.markdown(f"""
            <div class="profile-header">
                <div class="profile-pic">{student_data['name'][0]}</div>
                <div class="profile-info" style="flex:1;">
                    <h2>{student_data['name']}</h2>
                    <p>Roll Number: <b>{student_data['studentid']}</b> | Branch: <b>{student_data['department']}</b></p>
                    <p>Status: <span class="badge-result {'pass' if student_data['result'] == 'Pass' else 'fail'}">{student_data['result']}</span> | Grade: <b>{student_data['grade']}</b></p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        tab_scores, tab_att = st.columns(2)
        with tab_scores:
            st.write("**Evaluation Scores**")
            marks_categories = ["Mid-Term 1", "Mid-Term 2", "Assignment", "Final Semester Exam"]
            marks_values = [student_data["mid1"], student_data["mid2"], student_data["assignment"], student_data["finalmarks"]]
            
            fig = go.Figure([go.Bar(x=marks_categories, y=marks_values, text=marks_values, textposition='auto', marker_color='#2563eb')])
            fig.update_layout(height=240, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#64748b' if not st.session_state.dark_mode else '#f8fafc')
            st.plotly_chart(fig, use_container_width=True)
            
        with tab_att:
            st.write("**Attendance Gauge**")
            att = student_data["attendance"]
            gauge_color = "#10b981" if att >= 75 else "#ef4444"
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=att,
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': gauge_color}, 'bgcolor': 'rgba(128,128,128,0.1)'}
            ))
            fig_g.update_layout(height=240, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', font_color='#64748b' if not st.session_state.dark_mode else '#f8fafc')
            st.plotly_chart(fig_g, use_container_width=True)
