"""
Session Model - Represents a single race session
Follows Salesforce field naming conventions (PascalCase with __c suffix for custom fields)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Session:
    """
    Represents a race session (Salesforce: Session__c object)
    """
    # Standard fields (would be standard Salesforce fields)
    Id: str = field(default_factory=lambda: str(uuid.uuid4()))
    Name: str = ""  # Auto-generated session name
    CreatedDate: datetime = field(default_factory=datetime.utcnow)
    LastModifiedDate: datetime = field(default_factory=datetime.utcnow)

    # Custom fields (would have __c suffix in Salesforce)
    Rig_Number__c: int = 1  # 1 = Left Rig, 2 = Right Rig
    Driver_Name__c: str = ""
    Track_Name__c: str = ""
    Circuit_Name__c: str = ""
    Session_Type__c: str = "Race"  # Practice, Qualifying, Race, Time Trial
    Session_Status__c: str = "Waiting"  # Waiting, Active, Completed, Cancelled

    # Race weekend context
    Race_Round__c: Optional[int] = None
    Race_Name__c: str = ""  # e.g., "Monaco Grand Prix"
    Race_Country__c: str = ""
    Race_Date__c: Optional[datetime] = None

    # Session timing
    Session_Start_Time__c: Optional[datetime] = None
    Session_End_Time__c: Optional[datetime] = None
    Session_Duration_Seconds__c: Optional[float] = None

    # Session identifiers from F1 UDP
    UDP_Session_UID__c: Optional[int] = None

    # Performance metrics
    Total_Laps__c: int = 0
    Best_Lap_Time__c: Optional[float] = None  # In milliseconds
    Best_Lap_Number__c: Optional[int] = None

    # Sector times (best)
    Best_Sector_1_Time__c: Optional[float] = None
    Best_Sector_2_Time__c: Optional[float] = None
    Best_Sector_3_Time__c: Optional[float] = None

    # Session statistics
    Average_Lap_Time__c: Optional[float] = None
    Top_Speed__c: Optional[float] = None  # km/h
    Total_Distance__c: Optional[float] = None  # meters

    # Incidents and penalties
    Total_Warnings__c: int = 0
    Total_Penalties__c: int = 0
    Total_Collisions__c: int = 0

    # Flags to track terms acceptance
    Terms_Accepted__c: bool = False
    Safety_Rules_Accepted__c: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            'Id': self.Id,
            'Name': self.Name,
            'CreatedDate': self.CreatedDate.isoformat() if isinstance(self.CreatedDate, datetime) else self.CreatedDate,
            'LastModifiedDate': self.LastModifiedDate.isoformat() if isinstance(self.LastModifiedDate, datetime) else self.LastModifiedDate,
            'Rig_Number__c': self.Rig_Number__c,
            'Driver_Name__c': self.Driver_Name__c,
            'Track_Name__c': self.Track_Name__c,
            'Circuit_Name__c': self.Circuit_Name__c,
            'Session_Type__c': self.Session_Type__c,
            'Session_Status__c': self.Session_Status__c,
            'Race_Round__c': self.Race_Round__c,
            'Race_Name__c': self.Race_Name__c,
            'Race_Country__c': self.Race_Country__c,
            'Race_Date__c': self.Race_Date__c.isoformat() if isinstance(self.Race_Date__c, datetime) else self.Race_Date__c,
            'Session_Start_Time__c': self.Session_Start_Time__c.isoformat() if isinstance(self.Session_Start_Time__c, datetime) else self.Session_Start_Time__c,
            'Session_End_Time__c': self.Session_End_Time__c.isoformat() if isinstance(self.Session_End_Time__c, datetime) else self.Session_End_Time__c,
            'Session_Duration_Seconds__c': self.Session_Duration_Seconds__c,
            'UDP_Session_UID__c': self.UDP_Session_UID__c,
            'Total_Laps__c': self.Total_Laps__c,
            'Best_Lap_Time__c': self.Best_Lap_Time__c,
            'Best_Lap_Number__c': self.Best_Lap_Number__c,
            'Best_Sector_1_Time__c': self.Best_Sector_1_Time__c,
            'Best_Sector_2_Time__c': self.Best_Sector_2_Time__c,
            'Best_Sector_3_Time__c': self.Best_Sector_3_Time__c,
            'Average_Lap_Time__c': self.Average_Lap_Time__c,
            'Top_Speed__c': self.Top_Speed__c,
            'Total_Distance__c': self.Total_Distance__c,
            'Total_Warnings__c': self.Total_Warnings__c,
            'Total_Penalties__c': self.Total_Penalties__c,
            'Total_Collisions__c': self.Total_Collisions__c,
            'Terms_Accepted__c': self.Terms_Accepted__c,
            'Safety_Rules_Accepted__c': self.Safety_Rules_Accepted__c
        }

    @staticmethod
    def from_dict(data: dict) -> 'Session':
        """Create Session from dictionary"""
        # Convert ISO strings back to datetime
        for date_field in ['CreatedDate', 'LastModifiedDate', 'Race_Date__c',
                          'Session_Start_Time__c', 'Session_End_Time__c']:
            if data.get(date_field) and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])

        return Session(**data)
