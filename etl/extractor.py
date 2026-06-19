import os
import random
import datetime
import pandas as pd
from etl.logger import setup_logger

logger = setup_logger("extractor")

def generate_mock_data(filepath, count=500):
    """
    Generates a realistic student dataset with correlated attendance and marks,
    saving it as a CSV.
    
    Args:
        filepath (str): Target path to save the CSV.
        count (int): Number of records to generate.
    """
    logger.info(f"Generating {count} mock student records...")
    
    first_names_m = ["Rahul", "Amit", "Vijay", "Rajesh", "Sanjay", "Anil", "Arjun", "Deepak", "Aditya", "Rohan", "Vikram", "Karan", "Sunil", "Manish", "Abhishek", "Vivek"]
    first_names_f = ["Priya", "Neha", "Anjali", "Sneha", "Pooja", "Divya", "Kiran", "Shalini", "Ritu", "Swati", "Aishwarya", "Preeti", "Tanvi", "Meera", "Kriti", "Riya"]
    last_names = ["Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Joshi", "Mehta", "Reddy", "Nair", "Rao", "Das", "Choudhury", "Mishra", "Pandey", "Sen"]
    
    departments = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "IT"]
    genders = ["Male", "Female"]
    
    data = []
    start_date = datetime.date(2025, 1, 1)
    
    for i in range(count):
        student_id = f"STU{1000 + i}"
        gender = random.choice(genders)
        if gender == "Male":
            first_name = random.choice(first_names_m)
        else:
            first_name = random.choice(first_names_f)
        last_name = random.choice(last_names)
        name = f"{first_name} {last_name}"
        
        dept = random.choice(departments)
        
        # Correlated attendance: average around 78%
        attendance = round(random.triangular(40, 100, 78), 2)
        
        # Correlate marks with attendance (higher attendance -> higher marks on average)
        base_factor = attendance / 100.0  # 0.4 to 1.0
        
        # Generate raw marks out of 100
        mid1 = round(min(100, max(0, random.normalvariate(60 + base_factor * 20, 12))), 2)
        mid2 = round(min(100, max(0, random.normalvariate(62 + base_factor * 18, 12))), 2)
        assignment = round(min(100, max(0, random.normalvariate(70 + base_factor * 15, 8))), 2)
        final_marks = round(min(100, max(0, random.normalvariate(58 + base_factor * 25, 15))), 2)
        
        # Introduce a few nulls or anomalous values for data quality demonstration
        # (approx 2% chance of missing/corrupt values)
        if random.random() < 0.02:
            mid1 = None
        if random.random() < 0.01:
            name = name.upper()  # duplicates or case inconsistencies
        if random.random() < 0.01:
            attendance = None
            
        # Basic result calculation
        valid_marks = [m for m in [mid1, mid2, assignment, final_marks] if m is not None]
        avg_marks = sum(valid_marks) / len(valid_marks) if valid_marks else 0
        result = "Pass" if avg_marks >= 50 else "Fail"
        
        # Add random date in the semester (Jan to May 2025)
        random_days = random.randint(0, 135)
        record_date = (start_date + datetime.timedelta(days=random_days)).strftime("%Y-%m-%d")
        
        data.append({
            "StudentID": student_id,
            "Name": name,
            "Department": dept,
            "Gender": gender,
            "Attendance": attendance,
            "Mid1": mid1,
            "Mid2": mid2,
            "Assignment": assignment,
            "FinalMarks": final_marks,
            "Result": result,
            "Date": record_date
        })
        
    # Introduce some exact duplicates for duplicate cleaning demonstration
    duplicate_indices = random.sample(range(count), 5)
    for idx in duplicate_indices:
        dup = data[idx].copy()
        data.append(dup)
        
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Mock dataset generated successfully at {filepath}")

class StudentExtractor:
    """
    Handles data extraction from CSV or Azure SQL Database.
    """
    def __init__(self, csv_path="data/student_data.csv"):
        self.csv_path = csv_path
        
    def extract_from_csv(self):
        """
        Reads student data from local CSV file. Generates mock data if file not found.
        
        Returns:
            pd.DataFrame: Extracted dataset.
        """
        logger.info(f"Starting extraction from CSV: {self.csv_path}")
        if not os.path.exists(self.csv_path):
            logger.warning(f"CSV file not found. Generating mock data at {self.csv_path}")
            generate_mock_data(self.csv_path)
            
        try:
            df = pd.read_csv(self.csv_path)
            logger.info(f"Extracted {len(df)} records from CSV.")
            return df
        except Exception as e:
            logger.error(f"Failed to extract from CSV: {str(e)}")
            raise e

    def extract_from_azure_sql(self, connection_string=None):
        """
        Extracts student data from Azure SQL Database. Fallback to CSV if details missing.
        
        Args:
            connection_string (str, optional): Connection string.
            
        Returns:
            pd.DataFrame: Extracted dataset.
        """
        logger.info("Attempting extraction from Azure SQL Database...")
        if not connection_string:
            logger.warning("Azure SQL connection string not provided. Falling back to CSV extraction.")
            return self.extract_from_csv()
            
        try:
            import pyodbc
            conn = pyodbc.connect(connection_string)
            query = "SELECT * FROM Students"
            df = pd.read_sql(query, conn)
            logger.info(f"Extracted {len(df)} records from Azure SQL.")
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Azure SQL Extraction failed: {str(e)}. Falling back to CSV.")
            return self.extract_from_csv()
            
    def run(self, source_type="CSV", connection_string=None):
        """
        Runs the extraction process.
        
        Args:
            source_type (str): 'CSV' or 'AzureSQL'.
            connection_string (str, optional): Connection string.
            
        Returns:
            pd.DataFrame: The raw extracted dataframe.
        """
        if source_type.upper() == "AZURESQL":
            return self.extract_from_azure_sql(connection_string)
        else:
            return self.extract_from_csv()
