import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from theme import load_data

st.markdown("<h1>📈 Academic Performance Analytics</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 14px;'>Performance distributions, exam benchmarks, and support lists</p>", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("⚠️ No data available. Run the ETL pipeline first.")
else:
    # Top Branch Filter
    branches = ["All"] + sorted(df["department"].unique().tolist())
    selected_branch = st.selectbox("Filter Branch", branches, key="perf_branch")
    
    df_perf = df.copy()
    if selected_branch != "All":
        df_perf = df_perf[df_perf["department"] == selected_branch]
        
    # Page layout
    col_l, col_r = st.columns(2)
    
    with col_l:
        # Pass vs Fail distribution
        pf_counts = df_perf.groupby("result").size().reset_index(name="count")
        fig_pf = px.pie(
            pf_counts,
            values="count",
            names="result",
            title="Pass vs Fail Distribution",
            color="result",
            color_discrete_map={"Pass": "#10b981", "Fail": "#ef4444"},
            hole=0.4
        )
        fig_pf.update_layout(
            font_family="Outfit",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#64748b" if not st.session_state.dark_mode else "#f8fafc",
            margin=dict(t=40, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_pf, use_container_width=True)
        
    with col_r:
        # Department Average performance comparison
        dept_perf = df.groupby("department")["average_marks"].mean().reset_index()
        dept_perf = dept_perf.sort_values(by="average_marks", ascending=False)
        fig_dept = px.bar(
            dept_perf,
            y="department",
            x="average_marks",
            title="Overall Branch Marks Benchmarks",
            orientation="h",
            color="department",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_dept.update_layout(
            font_family="Outfit",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#64748b" if not st.session_state.dark_mode else "#f8fafc",
            margin=dict(t=40, b=10, l=10, r=10),
            showlegend=False
        )
        fig_dept.update_xaxes(title="Mean Score (%)", range=[0, 100])
        st.plotly_chart(fig_dept, use_container_width=True)
        
    # Scorers lists grid
    st.markdown("---")
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("### 🌟 Top 5 Outstanding Scorers")
        top_scorers = df_perf.sort_values(by="average_marks", ascending=False).head(5)
        top_scorers = top_scorers[["studentid", "name", "department", "attendance", "average_marks", "grade"]].rename(columns={
            "studentid": "ID", "name": "Name", "department": "Branch", "attendance": "Att. %", "average_marks": "Avg %", "grade": "Grade"
        })
        st.dataframe(top_scorers, hide_index=True, use_container_width=True)
        
    with col_t2:
        st.markdown("### ⚠️ Academic Support Alerts (Bottom 5)")
        need_support = df_perf.sort_values(by="average_marks", ascending=True).head(5)
        need_support = need_support[["studentid", "name", "department", "attendance", "average_marks", "grade"]].rename(columns={
            "studentid": "ID", "name": "Name", "department": "Branch", "attendance": "Att. %", "average_marks": "Avg %", "grade": "Grade"
        })
        st.dataframe(need_support, hide_index=True, use_container_width=True)
        
    # Subject-wise comparison Boxplot
    st.markdown("---")
    st.subheader("Distribution Comparison: Evaluation Components")
    st.markdown("Compare the spread and outlier counts across evaluation marks:")
    
    # Restructure df for component comparison
    df_melted = df_perf.melt(
        id_vars=["studentid", "name", "department"],
        value_vars=["mid1", "mid2", "assignment", "finalmarks"],
        var_name="component",
        value_name="marks"
    )
    # Capitalize component labels
    component_map = {
        "mid1": "Mid-Term 1",
        "mid2": "Mid-Term 2",
        "assignment": "Assignment",
        "finalmarks": "Final Marks"
    }
    df_melted["component"] = df_melted["component"].map(component_map)
    
    fig_box = px.box(
        df_melted,
        x="component",
        y="marks",
        color="component",
        title="Component Score Spread (Box Plot)",
        points="outliers",
        color_discrete_sequence=["#60a5fa", "#3b82f6", "#2563eb", "#1d4ed8"]
    )
    fig_box.update_layout(
        font_family="Outfit",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#64748b" if not st.session_state.dark_mode else "#f8fafc",
        showlegend=False,
        margin=dict(t=40, b=20, l=10, r=10)
    )
    fig_box.update_yaxes(title="Score (Out of 100)")
    fig_box.update_xaxes(title="Assessment Component")
    st.plotly_chart(fig_box, use_container_width=True)
