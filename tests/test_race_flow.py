#!/usr/bin/env python3
"""
Test script for the Race Flow System
Tests session creation, updates, and leaderboards
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from repositories.database import get_database
from repositories.session_repository import SessionRepository
from services.session_service import get_session_service
from services.calendar_service import get_calendar_service
from models.session import Session


def test_database_creation():
    """Test database initialization"""
    print("🧪 Test 1: Database Creation")
    try:
        db = get_database("data/test_f1_telemetry.db")
        print("✅ Database created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_calendar_service():
    """Test calendar service"""
    print("\n🧪 Test 2: Calendar Service")
    try:
        calendar_service = get_calendar_service()
        summary = calendar_service.get_calendar_summary()

        if summary['loaded']:
            current_race = summary['currentRace']
            print(f"✅ Calendar loaded: {summary['season']} season")
            print(f"   Current race: {current_race['raceName']}")
            print(f"   Track: {current_race['location']}, {current_race['country']}")
            return True
        else:
            print("⚠️  Calendar not loaded (files missing?)")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_session_creation():
    """Test session creation"""
    print("\n🧪 Test 3: Session Creation")
    try:
        session_service = get_session_service()

        # Create a test session
        session = session_service.create_waiting_session(
            rig_number=1,
            driver_name="TestDriver",
            terms_accepted=True,
            safety_accepted=True
        )

        print(f"✅ Session created: {session.Name}")
        print(f"   ID: {session.Id}")
        print(f"   Driver: {session.Driver_Name__c}")
        print(f"   Track: {session.Track_Name__c}")
        print(f"   Race: {session.Race_Name__c}")
        print(f"   Status: {session.Session_Status__c}")

        return session.Id
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None


def test_session_lifecycle(session_id):
    """Test session state transitions"""
    print("\n🧪 Test 4: Session Lifecycle")
    try:
        session_service = get_session_service()

        # Start session
        session = session_service.start_session(session_id)
        print(f"✅ Session started: {session.Session_Status__c}")

        # Simulate some telemetry updates
        telemetry_data = {
            'lapNumber': 5,
            'currentLapTime': 92456,  # 1:32.456
            'sector1Time': 28123,
            'sector2Time': 32234,
            'sector3Time': 32099,
            'speed': 312.5,
            'trackName': 'Monaco'
        }

        session = session_service.update_session_telemetry(session_id, telemetry_data)
        print(f"✅ Telemetry updated:")
        print(f"   Best lap: {session.Best_Lap_Time__c}ms")
        print(f"   Top speed: {session.Top_Speed__c} km/h")

        # Complete session
        session = session_service.complete_session(session_id)
        print(f"✅ Session completed: {session.Session_Status__c}")

        # Get summary
        summary = session_service.get_session_summary(session_id)
        print(f"✅ Summary generated:")
        print(f"   Best lap: {summary['bestLapTimeFormatted']}")
        print(f"   Total laps: {summary['totalLaps']}")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_leaderboards():
    """Test leaderboard queries"""
    print("\n🧪 Test 5: Leaderboards")
    try:
        session_repo = SessionRepository()

        # Daily leaderboard
        daily = session_repo.get_leaderboard_daily(limit=5)
        print(f"✅ Daily leaderboard: {len(daily)} entries")
        if daily:
            top = daily[0]
            print(f"   Top: {top['Driver_Name__c']} - {top['Best_Lap_Time__c']}ms")

        # Monthly leaderboard
        monthly = session_repo.get_leaderboard_monthly(limit=5)
        print(f"✅ Monthly leaderboard: {len(monthly)} entries")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_multiple_sessions():
    """Test multiple sessions and leaderboard ranking"""
    print("\n🧪 Test 6: Multiple Sessions")
    try:
        session_service = get_session_service()

        # Create and complete 3 sessions with different lap times
        drivers = [
            ("Hamilton", 91234),  # 1:31.234
            ("Verstappen", 90987),  # 1:30.987 (fastest)
            ("Leclerc", 91456)  # 1:31.456
        ]

        for driver, lap_time in drivers:
            session = session_service.create_waiting_session(
                rig_number=1,
                driver_name=driver,
                terms_accepted=True,
                safety_accepted=True
            )
            session = session_service.start_session(session.Id)
            session = session_service.update_session_telemetry(session.Id, {
                'lapNumber': 1,
                'currentLapTime': lap_time,
                'speed': 300
            })
            session_service.complete_session(session.Id)

        print(f"✅ Created 3 test sessions")

        # Check leaderboard order
        session_repo = SessionRepository()
        daily = session_repo.get_leaderboard_daily(limit=5)

        print(f"✅ Leaderboard ranking:")
        for i, entry in enumerate(daily[:3], 1):
            lap_time_sec = entry['Best_Lap_Time__c'] / 1000
            minutes = int(lap_time_sec // 60)
            seconds = lap_time_sec % 60
            print(f"   {i}. {entry['Driver_Name__c']}: {minutes}:{seconds:06.3f}")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_db():
    """Remove test database"""
    print("\n🧹 Cleanup: Removing test database")
    try:
        if os.path.exists("data/test_f1_telemetry.db"):
            os.remove("data/test_f1_telemetry.db")
            print("✅ Test database removed")
    except Exception as e:
        print(f"⚠️  Failed to remove test db: {e}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("🏎️  F1 Race Flow System - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Database
    results.append(test_database_creation())

    # Test 2: Calendar
    results.append(test_calendar_service())

    # Test 3: Session creation
    session_id = test_session_creation()
    results.append(session_id is not None)

    # Test 4: Session lifecycle
    if session_id:
        results.append(test_session_lifecycle(session_id))
    else:
        results.append(False)

    # Test 5: Leaderboards
    results.append(test_leaderboards())

    # Test 6: Multiple sessions
    results.append(test_multiple_sessions())

    # Results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)

    if all(results):
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")

    # Cleanup
    cleanup_test_db()

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
