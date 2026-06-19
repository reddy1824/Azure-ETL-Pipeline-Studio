import os
import pandas as pd
from dotenv import load_dotenv
from etl.logger import setup_logger

load_dotenv()
logger = setup_logger("azure_sql_reader")

class AzureSQLReader:
    """
    Connects to Azure SQL Database to read raw student data.
    Provides mock fallback logic if SQL connections are unavailable.
    """
    def __init__(self):
        self.server = os.getenv("AZURE_SQL_SERVER")
        self.database = os.getenv("AZURE_SQL_DATABASE")
        self.username = os.getenv("AZURE_SQL_USERNAME")
        self.password = os.getenv("AZURE_SQL_PASSWORD")
        self.driver = os.getenv("AZURE_SQL_DRIVER", "{ODBC Driver 18 for SQL Server}")
        
    def get_connection_string(self):
        """
        Builds pyodbc connection string if details are configured.
        """
        if not all([self.server, self.database, self.username, self.password]):
            return None
        return f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

    def read_students_table(self):
        """
        Executes query on Azure SQL Database to retrieve data.
        
        Returns:
            pd.DataFrame or None: Extracted dataframe, or None if failed.
        """
        conn_str = self.get_connection_string()
        if not conn_str:
            logger.warning("Azure SQL Database parameters are not fully configured in environment. Skipping extraction.")
            return None
            
        try:
            import pyodbc
            logger.info(f"Connecting to Azure SQL Server: {self.server}...")
            conn = pyodbc.connect(conn_str)
            query = "SELECT * FROM students_raw"
            df = pd.read_sql(query, conn)
            conn.close()
            logger.info(f"Extracted {len(df)} records from Azure SQL.")
            return df
        except Exception as e:
            logger.error(f"Failed to read from Azure SQL Database: {str(e)}")
            return None
