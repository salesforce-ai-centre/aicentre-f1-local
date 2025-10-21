#!/usr/bin/env python3
"""
Standalone Data Cloud Ingestion Test & Streaming Template

This script tests real-time ingestion to Salesforce Data Cloud using JWT Bearer Flow
with a fallback to Client Credentials Flow. It also serves as a basic template
for streaming data to Data Cloud.

Prerequisites:
1.  A Salesforce Connected App configured for JWT Bearer Flow with the
    'cdp_ingest_api' (and optionally 'api') scope.
2.  The authenticating user (SF_USERNAME) must have:
    a. A Data Cloud license.
    b. A Permission Set granting the "Access Data Cloud Ingestion API"
       system permission.
3.  A .env file with correct Salesforce and Data Cloud configurations.
"""

import os
import time
import json
import requests
import jwt  # PyJWT library
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# Load environment variables from .env file
load_dotenv()

# --- Configuration & Constants ---
# For long-running streaming, consider refreshing the token before it expires.
# Salesforce access tokens from JWT Bearer flow are typically short-lived (e.g., minutes to hours).
# The JWT itself created by this script has a 3-minute expiry.
# The access token obtained from Salesforce might have a longer validity,
# but it's not indefinite.
# For simplicity, this script gets a new token on each run. A real streaming
# app would need to manage the token lifecycle.

# Data Cloud Ingestion API limits:
# - Max 200 records per request.
# - Max 1MB payload size per request.
# Consider these when implementing batching.
MAX_RECORDS_PER_BATCH = 200


# --- JWT and Authentication Functions ---

def create_jwt_token() -> Optional[str]:
    """Create JWT token for Salesforce authentication."""
    try:
        private_key_path: Optional[str] = os.environ.get('SF_PRIVATE_KEY_PATH')
        if not private_key_path or not os.path.exists(private_key_path):
            print(f"❌ Private key file not found at: {private_key_path}")
            print("   Ensure SF_PRIVATE_KEY_PATH is set correctly in .env and the file exists.")
            print("   SECURITY NOTE: Ensure your private key file has restricted permissions (e.g., chmod 600).")
            return None

        with open(private_key_path, 'r') as key_file:
            private_key: str = key_file.read()

        now = int(time.time())
        client_id: Optional[str] = os.environ.get('SF_CLIENT_ID')
        username: Optional[str] = os.environ.get('SF_USERNAME')
        # SF_LOGIN_URL is used for 'aud' claim and Client Credentials token endpoint.
        # For Prod/Dev orgs: https://login.salesforce.com
        # For Sandboxes: https://test.salesforce.com
        login_url_for_aud: Optional[str] = os.environ.get('SF_LOGIN_URL')

        if not all([client_id, username, login_url_for_aud]):
            print("❌ Missing SF_CLIENT_ID, SF_USERNAME, or SF_LOGIN_URL for JWT creation.")
            return None

        payload: Dict[str, Any] = {
            'iss': client_id,
            'sub': username,
            'aud': login_url_for_aud,
            'exp': now + 180,  # JWT expires in 3 minutes
            'iat': now
        }

        print(f"🔧 JWT Payload: {json.dumps(payload, indent=2)}")
        jwt_token: str = jwt.encode(payload, private_key, algorithm='RS256')
        print(f"🔧 JWT Token generated (length: {len(jwt_token)} characters)")
        return jwt_token

    except FileNotFoundError:
        print(f"❌ Error: Private key file not found at '{os.environ.get('SF_PRIVATE_KEY_PATH')}'.")
        return None
    except Exception as e:
        print(f"❌ Error creating JWT: {e}")
        return None

def get_access_token() -> Optional[str]:
    """Get access token using JWT Bearer Flow or Client Credentials Flow."""
    access_token: Optional[str] = None

    print("\n🔐 Attempting JWT Bearer Flow...")
    try:
        jwt_token: Optional[str] = create_jwt_token()
        if jwt_token:
            # SALESFORCE_DOMAIN is your org's My Domain (e.g., mydomain.my.salesforce.com)
            # used for the JWT Bearer token exchange endpoint.
            salesforce_domain_for_token_ep: Optional[str] = os.environ.get('SALESFORCE_DOMAIN')
            if not salesforce_domain_for_token_ep:
                print("❌ SALESFORCE_DOMAIN not set. Cannot construct JWT token endpoint.")
            else:
                auth_url: str = f"https://{salesforce_domain_for_token_ep}/services/oauth2/token"
                auth_data: Dict[str, str] = {
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": jwt_token
                }
                print(f"   Auth URL (JWT): {auth_url}")
                response = requests.post(auth_url, data=auth_data, timeout=20)

                if response.status_code == 200:
                    result: Dict[str, Any] = response.json()
                    access_token = result.get('access_token')
                    print(f"✅ JWT Bearer Flow successful!")
                    print(f"   Scope: {result.get('scope', 'N/A')}")
                    print(f"   Instance URL: {result.get('instance_url', 'N/A')}")
                    return access_token
                else:
                    print(f"❌ JWT Bearer Flow failed: {response.status_code}")
                    try:
                        error_details = response.json()
                        print(f"   Error: {error_details.get('error', 'Unknown error')}")
                        print(f"   Description: {error_details.get('error_description', response.text[:200])}")
                    except json.JSONDecodeError:
                        print(f"   Response (non-JSON): {response.text[:200]}")
    except requests.exceptions.Timeout:
        print("❌ JWT Bearer Flow timed out.")
    except requests.exceptions.RequestException as e:
        print(f"❌ JWT Bearer Flow request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error during JWT Bearer Flow: {e}")

    print("\n🔐 Attempting Client Credentials Flow (fallback)...")
    try:
        client_id: Optional[str] = os.environ.get('SF_CLIENT_ID')
        client_secret: Optional[str] = os.environ.get('SF_CLIENT_SECRET')
        login_url_for_cc: Optional[str] = os.environ.get('SF_LOGIN_URL')

        if not client_id or not client_secret:
            print("ℹ️ SF_CLIENT_ID or SF_CLIENT_SECRET not found. Skipping Client Credentials flow.")
            return None
        if not login_url_for_cc:
            print("ℹ️ SF_LOGIN_URL not found. Skipping Client Credentials flow.")
            return None


        auth_url_cc: str = f"{login_url_for_cc}/services/oauth2/token"
        auth_data_cc: Dict[str, str] = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
            # Optional: Add 'scope' parameter if your CC flow needs specific scopes not default to the app
        }
        print(f"   Auth URL (Client Credentials): {auth_url_cc}")
        response_cc = requests.post(auth_url_cc, data=auth_data_cc, timeout=20)

        if response_cc.status_code == 200:
            result_cc: Dict[str, Any] = response_cc.json()
            access_token = result_cc.get('access_token')
            print(f"✅ Client Credentials Flow successful!")
            print(f"   Scope: {result_cc.get('scope', 'N/A')}")
            return access_token
        else:
            print(f"❌ Client Credentials Flow failed: {response_cc.status_code}")
            try:
                error_details_cc = response_cc.json()
                print(f"   Error: {error_details_cc.get('error', 'Unknown error')}")
                print(f"   Description: {error_details_cc.get('error_description', response_cc.text[:200])}")
            except json.JSONDecodeError:
                print(f"   Response (non-JSON): {response_cc.text[:200]}")
    except requests.exceptions.Timeout:
        print("❌ Client Credentials Flow timed out.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Client Credentials Flow request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error during Client Credentials Flow: {e}")

    if not access_token:
        print("\n❌ All authentication methods failed.")
    return access_token

# --- Data Generation and Ingestion Functions ---

def generate_telemetry_records(count: int = 1) -> List[Dict[str, Any]]:
    """
    Generates a list of sample TelemetryRecord objects.
    Modify this function to generate records matching your actual data and schema.
    The schema used here is based on the F1 TelemetryRecord example.
    """
    records: List[Dict[str, Any]] = []
    base_unique_id = int(time.time())
    for i in range(count):
        now_iso: str = datetime.now(timezone.utc).isoformat()
        # Ensure telemetry_id is unique for each record if it's a primary key.
        unique_record_id: str = f"stream-test-{base_unique_id}-{i}"

        record: Dict[str, Any] = {
            "telemetry_id": unique_record_id,
            "session_id": f"stream-session-{base_unique_id}",
            "timestamp": now_iso,  # Ensure this field is Timestamp type in Data Stream
            "driver_name": f"Stream Driver {i+1}",
            "track_name": "Streaming Test Circuit",
            "frame_id": i + 1000, # Example: make frame_id distinct
            "player_car_index": 0,
            "session_time": float(i * 15.5),
            "last_lap_time_ms": 0,
            "current_lap_time_ms": 15500 + i * 100,
            "lap_number": 1,
            "position": (i % 5) + 1,
            "sector": (i % 3),
            "lap_valid": True,
            "pit_status": 0,
            "speed": 160.0 + (i * 2.5),
            "throttle": 0.75 + (i * 0.01),
            "brake": 0.05 * (i % 2), # Alternating brake
            "steer": 0.05 - (i * 0.005),
            "gear": 5,
            "engine_rpm": 8800 + (i * 50),
            "drs_active": (i % 4 == 0),
            "drs_allowed": True,
            "fuel_in_tank": 22.5 - (i * 0.1),
            "fuel_remaining_laps": 12.2 - (i * 0.05),
            "ers_store_energy": 1.8 + (i * 0.02),
            "ers_deploy_mode": "overtake" if i % 3 == 0 else "balanced",
            "actual_tyre_compound": "medium"
            # Add all other fields from your TelemetryRecord schema here
        }
        records.append(record)
    print(f"ℹ️ Generated {len(records)} sample TelemetryRecord(s).")
    return records

def send_data_to_data_cloud(access_token: str, records_to_send: List[Dict[str, Any]]) -> bool:
    """Sends a batch of records to the configured Data Cloud endpoint."""
    if not records_to_send:
        print("ℹ️ No records provided to send to Data Cloud.")
        return True # Considered success as there's nothing to fail on

    endpoint: Optional[str] = os.environ.get('DC_TELEMETRY_ENDPOINT')
    if not endpoint:
        print("❌ DC_TELEMETRY_ENDPOINT not found in environment variables.")
        return False

    print(f"\n📤 Sending {len(records_to_send)} record(s) to Data Cloud: {endpoint}")

    # Ensure payload adheres to API: {"data": [record1, record2, ...]}
    payload: Dict[str, List[Dict[str, Any]]] = {"data": records_to_send}
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "DataCloud-StreamingTemplate/1.2" # Updated User-Agent
    }

    if len(records_to_send) > 0:
         print(f"   Payload Preview (first record): {json.dumps(records_to_send[0], indent=2)}")

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        print(f"\n📊 Ingestion Response Status: {response.status_code}")

        if response.status_code in [200, 201, 202]: # 202 is common for async Ingestion API
            print("✅ SUCCESS! Data Cloud ingestion API call successful.")
            print(f"   Response: {response.text[:250] if response.text else 'No content'}")
            return True
        # Handle specific error codes with more detail
        elif response.status_code == 400:
            print("❌ 400 Bad Request")
            print("   Issue: Payload malformed, schema mismatch, or incorrect endpoint component.")
            print("   Check: Payload structure, all field names, data types against your Data Stream schema.")
            print(f"   Response: {response.text[:500]}")
        elif response.status_code == 401:
            print("❌ 401 Unauthorized")
            print("   Issue: Access token invalid/expired, or user lacks Data Cloud permissions.")
            print("   Check: ")
            print("     1. Salesforce User (SF_USERNAME) has a Data Cloud license.")
            print("     2. User has a Permission Set with 'Access Data Cloud Ingestion API' system permission.")
            print("     3. Token has 'cdp_ingest_api' scope (verified during auth step).")
            print(f"   Response: {response.text[:250]}")
        elif response.status_code == 403:
            print("❌ 403 Forbidden")
            print("   Issue: Authenticated user lacks specific permission for this Data Stream/action.")
            print(f"   Response: {response.text[:250]}")
        elif response.status_code == 404:
            print("❌ 404 Not Found")
            print("   Issue: DC_TELEMETRY_ENDPOINT URL, Data Stream, or Object name is incorrect.")
            print(f"   Response: {response.text[:250]}")
        else:
            print(f"❌ Unexpected ingestion error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")

        print(f"\n🔍 Response Headers:")
        for header, value in response.headers.items():
            if header.lower() in ['content-type', 'x-request-id', 'sf-request-id', 'date', 'x-cdc-asyncrequestsremaining', 'x-cdc-syncrequestsremaining', 'retry-after']:
                print(f"   {header}: {value}")
        return False

    except requests.exceptions.Timeout:
        print("❌ Data Cloud ingestion request timed out.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Data Cloud ingestion request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during Data Cloud ingestion: {e}")
        return False

# --- Main Execution ---

def main() -> bool:
    """Main test and streaming demonstration function."""
    print("🎯 Standalone Data Cloud Ingestion Test & Streaming Template")
    print("=" * 60)
    print("This script tests Salesforce authentication and sends sample data to Data Cloud.")
    print("Ensure your .env file and Salesforce user permissions are correctly configured.")
    print("-" * 60)

    # --- Environment Variable Setup ---
    # Ensure these are correctly set in your .env file:
    # SF_CLIENT_ID: Your Connected App's Consumer Key.
    # SF_CLIENT_SECRET: Your Connected App's Consumer Secret (for Client Credentials fallback).
    # SF_USERNAME: The Salesforce username for JWT Bearer Flow.
    # SF_LOGIN_URL: 'https://login.salesforce.com' (Prod/Dev) or 'https://test.salesforce.com' (Sandbox). Used for JWT 'aud' & CC token URL.
    # SALESFORCE_DOMAIN: Your org's My Domain (e.g., 'yourdomain.my.salesforce.com'). Used for JWT Bearer token URL.
    # SF_PRIVATE_KEY_PATH: Path to your RSA private key file (e.g., './private.key').
    # DC_TELEMETRY_ENDPOINT: Full Ingestion API URL for your target Data Stream object
    #                        (e.g., 'https://<instance>.c360a.salesforce.com/api/v1/ingest/sources/<ConnectorApiName>/<ObjectName>')
    required_vars: List[str] = [
        'SF_CLIENT_ID', 'SF_USERNAME', 'SF_LOGIN_URL',
        'SALESFORCE_DOMAIN', 'SF_PRIVATE_KEY_PATH', 'DC_TELEMETRY_ENDPOINT'
    ]
    missing_vars: List[str] = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        print(f"❌ Critical Error: Missing environment variables: {', '.join(missing_vars)}")
        print("   Please create or update your .env file with these values.")
        return False

    print("✅ Environment configuration loaded.")
    # Optional: Print loaded vars for verification, be mindful of sensitive data in logs.
    # print(f"   SF_USERNAME: {os.environ.get('SF_USERNAME')}")
    # print(f"   DC_TELEMETRY_ENDPOINT: {os.environ.get('DC_TELEMETRY_ENDPOINT')}")

    # Step 1: Authenticate
    print(f"\n🔑 Step 1: Authentication")
    print("-" * 60)
    access_token: Optional[str] = get_access_token()

    if not access_token:
        # Detailed diagnostics are printed within get_access_token() and by the generic auth failure message below
        print("\n" + "=" * 60)
        print("🔧 AUTHENTICATION DIAGNOSIS (Summary)")
        print("=" * 60)
        print("❌ Authentication failed. Review specific error messages from JWT/Client Credentials attempts above.")
        print("   Common issues: Incorrect .env vars, Connected App setup (scopes, cert, user pre-auth), or system clock.")
        return False
    
    print("\n✅ Authentication successful. Access token obtained.")

    # Step 2: Prepare and Send Data to Data Cloud
    print(f"\n☁️ Step 2: Data Cloud Ingestion")
    print("-" * 60)
    
    # For a real streaming application, you would continuously generate or receive data here.
    # This example sends a small batch of test records.
    # The Ingestion API supports batching (e.g., up to MAX_RECORDS_PER_BATCH).
    # Adapt generate_telemetry_records() to your specific data source and schema.
    sample_records_batch: List[Dict[str, Any]] = generate_telemetry_records(count=3) # Generate a batch of 3 sample records
    
    if not sample_records_batch:
        print("No sample records generated. Skipping ingestion test.")
        ingestion_successful = True # Or False if this should be an error
    else:
        ingestion_successful: bool = send_data_to_data_cloud(access_token, sample_records_batch)
    
    # For a continuous stream, you'd loop here, potentially refreshing the access_token periodically.
    # Example:
    # while True:
    #   if is_token_expired(access_token_obtained_time, access_token_expires_in_seconds):
    #       access_token = get_access_token()
    #       if not access_token: break # Handle auth failure
    #   new_batch = get_next_data_batch()
    #   if not new_batch: break # Or continue if stream ends
    #   send_data_to_data_cloud(access_token, new_batch)
    #   time.sleep(your_streaming_interval)


    # Results
    print(f"\n" + "=" * 60)
    print("🏁 SCRIPT EXECUTION RESULTS")
    print("=" * 60)
    if ingestion_successful and access_token:
        print("✅🏆 SUCCESS: Authentication and Data Cloud ingestion API call(s) were successful.")
        print("   Remember to verify the data appears in your Data Lake Object in Data Cloud.")
        print("   This script can be adapted for continuous data streaming.")
    else:
        print("❌ FAILED: The script encountered issues.")
        if not access_token:
             print("   Primary issue: Authentication failed. See diagnostics above.")
        elif not ingestion_successful:
             print("   Primary issue: Authentication was successful, but the Data Cloud Ingestion API call failed.")
             print("   Review the Ingestion Response details and diagnostics printed earlier.")
             print("\n📋 Key Data Cloud Ingestion Checks (if 401/403 error):")
             print("   1. User Permissions: Ensure SF_USERNAME has:")
             print("      - Data Cloud License assigned.")
             print("      - Permission Set with 'Access Data Cloud Ingestion API' system permission enabled.")
             print("   2. Endpoint & Schema: Verify DC_TELEMETRY_ENDPOINT and payload schema match your Data Stream.")
    
    return ingestion_successful and access_token is not None

if __name__ == "__main__":
    run_success = main()
    if run_success:
        print("\n🎉 Script completed successfully.")
        exit(0)
    else:
        print("\n💔 Script completed with errors.")
        exit(1)