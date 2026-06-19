import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from etl.logger import setup_logger

logger = setup_logger("viz")

def generate_summary_charts(df: pd.DataFrame, output_path="reports/summary.png"):
    """
    Generates high-quality static charts summarizing student performance
    and saves them as a PNG image for the ETL report.
    
    Args:
        df (pd.DataFrame): Cleaned student dataframe.
        output_path (str): Target path to save the chart.
    """
    logger.info(f"Generating summary visualization at {output_path}...")
    
    # Set styling
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'figure.titlesize': 14
    })
    
    # Create subplots: 1 row, 2 columns
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Use clean, premium colors (shades of blue)
    palette = sns.color_palette("Blues_r", n_colors=6)
    
    # 1. Bar Chart: Average Marks by Department
    dept_avg = df.groupby("department")["average_marks"].mean().reset_index()
    dept_avg = dept_avg.sort_values(by="average_marks", ascending=False)
    
    sns.barplot(
        x="department", 
        y="average_marks", 
        data=dept_avg, 
        ax=axes[0], 
        palette="Blues_d",
        hue="department",
        legend=False
    )
    axes[0].set_title("Average Marks by Department", pad=15, fontweight="bold", color="#1a365d")
    axes[0].set_xlabel("Department", fontweight="semibold")
    axes[0].set_ylabel("Average Marks (%)", fontweight="semibold")
    axes[0].set_ylim(0, 100)
    
    # Add labels on top of the bars
    for index, row in dept_avg.iterrows():
        axes[0].text(
            dept_avg.index.get_loc(index), 
            row['average_marks'] + 1, 
            f"{row['average_marks']:.1f}%", 
            color='black', 
            ha="center", 
            va="bottom",
            fontsize=9
        )
        
    # 2. Scatter Plot: Attendance vs Average Marks
    sns.scatterplot(
        x="attendance", 
        y="average_marks", 
        hue="department", 
        palette="tab10",
        data=df, 
        ax=axes[1],
        alpha=0.7,
        edgecolor='w',
        s=40
    )
    axes[1].set_title("Attendance vs Average Marks", pad=15, fontweight="bold", color="#1a365d")
    axes[1].set_xlabel("Attendance (%)", fontweight="semibold")
    axes[1].set_ylabel("Average Marks (%)", fontweight="semibold")
    axes[1].set_xlim(35, 105)
    axes[1].set_ylim(-5, 105)
    axes[1].legend(title="Department", loc="lower right", frameon=True)
    
    plt.suptitle("Cloud-Based Student Performance ETL Pipeline Summary Report", fontweight="bold", y=0.98, color="#0f172a")
    plt.tight_layout()
    
    # Ensure reports directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Summary chart saved successfully at {output_path}")
