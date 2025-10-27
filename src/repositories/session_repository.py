"""
Session Repository - Data access for Session__c object
Follows Salesforce SOQL-like query patterns
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from models.session import Session
from repositories.database import get_database

logger = logging.getLogger(__name__)


class SessionRepository:
    """
    Repository for Session__c operations
    Mimics Salesforce Database class methods (insert, update, upsert, query)
    """

    def __init__(self):
        self.db = get_database()

    def insert(self, session: Session) -> Session:
        """
        Insert new session (Salesforce: Database.insert())
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Generate session name (similar to Salesforce auto-number)
            session.Name = self._generate_session_name(session)

            # Convert boolean to int for SQLite
            data = session.to_dict()
            data['Terms_Accepted__c'] = 1 if data['Terms_Accepted__c'] else 0
            data['Safety_Rules_Accepted__c'] = 1 if data['Safety_Rules_Accepted__c'] else 0

            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())

            cursor.execute(
                f"INSERT INTO Session__c ({columns}) VALUES ({placeholders})",
                values
            )

            logger.info(f"Created session: {session.Name} (Id: {session.Id})")
            return session

    def update(self, session: Session) -> Session:
        """
        Update existing session (Salesforce: Database.update())
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            session.LastModifiedDate = datetime.utcnow()
            data = session.to_dict()

            # Convert boolean to int
            data['Terms_Accepted__c'] = 1 if data['Terms_Accepted__c'] else 0
            data['Safety_Rules_Accepted__c'] = 1 if data['Safety_Rules_Accepted__c'] else 0

            # Build UPDATE query
            set_clause = ', '.join([f"{key} = ?" for key in data.keys() if key != 'Id'])
            values = [v for k, v in data.items() if k != 'Id']
            values.append(data['Id'])

            cursor.execute(
                f"UPDATE Session__c SET {set_clause} WHERE Id = ?",
                values
            )

            logger.info(f"Updated session: {session.Name} (Id: {session.Id})")
            return session

    def query(self, where: str = "", params: tuple = (), order_by: str = "",
              limit: Optional[int] = None) -> List[Session]:
        """
        Query sessions (Salesforce: SOQL query)
        Example: query(where="Rig_Number__c = ? AND Session_Status__c = ?",
                       params=(1, 'Active'))
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            sql = "SELECT * FROM Session__c"
            if where:
                sql += f" WHERE {where}"
            if order_by:
                sql += f" ORDER BY {order_by}"
            if limit:
                sql += f" LIMIT {limit}"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            sessions = []
            for row in rows:
                data = dict(row)
                # Convert int back to boolean
                data['Terms_Accepted__c'] = bool(data['Terms_Accepted__c'])
                data['Safety_Rules_Accepted__c'] = bool(data['Safety_Rules_Accepted__c'])
                sessions.append(Session.from_dict(data))

            return sessions

    def get_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        results = self.query(where="Id = ?", params=(session_id,), limit=1)
        return results[0] if results else None

    def get_active_session(self, rig_number: int) -> Optional[Session]:
        """
        Get active session for a rig
        Equivalent to: SELECT Id FROM Session__c WHERE Rig_Number__c = :rigNumber
                       AND Session_Status__c = 'Active' LIMIT 1
        """
        results = self.query(
            where="Rig_Number__c = ? AND Session_Status__c = ?",
            params=(rig_number, "Active"),
            order_by="Session_Start_Time__c DESC",
            limit=1
        )
        return results[0] if results else None

    def get_waiting_session(self, rig_number: int) -> Optional[Session]:
        """Get waiting session for a rig"""
        results = self.query(
            where="Rig_Number__c = ? AND Session_Status__c = ?",
            params=(rig_number, "Waiting"),
            order_by="CreatedDate DESC",
            limit=1
        )
        return results[0] if results else None

    def get_leaderboard_daily(self, track_name: Optional[str] = None,
                             limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get daily leaderboard (best laps from today)
        Returns sessions with best lap times
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            today = datetime.utcnow().date().isoformat()

            sql = """
                SELECT
                    Id,
                    Name,
                    Driver_Name__c,
                    Track_Name__c,
                    Best_Lap_Time__c,
                    Total_Laps__c,
                    Session_Start_Time__c,
                    Rig_Number__c
                FROM Session__c
                WHERE
                    Session_Status__c = 'Completed'
                    AND Best_Lap_Time__c IS NOT NULL
                    AND DATE(Session_Start_Time__c) = ?
            """

            params = [today]

            if track_name:
                sql += " AND Track_Name__c = ?"
                params.append(track_name)

            sql += " ORDER BY Best_Lap_Time__c ASC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_leaderboard_monthly(self, track_name: Optional[str] = None,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get monthly leaderboard (best laps from this month)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # First day of current month
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1).isoformat()

            sql = """
                SELECT
                    Id,
                    Name,
                    Driver_Name__c,
                    Track_Name__c,
                    Best_Lap_Time__c,
                    Total_Laps__c,
                    Session_Start_Time__c,
                    Rig_Number__c
                FROM Session__c
                WHERE
                    Session_Status__c = 'Completed'
                    AND Best_Lap_Time__c IS NOT NULL
                    AND Session_Start_Time__c >= ?
            """

            params = [month_start]

            if track_name:
                sql += " AND Track_Name__c = ?"
                params.append(track_name)

            sql += " ORDER BY Best_Lap_Time__c ASC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_leaderboard_track(self, track_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get all-time track leaderboard
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            sql = """
                SELECT
                    Id,
                    Name,
                    Driver_Name__c,
                    Track_Name__c,
                    Best_Lap_Time__c,
                    Total_Laps__c,
                    Session_Start_Time__c,
                    Rig_Number__c
                FROM Session__c
                WHERE
                    Session_Status__c = 'Completed'
                    AND Best_Lap_Time__c IS NOT NULL
                    AND Track_Name__c = ?
                ORDER BY Best_Lap_Time__c ASC
                LIMIT ?
            """

            cursor.execute(sql, [track_name, limit])
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def _generate_session_name(self, session: Session) -> str:
        """
        Generate session name (Salesforce auto-number pattern)
        Format: SES-YYYYMMDD-RIG{N}-NNNN
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Count sessions today for this rig
            today = datetime.utcnow().date().isoformat()
            cursor.execute(
                """SELECT COUNT(*) FROM Session__c
                   WHERE Rig_Number__c = ? AND DATE(CreatedDate) = ?""",
                (session.Rig_Number__c, today)
            )
            count = cursor.fetchone()[0] + 1

            date_str = datetime.utcnow().strftime("%Y%m%d")
            return f"SES-{date_str}-RIG{session.Rig_Number__c}-{count:04d}"
