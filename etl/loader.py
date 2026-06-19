import os
import json
import datetime
import pandas as pd
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from etl.logger import setup_logger

logger = setup_logger("loader")
Base = declarative_base()

class StudentModel(Base):
    """
    SQLAlchemy model for the 'students' table.
    """
    __tablename__ = "students"
    
    studentid = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)
    gender = Column(String(20), nullable=False)
    attendance = Column(Float, nullable=False)
    mid1 = Column(Float, nullable=False)
    mid2 = Column(Float, nullable=False)
    assignment = Column(Float, nullable=False)
    finalmarks = Column(Float, nullable=False)
    average_marks = Column(Float, nullable=False)
    grade = Column(String(5), nullable=False)
    result = Column(String(10), nullable=False)
    date = Column(String(20), nullable=False)

class ETLRunModel(Base):
    """
    SQLAlchemy model for tracking pipeline execution history.
    """
    __tablename__ = "etl_runs"
    
    run_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), nullable=False)
    records_processed = Column(Integer, nullable=False)
    quality_score = Column(Float, nullable=False)
    details = Column(Text, nullable=True)  # Stores JSON string of pipeline quality details

class StudentLoader:
    """
    Handles SQLite database schema initialization and loading of data.
    """
    def __init__(self, db_path="data/etl.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_database(self):
        """
        Creates all tables in the database if they don't exist.
        """
        logger.info("Initializing database schema...")
        Base.metadata.create_all(self.engine)
        logger.info("Database schema initialized successfully.")

    def load(self, df: pd.DataFrame, quality_metrics: dict):
        """
        Clears the student table, inserts the new dataframe, and logs the run metadata.
        
        Args:
            df (pd.DataFrame): Transformed student records.
            quality_metrics (dict): Quality metrics dictionary from transformer.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        self.init_database()
        session = self.Session()
        
        try:
            logger.info("Writing transformed data to 'students' table...")
            
            # Use pandas to write to SQL by replacing table contents for student records
            # Recreating the table via pandas might drop the primary key, so we truncate 
            # the table and use pandas to append. Let's do this to maintain Schema constraints!
            session.query(StudentModel).delete()
            session.commit()
            
            # Write students to SQLite
            df.to_sql(StudentModel.__tablename__, con=self.engine, if_exists="append", index=False)
            logger.info(f"Loaded {len(df)} records into the database.")
            
            # Log ETL Run in database
            run_log = ETLRunModel(
                timestamp=datetime.datetime.now(),
                status="SUCCESS",
                records_processed=len(df),
                quality_score=quality_metrics.get("data_quality_score", 100.0),
                details=json.dumps(quality_metrics)
            )
            session.add(run_log)
            session.commit()
            logger.info("ETL run metadata logged in database.")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to load data to database: {str(e)}")
            
            # Log ETL failure
            try:
                fail_log = ETLRunModel(
                    timestamp=datetime.datetime.now(),
                    status="FAILED",
                    records_processed=0,
                    quality_score=0.0,
                    details=json.dumps({"error": str(e)})
                )
                session.add(fail_log)
                session.commit()
            except Exception as inner_e:
                logger.error(f"Failed to log failure: {str(inner_e)}")
                
            raise e
        finally:
            session.close()
            
    def get_last_run(self):
        """
        Retrieves the last successful ETL run details.
        
        Returns:
            dict or None: Run details if found.
        """
        session = self.Session()
        try:
            inspector = inspect(self.engine)
            if ETLRunModel.__tablename__ not in inspector.get_table_names():
                return None
                
            run = session.query(ETLRunModel).filter_by(status="SUCCESS").order_by(ETLRunModel.timestamp.desc()).first()
            if run:
                return {
                    "timestamp": run.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "records_processed": run.records_processed,
                    "quality_score": run.quality_score,
                    "details": json.loads(run.details) if run.details else {}
                }
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve last run metadata: {str(e)}")
            return None
        finally:
            session.close()
