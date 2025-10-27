"""
Session Management Service
Business logic for managing race sessions
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from models.session import Session
from repositories.session_repository import SessionRepository
from services.calendar_service import get_calendar_service

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for session lifecycle management
    Follows Salesforce Apex service class pattern
    """

    def __init__(self):
        self.session_repo = SessionRepository()
        self.calendar_service = get_calendar_service()

        # Track active sessions by rig number
        self._active_sessions: Dict[int, str] = {}  # rig_number -> session_id

    def create_waiting_session(self, rig_number: int, driver_name: str,
                              terms_accepted: bool, safety_accepted: bool,
                              track_override: Optional[str] = None) -> Session:
        """
        Create a new session in 'Waiting' status
        Auto-populates race context from calendar

        Args:
            rig_number: 1 (Left) or 2 (Right)
            driver_name: Driver nickname
            terms_accepted: Terms and conditions accepted
            safety_accepted: Safety rules accepted
            track_override: Optional track name override (otherwise uses calendar)

        Returns:
            Created Session object
        """
        # Get race context from calendar
        race_context = {}
        if track_override:
            # Try to find this track in the calendar
            race = self.calendar_service.get_race_by_track(track_override)
            if race:
                race_context = self._extract_race_context(race)
        else:
            # Use current/next race from calendar
            current_race = self.calendar_service.get_current_race()
            if current_race:
                race_context = self._extract_race_context(current_race)

        # Create session
        session = Session(
            Rig_Number__c=rig_number,
            Driver_Name__c=driver_name,
            Session_Status__c="Waiting",
            Terms_Accepted__c=terms_accepted,
            Safety_Rules_Accepted__c=safety_accepted,
            **race_context
        )

        # Save to database
        return self.session_repo.insert(session)

    def start_session(self, session_id: str, udp_session_uid: Optional[int] = None) -> Session:
        """
        Start a session (transition from Waiting to Active)

        Args:
            session_id: Session ID to start
            udp_session_uid: Optional UDP session UID from F1 game

        Returns:
            Updated Session object
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.Session_Status__c == "Active":
            logger.warning(f"Session {session_id} is already active")
            return session

        # Update session
        session.Session_Status__c = "Active"
        session.Session_Start_Time__c = datetime.utcnow()

        if udp_session_uid:
            session.UDP_Session_UID__c = udp_session_uid

        # Track as active session
        self._active_sessions[session.Rig_Number__c] = session_id

        return self.session_repo.update(session)

    def complete_session(self, session_id: str) -> Session:
        """
        Complete a session (transition to Completed)
        Calculates final statistics

        Args:
            session_id: Session ID to complete

        Returns:
            Updated Session object
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Update session
        session.Session_Status__c = "Completed"
        session.Session_End_Time__c = datetime.utcnow()

        # Calculate duration
        if session.Session_Start_Time__c:
            duration = session.Session_End_Time__c - session.Session_Start_Time__c
            session.Session_Duration_Seconds__c = duration.total_seconds()

        # Remove from active tracking
        if session.Rig_Number__c in self._active_sessions:
            del self._active_sessions[session.Rig_Number__c]

        return self.session_repo.update(session)

    def update_session_telemetry(self, session_id: str, telemetry_data: Dict[str, Any]) -> Session:
        """
        Update session with telemetry data
        Called periodically during active session

        Args:
            session_id: Session ID
            telemetry_data: Telemetry payload from receiver

        Returns:
            Updated Session object
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Update lap count
        lap_number = telemetry_data.get('lapNumber', 0)
        if lap_number > session.Total_Laps__c:
            session.Total_Laps__c = lap_number

        # Update best lap time
        current_lap_time = telemetry_data.get('currentLapTime')
        if current_lap_time and (not session.Best_Lap_Time__c or
                                 current_lap_time < session.Best_Lap_Time__c):
            session.Best_Lap_Time__c = current_lap_time
            session.Best_Lap_Number__c = lap_number

        # Update sector times
        sector1 = telemetry_data.get('sector1Time')
        sector2 = telemetry_data.get('sector2Time')
        sector3 = telemetry_data.get('sector3Time')

        if sector1 and (not session.Best_Sector_1_Time__c or
                       sector1 < session.Best_Sector_1_Time__c):
            session.Best_Sector_1_Time__c = sector1

        if sector2 and (not session.Best_Sector_2_Time__c or
                       sector2 < session.Best_Sector_2_Time__c):
            session.Best_Sector_2_Time__c = sector2

        if sector3 and (not session.Best_Sector_3_Time__c or
                       sector3 < session.Best_Sector_3_Time__c):
            session.Best_Sector_3_Time__c = sector3

        # Update top speed
        speed = telemetry_data.get('speed')
        if speed and (not session.Top_Speed__c or speed > session.Top_Speed__c):
            session.Top_Speed__c = speed

        # Update track name if not set
        if not session.Track_Name__c:
            track_name = telemetry_data.get('trackName')
            if track_name:
                session.Track_Name__c = track_name

        return self.session_repo.update(session)

    def get_active_session_for_rig(self, rig_number: int) -> Optional[Session]:
        """Get the active session for a rig"""
        return self.session_repo.get_active_session(rig_number)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get session summary for post-race display

        Returns:
            Dictionary with formatted session statistics
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            return {'error': 'Session not found'}

        # Format best lap time
        best_lap_formatted = None
        if session.Best_Lap_Time__c:
            best_lap_formatted = self._format_lap_time(session.Best_Lap_Time__c)

        # Format sector times
        sector_times = []
        for i, sector_time in enumerate([session.Best_Sector_1_Time__c,
                                        session.Best_Sector_2_Time__c,
                                        session.Best_Sector_3_Time__c], 1):
            if sector_time:
                sector_times.append({
                    'sector': i,
                    'time': sector_time,
                    'formatted': self._format_lap_time(sector_time)
                })

        return {
            'sessionId': session.Id,
            'sessionName': session.Name,
            'driverName': session.Driver_Name__c,
            'rigNumber': session.Rig_Number__c,
            'trackName': session.Track_Name__c,
            'raceName': session.Race_Name__c,
            'totalLaps': session.Total_Laps__c,
            'bestLapTime': session.Best_Lap_Time__c,
            'bestLapTimeFormatted': best_lap_formatted,
            'bestLapNumber': session.Best_Lap_Number__c,
            'sectorTimes': sector_times,
            'topSpeed': session.Top_Speed__c,
            'duration': session.Session_Duration_Seconds__c,
            'startTime': session.Session_Start_Time__c.isoformat() if session.Session_Start_Time__c else None,
            'endTime': session.Session_End_Time__c.isoformat() if session.Session_End_Time__c else None
        }

    def _extract_race_context(self, race: Dict[str, Any]) -> Dict[str, str]:
        """Extract race context from calendar race entry"""
        return {
            'Race_Round__c': race.get('round'),
            'Race_Name__c': race.get('raceName', ''),
            'Race_Country__c': race.get('country', ''),
            'Track_Name__c': race.get('location', ''),
            'Circuit_Name__c': race.get('circuit', ''),
            'Race_Date__c': datetime.fromisoformat(race['startDate']) if 'startDate' in race else None
        }

    def _format_lap_time(self, milliseconds: float) -> str:
        """
        Format lap time from milliseconds to M:SS.mmm

        Args:
            milliseconds: Time in milliseconds

        Returns:
            Formatted string like "1:32.456"
        """
        total_seconds = milliseconds / 1000.0
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:06.3f}"


# Singleton instance
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """Get or create session service singleton"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
