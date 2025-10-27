"""
Database connection and initialization
SQLite implementation designed for easy migration to Salesforce
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """
    Database manager following Salesforce object model patterns
    Uses SQLite locally, designed for future Salesforce migration
    """

    def __init__(self, db_path: str = "data/f1_telemetry.db"):
        """Initialize database connection"""
        self.db_path = db_path

        # Ensure data directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_database()

    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Session__c table (equivalent to Salesforce custom object)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Session__c (
                    Id TEXT PRIMARY KEY,
                    Name TEXT NOT NULL,
                    CreatedDate TEXT NOT NULL,
                    LastModifiedDate TEXT NOT NULL,

                    -- Custom fields
                    Rig_Number__c INTEGER NOT NULL,
                    Driver_Name__c TEXT NOT NULL,
                    Track_Name__c TEXT,
                    Circuit_Name__c TEXT,
                    Session_Type__c TEXT DEFAULT 'Race',
                    Session_Status__c TEXT DEFAULT 'Waiting',

                    -- Race context
                    Race_Round__c INTEGER,
                    Race_Name__c TEXT,
                    Race_Country__c TEXT,
                    Race_Date__c TEXT,

                    -- Timing
                    Session_Start_Time__c TEXT,
                    Session_End_Time__c TEXT,
                    Session_Duration_Seconds__c REAL,

                    -- UDP identifier
                    UDP_Session_UID__c INTEGER,

                    -- Performance
                    Total_Laps__c INTEGER DEFAULT 0,
                    Best_Lap_Time__c REAL,
                    Best_Lap_Number__c INTEGER,
                    Best_Sector_1_Time__c REAL,
                    Best_Sector_2_Time__c REAL,
                    Best_Sector_3_Time__c REAL,
                    Average_Lap_Time__c REAL,
                    Top_Speed__c REAL,
                    Total_Distance__c REAL,

                    -- Incidents
                    Total_Warnings__c INTEGER DEFAULT 0,
                    Total_Penalties__c INTEGER DEFAULT 0,
                    Total_Collisions__c INTEGER DEFAULT 0,

                    -- Terms
                    Terms_Accepted__c INTEGER DEFAULT 0,
                    Safety_Rules_Accepted__c INTEGER DEFAULT 0
                )
            """)

            # Lap_Record__c table (child object with Master-Detail relationship)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Lap_Record__c (
                    Id TEXT PRIMARY KEY,
                    Name TEXT NOT NULL,
                    CreatedDate TEXT NOT NULL,

                    -- Master-Detail relationship (foreign key)
                    Session__c TEXT NOT NULL,

                    -- Lap data
                    Lap_Number__c INTEGER NOT NULL,
                    Lap_Time__c REAL,
                    Lap_Valid__c INTEGER DEFAULT 1,

                    -- Sector times
                    Sector_1_Time__c REAL,
                    Sector_2_Time__c REAL,
                    Sector_3_Time__c REAL,

                    -- Best lap flags
                    Is_Best_Lap__c INTEGER DEFAULT 0,
                    Is_Personal_Best__c INTEGER DEFAULT 0,

                    -- Position
                    Position__c INTEGER,
                    Gap_To_Leader__c REAL,

                    -- Speed
                    Max_Speed__c REAL,
                    Speed_Trap__c REAL,

                    -- Tire and fuel
                    Tire_Compound__c TEXT,
                    Tire_Age_Laps__c INTEGER,
                    Fuel_Remaining__c REAL,

                    -- Timestamp
                    Lap_Completed_Time__c TEXT,

                    -- Foreign key constraint (Salesforce Master-Detail cascade delete)
                    FOREIGN KEY (Session__c) REFERENCES Session__c(Id) ON DELETE CASCADE
                )
            """)

            # Create indexes for common queries (similar to Salesforce indexes)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_status
                ON Session__c(Session_Status__c)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_rig_date
                ON Session__c(Rig_Number__c, CreatedDate)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_track_date
                ON Session__c(Track_Name__c, CreatedDate)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lap_session
                ON Lap_Record__c(Session__c)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_best_laps
                ON Lap_Record__c(Is_Best_Lap__c, Lap_Time__c)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        Similar to Salesforce transaction management
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            conn.close()

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None


# Singleton instance
_db_instance: Optional[Database] = None


def get_database(db_path: str = "data/f1_telemetry.db") -> Database:
    """Get or create database singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance
