"""
Lap Record Model - Individual lap data
Follows Salesforce field naming conventions
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class LapRecord:
    """
    Represents a single lap in a session (Salesforce: Lap_Record__c object)
    Master-Detail relationship to Session__c
    """
    # Standard fields
    Id: str = field(default_factory=lambda: str(uuid.uuid4()))
    Name: str = ""  # Auto-generated lap name
    CreatedDate: datetime = field(default_factory=datetime.utcnow)

    # Master-Detail relationship to Session
    Session__c: str = ""  # Foreign key to Session.Id

    # Custom fields
    Lap_Number__c: int = 0
    Lap_Time__c: Optional[float] = None  # Total lap time in milliseconds
    Lap_Valid__c: bool = True  # Whether lap was valid (no track limits, penalties)

    # Sector times
    Sector_1_Time__c: Optional[float] = None
    Sector_2_Time__c: Optional[float] = None
    Sector_3_Time__c: Optional[float] = None

    # Is this the best lap?
    Is_Best_Lap__c: bool = False
    Is_Personal_Best__c: bool = False

    # Position and gaps
    Position__c: Optional[int] = None
    Gap_To_Leader__c: Optional[float] = None  # Seconds

    # Speed data
    Max_Speed__c: Optional[float] = None  # km/h
    Speed_Trap__c: Optional[float] = None

    # Tire and fuel
    Tire_Compound__c: Optional[str] = None
    Tire_Age_Laps__c: Optional[int] = None
    Fuel_Remaining__c: Optional[float] = None

    # Lap completion timestamp
    Lap_Completed_Time__c: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            'Id': self.Id,
            'Name': self.Name,
            'CreatedDate': self.CreatedDate.isoformat() if isinstance(self.CreatedDate, datetime) else self.CreatedDate,
            'Session__c': self.Session__c,
            'Lap_Number__c': self.Lap_Number__c,
            'Lap_Time__c': self.Lap_Time__c,
            'Lap_Valid__c': self.Lap_Valid__c,
            'Sector_1_Time__c': self.Sector_1_Time__c,
            'Sector_2_Time__c': self.Sector_2_Time__c,
            'Sector_3_Time__c': self.Sector_3_Time__c,
            'Is_Best_Lap__c': self.Is_Best_Lap__c,
            'Is_Personal_Best__c': self.Is_Personal_Best__c,
            'Position__c': self.Position__c,
            'Gap_To_Leader__c': self.Gap_To_Leader__c,
            'Max_Speed__c': self.Max_Speed__c,
            'Speed_Trap__c': self.Speed_Trap__c,
            'Tire_Compound__c': self.Tire_Compound__c,
            'Tire_Age_Laps__c': self.Tire_Age_Laps__c,
            'Fuel_Remaining__c': self.Fuel_Remaining__c,
            'Lap_Completed_Time__c': self.Lap_Completed_Time__c.isoformat() if isinstance(self.Lap_Completed_Time__c, datetime) else self.Lap_Completed_Time__c
        }

    @staticmethod
    def from_dict(data: dict) -> 'LapRecord':
        """Create LapRecord from dictionary"""
        for date_field in ['CreatedDate', 'Lap_Completed_Time__c']:
            if data.get(date_field) and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        return LapRecord(**data)
