import pandas as pd
import numpy as np
from etl.logger import setup_logger

logger = setup_logger("transformer")

class StudentTransformer:
    """
    Cleans and transforms student performance data.
    """
    def __init__(self):
        self.quality_metrics = {
            "initial_rows": 0,
            "final_rows": 0,
            "duplicates_removed": 0,
            "nulls_filled": {},
            "data_quality_score": 100.0
        }

    def transform(self, df: pd.DataFrame):
        """
        Cleans column names, handles duplicates, handles missing values,
        formats dates, calculates averages, grades, and results,
        and generates data quality statistics.
        
        Args:
            df (pd.DataFrame): Raw student dataframe.
            
        Returns:
            pd.DataFrame: Transformed dataframe.
            dict: Data quality metrics dictionary.
        """
        logger.info("Starting data transformation pipeline...")
        self.quality_metrics["initial_rows"] = len(df)
        
        # 1. Convert column names to lowercase
        df = df.copy()
        df.columns = df.columns.str.lower()
        logger.info("Converted column names to lowercase.")
        
        # 2. Count and remove duplicate records
        duplicate_count = df.duplicated().sum()
        df = df.drop_duplicates()
        self.quality_metrics["duplicates_removed"] = int(duplicate_count)
        logger.info(f"Removed {duplicate_count} duplicate records.")
        
        # 3. Handle missing values & record counts
        numeric_cols = ["attendance", "mid1", "mid2", "assignment", "finalmarks"]
        null_counts = {}
        
        # Keep track of records with any missing data for quality score
        rows_with_null = df.isnull().any(axis=1).sum()
        
        # Fill missing names with "Unknown Student"
        if "name" in df.columns:
            name_nulls = df["name"].isnull().sum()
            if name_nulls > 0:
                df["name"] = df["name"].fillna("Unknown Student")
                null_counts["name"] = int(name_nulls)
                
        # Fill missing attendance with median attendance
        if "attendance" in df.columns:
            att_nulls = df["attendance"].isnull().sum()
            if att_nulls > 0:
                median_att = df["attendance"].median()
                if pd.isna(median_att):
                    median_att = 75.0
                df["attendance"] = df["attendance"].fillna(round(median_att, 2))
                null_counts["attendance"] = int(att_nulls)
                
        # Fill missing marks with 0
        for col in ["mid1", "mid2", "assignment", "finalmarks"]:
            if col in df.columns:
                col_nulls = df[col].isnull().sum()
                if col_nulls > 0:
                    df[col] = df[col].fillna(0.0)
                    null_counts[col] = int(col_nulls)
                    
        self.quality_metrics["nulls_filled"] = null_counts
        logger.info(f"Handled missing values. Logged fills: {null_counts}")
        
        # 4. Format dates
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            logger.info("Formatted date column to YYYY-MM-DD.")
            
        # 5. Calculate average marks (Weighted average: Mid1: 20%, Mid2: 20%, Assignment: 10%, FinalMarks: 50%)
        # This provides a realistic grading weight
        logger.info("Calculating average marks and assigning grades...")
        df["average_marks"] = (
            df["mid1"] * 0.20 + 
            df["mid2"] * 0.20 + 
            df["assignment"] * 0.10 + 
            df["finalmarks"] * 0.50
        ).round(2)
        
        # 6. Assign letter grades based on the average
        conditions = [
            (df["average_marks"] >= 90),
            (df["average_marks"] >= 80) & (df["average_marks"] < 90),
            (df["average_marks"] >= 70) & (df["average_marks"] < 80),
            (df["average_marks"] >= 60) & (df["average_marks"] < 70),
            (df["average_marks"] >= 50) & (df["average_marks"] < 60),
            (df["average_marks"] < 50)
        ]
        grades = ["A+", "A", "B", "C", "D", "F"]
        df["grade"] = np.select(conditions, grades, default="F")
        
        # 7. Update results based on passing average (>= 50)
        df["result"] = np.where(df["average_marks"] >= 50, "Pass", "Fail")
        
        # 8. Calculate overall data quality score
        self.quality_metrics["final_rows"] = len(df)
        total_issues = duplicate_count + rows_with_null
        if self.quality_metrics["initial_rows"] > 0:
            score = ((self.quality_metrics["initial_rows"] - total_issues) / self.quality_metrics["initial_rows"]) * 100
            self.quality_metrics["data_quality_score"] = max(0.0, round(score, 2))
        else:
            self.quality_metrics["data_quality_score"] = 100.0
            
        logger.info(f"Transformation complete. Data Quality Score: {self.quality_metrics['data_quality_score']}%")
        return df, self.quality_metrics
