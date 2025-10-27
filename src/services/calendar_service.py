"""
F1 Calendar Service
Manages F1 race calendar and determines current/upcoming races
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Service for F1 calendar management
    Auto-selects the next upcoming race based on current date
    """

    def __init__(self, calendar_year: Optional[int] = None):
        """
        Initialize calendar service

        Args:
            calendar_year: Force a specific calendar year (None = auto-detect)
        """
        self.calendar_year = calendar_year
        self.calendar_data: Optional[Dict[str, Any]] = None
        self._load_calendar()

    def _load_calendar(self):
        """Load the appropriate F1 calendar JSON"""
        # Determine which calendar to use
        if self.calendar_year:
            year = self.calendar_year
        else:
            # Auto-detect: Use current year, but if we're in late season and next year
            # calendar is available, prepare for next season
            now = datetime.now()
            year = now.year
            # If we're past November, try next year's calendar
            if now.month >= 11:
                year += 1

        # Try to load the calendar file
        project_root = Path(__file__).parent.parent.parent
        calendar_file = project_root / f"F1-{year%100:02d}-Calendar.json"

        # Fallback to current year if next year not found
        if not calendar_file.exists() and year > datetime.now().year:
            year = datetime.now().year
            calendar_file = project_root / f"F1-{year%100:02d}-Calendar.json"

        if not calendar_file.exists():
            logger.warning(f"Calendar file not found: {calendar_file}")
            self.calendar_data = None
            return

        try:
            with open(calendar_file, 'r') as f:
                self.calendar_data = json.load(f)
            logger.info(f"Loaded F1 {self.calendar_data.get('season')} calendar "
                       f"({self.calendar_data.get('totalRaces')} races)")
        except Exception as e:
            logger.error(f"Failed to load calendar: {e}")
            self.calendar_data = None

    def get_current_race(self) -> Optional[Dict[str, Any]]:
        """
        Get the current or next upcoming race

        Returns:
            Race dictionary with all race details, or None if no calendar loaded
        """
        if not self.calendar_data:
            return None

        races = self.calendar_data.get('races', [])
        now = datetime.now()

        # Find the next race that hasn't ended yet
        for race in races:
            race_end = datetime.fromisoformat(race['endDate'])
            # Add a day buffer - race is "current" until day after it ends
            if race_end + timedelta(days=1) >= now:
                return race

        # If all races are done, return the last race
        return races[-1] if races else None

    def get_next_races(self, count: int = 3) -> List[Dict[str, Any]]:
        """
        Get the next N upcoming races after the current one

        Args:
            count: Number of races to return

        Returns:
            List of race dictionaries
        """
        if not self.calendar_data:
            return []

        races = self.calendar_data.get('races', [])
        current_race = self.get_current_race()

        if not current_race:
            return races[:count]

        # Find current race index
        current_round = current_race['round']

        # Get next races
        next_races = []
        for race in races:
            if race['round'] > current_round:
                next_races.append(race)
                if len(next_races) >= count:
                    break

        return next_races

    def get_race_by_round(self, round_number: int) -> Optional[Dict[str, Any]]:
        """Get race by round number"""
        if not self.calendar_data:
            return None

        races = self.calendar_data.get('races', [])
        for race in races:
            if race['round'] == round_number:
                return race
        return None

    def get_race_by_track(self, track_name: str) -> Optional[Dict[str, Any]]:
        """
        Get race by circuit/track name
        Case-insensitive partial match
        """
        if not self.calendar_data:
            return None

        track_name_lower = track_name.lower()
        races = self.calendar_data.get('races', [])

        for race in races:
            circuit = race.get('circuit', '').lower()
            location = race.get('location', '').lower()

            if track_name_lower in circuit or track_name_lower in location:
                return race

        return None

    def get_calendar_summary(self) -> Dict[str, Any]:
        """
        Get calendar summary for display
        Includes current race, next races, and season info
        """
        if not self.calendar_data:
            return {
                'loaded': False,
                'message': 'No calendar data available'
            }

        current_race = self.get_current_race()
        next_races = self.get_next_races(3)

        return {
            'loaded': True,
            'season': self.calendar_data.get('season'),
            'totalRaces': self.calendar_data.get('totalRaces'),
            'currentRace': current_race,
            'nextRaces': next_races,
            'sprintRaces': self.calendar_data.get('sprintRaces', []),
            'newVenues': self.calendar_data.get('newVenues', [])
        }

    def format_race_display(self, race: Dict[str, Any]) -> str:
        """
        Format race for display
        Example: "Round 8: Monaco Grand Prix (Monaco) - Jun 5-7"
        """
        round_num = race.get('round', '?')
        race_name = race.get('raceName', 'Unknown')
        location = race.get('location', '')
        country = race.get('country', '')

        # Format dates
        start_date = datetime.fromisoformat(race['startDate'])
        end_date = datetime.fromisoformat(race['endDate'])

        date_str = f"{start_date.strftime('%b %d')}-{end_date.strftime('%d')}"

        location_str = f"{location}, {country}" if location != country else country

        sprint_flag = " 🏁" if race.get('hasSprint', False) else ""

        return f"Round {round_num}: {race_name}{sprint_flag} ({location_str}) - {date_str}"


# Singleton instance
_calendar_service: Optional[CalendarService] = None


def get_calendar_service(calendar_year: Optional[int] = None) -> CalendarService:
    """Get or create calendar service singleton"""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarService(calendar_year)
    return _calendar_service
