"""
Data Cloud Integration for F1 Telemetry
Sends telemetry data to Salesforce Data Cloud via Ingestion API
"""

import json
import time
import requests
import logging
import jwt
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import uuid


class DataCloudClient:
    """Client for sending F1 telemetry data to Salesforce Data Cloud"""
    
    def __init__(self, 
                 salesforce_domain: str,
                 client_id: str, 
                 private_key_path: str,
                 username: str,
                 stream_endpoints: Dict[str, str],
                 debug: bool = False):
        """
        Initialize Data Cloud client
        
        Args:
            salesforce_domain: Your Salesforce domain (e.g., "myorg.my.salesforce.com")
            client_id: Connected App Client ID (Consumer Key)
            private_key_path: Path to private.key file for JWT signing
            username: Salesforce username for JWT authentication
            stream_endpoints: Dict mapping stream names to their API endpoints
            debug: Enable debug logging
        """
        self.salesforce_domain = salesforce_domain
        self.client_id = client_id
        self.private_key_path = private_key_path
        self.username = username
        self.stream_endpoints = stream_endpoints
        self.debug = debug
        
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        
        # Batch settings for efficient data transfer - smaller batches for better reliability
        self.batch_size = 10  # Reduced from 100 to avoid rate limits
        self.batch_timeout = 2.0  # Reduced from 5.0 for faster response
        self.pending_records: Dict[str, List[Dict]] = {
            'telemetry': [],
            'events': [],
            'sessions': [],
            'participants': [],
            'motion': []
        }
        self.last_batch_time = time.time()
        
    def authenticate(self) -> bool:
        """Get OAuth access token using JWT Bearer Flow"""
        try:
            # Check if we have a valid cached token
            current_time = time.time()
            if self.access_token and current_time < self.token_expires_at - 60:
                return True
            
            # Try Data Cloud-specific JWT authentication first
            dc_domain = None
            for endpoint in self.stream_endpoints.values():
                if endpoint and '.c360a.salesforce.com' in endpoint:
                    dc_domain = endpoint.split('/')[2]
                    break
            
            if dc_domain:
                if self.debug:
                    logging.info(f"Attempting Data Cloud JWT authentication for domain: {dc_domain}")
                
                # Create JWT token with Data Cloud domain as audience
                dc_jwt_token = self._create_datacloud_jwt()
                if dc_jwt_token:
                    dc_auth_urls = [
                        f"https://{dc_domain}/services/oauth2/token",
                        f"https://{self.salesforce_domain}/services/oauth2/token"
                    ]
                    
                    auth_data = {
                        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                        "assertion": dc_jwt_token
                    }
                    
                    headers = {
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                    
                    for auth_url in dc_auth_urls:
                        if self.debug:
                            logging.info(f"Requesting Data Cloud access token from {auth_url}")
                            logging.info(f"JWT assertion length: {len(dc_jwt_token)}")
                        
                        try:
                            response = requests.post(auth_url, data=auth_data, headers=headers, timeout=10)
                            
                            if response.status_code == 200:
                                result = response.json()
                                self.access_token = result.get("access_token")
                                expires_in = result.get("expires_in", 3600)
                                self.token_expires_at = current_time + expires_in
                                
                                if self.debug:
                                    logging.info(f"Data Cloud JWT authentication successful from {auth_url}, expires in {expires_in}s")
                                    logging.info(f"Instance URL: {result.get('instance_url', 'N/A')}")
                                    logging.info(f"Token scope: {result.get('scope', 'N/A')}")
                                    logging.info(f"Access token (first 50 chars): {self.access_token[:50]}...")
                                return True
                            else:
                                if self.debug:
                                    logging.debug(f"Data Cloud authentication failed at {auth_url}: {response.status_code}")
                        except Exception as e:
                            if self.debug:
                                logging.debug(f"Data Cloud authentication error at {auth_url}: {e}")
            
            # Fallback to standard Salesforce authentication
            if self.debug:
                logging.info("Data Cloud authentication failed, falling back to standard Salesforce authentication")
            
            # Create JWT token
            jwt_token = self._create_jwt()
            if not jwt_token:
                return False
            
            # Use standard Salesforce authentication endpoints
            auth_urls = [
                f"https://{self.salesforce_domain}/services/oauth2/token",
                "https://login.salesforce.com/services/oauth2/token"
            ]
            
            auth_data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Try each authentication URL until one works
            for auth_url in auth_urls:
                if self.debug:
                    logging.info(f"Requesting access token from {auth_url}")
                    logging.info(f"JWT assertion length: {len(jwt_token)}")
                
                response = requests.post(auth_url, data=auth_data, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    self.access_token = result.get("access_token")
                    expires_in = result.get("expires_in", 3600)
                    self.token_expires_at = current_time + expires_in
                    
                    if self.debug:
                        logging.info(f"JWT authentication successful from {auth_url}, expires in {expires_in}s")
                        logging.info(f"Instance URL: {result.get('instance_url', 'N/A')}")
                        logging.info(f"Token scope: {result.get('scope', 'N/A')}")
                        logging.info(f"Access token (first 50 chars): {self.access_token[:50]}...")
                    
                    # CRITICAL: Data Cloud requires token exchange - cannot use Salesforce token directly
                    if self.debug:
                        logging.info("Exchanging Salesforce token for Data Cloud-specific token")
                    
                    # Attempt to exchange Salesforce token for Data Cloud token
                    if self._exchange_for_datacloud_token(self.access_token):
                        if self.debug:
                            logging.info("Data Cloud token exchange successful")
                        return True
                    else:
                        if self.debug:
                            logging.warning("Data Cloud token exchange failed, using Salesforce token as fallback")
                        # Continue with Salesforce token as fallback
                        return True
                else:
                    if self.debug:
                        logging.debug(f"Authentication failed at {auth_url}: {response.status_code}")
            
            logging.error(f"All JWT authentication attempts failed")
            return False
                
        except Exception as e:
            logging.error(f"Error authenticating with Data Cloud: {e}", exc_info=True)
            return False
    
    def _create_jwt(self) -> Optional[str]:
        """Create JWT token for authentication"""
        try:
            # Load private key
            if not os.path.exists(self.private_key_path):
                logging.error(f"Private key file not found: {self.private_key_path}")
                return None
            
            with open(self.private_key_path, 'r') as key_file:
                private_key = key_file.read()
            
            # Create JWT payload
            now = int(time.time())
            
            payload = {
                'iss': self.client_id,  # Consumer Key from Connected App
                'sub': self.username,   # Salesforce username
                'aud': 'https://login.salesforce.com',  # Standard Salesforce audience
                'exp': now + 300,       # Expires in 5 minutes
                'iat': now              # Issued at
            }
            
            if self.debug:
                logging.info(f"Creating JWT with payload: {payload}")
            
            # Sign JWT with private key
            jwt_token = jwt.encode(
                payload,
                private_key,
                algorithm='RS256'
            )
            
            return jwt_token
            
        except Exception as e:
            logging.error(f"Error creating JWT: {e}", exc_info=True)
            return None
    
    def _exchange_for_datacloud_token(self, salesforce_token: str) -> bool:
        """Exchange Salesforce access token for Data Cloud-specific JWT token"""
        try:
            # Extract Data Cloud domain from ingestion endpoints
            dc_domain = None
            for endpoint in self.stream_endpoints.values():
                if endpoint and '.c360a.salesforce.com' in endpoint:
                    dc_domain = endpoint.split('/')[2]
                    break
            
            if not dc_domain:
                logging.error("Could not determine Data Cloud domain from endpoints")
                return False
            
            # Modern Data Cloud token exchange endpoints (2024-2025)
            exchange_endpoints = [
                f"https://{self.salesforce_domain}/services/oauth2/token",  # Use Salesforce domain for exchange
                f"https://{dc_domain}/services/oauth2/token"  # Direct Data Cloud exchange
            ]
            
            # OAuth 2.0 Token Exchange flow for Data Cloud
            exchange_data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": salesforce_token,
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "audience": f"https://{dc_domain}",  # Target Data Cloud audience
                "scope": "cdp_ingest_api"  # Specific Data Cloud scope
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Bearer {salesforce_token}"
            }
            
            for exchange_url in exchange_endpoints:
                if self.debug:
                    logging.info(f"Attempting Data Cloud token exchange at {exchange_url}")
                    logging.info(f"Target audience: https://{dc_domain}")
                
                try:
                    response = requests.post(exchange_url, data=exchange_data, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.access_token = result.get("access_token")  # Replace with Data Cloud JWT
                        expires_in = result.get("expires_in", 3600)
                        current_time = time.time()
                        self.token_expires_at = current_time + expires_in
                        
                        if self.debug:
                            logging.info(f"✅ Data Cloud token exchange successful!")
                            logging.info(f"Exchange endpoint: {exchange_url}")
                            logging.info(f"New token expires in: {expires_in}s")
                            logging.info(f"Token type: {result.get('token_type', 'Bearer')}")
                            logging.info(f"Data Cloud token (first 50 chars): {self.access_token[:50]}...")
                        return True
                    else:
                        if self.debug:
                            logging.debug(f"Token exchange failed at {exchange_url}: {response.status_code}")
                            logging.debug(f"Response: {response.text[:200]}")
                            
                except Exception as e:
                    if self.debug:
                        logging.debug(f"Token exchange error at {exchange_url}: {e}")
                    continue
            
            if self.debug:
                logging.warning("All Data Cloud token exchange attempts failed")
            return False
                
        except Exception as e:
            logging.error(f"Error in Data Cloud token exchange: {e}", exc_info=True)
            return False
    
    def _create_datacloud_jwt(self) -> Optional[str]:
        """Create JWT token specifically for Data Cloud authentication"""
        try:
            # Load private key
            if not os.path.exists(self.private_key_path):
                logging.error(f"Private key file not found: {self.private_key_path}")
                return None
            
            with open(self.private_key_path, 'r') as key_file:
                private_key = key_file.read()
            
            # Extract Data Cloud domain for audience
            dc_domain = None
            for endpoint in self.stream_endpoints.values():
                if endpoint and '.c360a.salesforce.com' in endpoint:
                    dc_domain = endpoint.split('/')[2]
                    break
            
            if not dc_domain:
                logging.error("Could not determine Data Cloud domain for JWT audience")
                return None
            
            # Create JWT payload for Data Cloud with tenant-specific audience
            now = int(time.time())
            
            # CRITICAL: Use the Data Cloud tenant endpoint as audience for proper authentication
            payload = {
                'iss': self.client_id,  # Consumer Key from Connected App
                'sub': self.username,   # Salesforce username  
                'aud': f"https://{dc_domain}",  # Data Cloud tenant endpoint as audience
                'exp': now + 300,       # Expires in 5 minutes
                'iat': now,             # Issued at
                'nbf': now              # Not before (additional security)
            }
            
            if self.debug:
                logging.info(f"Creating Data Cloud JWT with tenant audience: {payload}")
            
            # Sign the JWT with RS256 algorithm
            jwt_token = jwt.encode(
                payload,
                private_key,
                algorithm='RS256'
            )
            
            return jwt_token
            
        except Exception as e:
            logging.error(f"Error creating Data Cloud JWT: {e}", exc_info=True)
            return None
    
    def _try_salesforce_datacloud_endpoints(self):
        """This method is no longer needed - using original endpoints"""
        pass
    
    def send_telemetry_record(self, telemetry_data: Dict[str, Any]):
        """Add telemetry record to batch for sending to Data Cloud"""
        if not self.authenticate():
            raise Exception("401 - Data Cloud authentication failed")
            
        # Transform the payload to match Data Cloud schema
        record = self._transform_telemetry_record(telemetry_data)
        self.pending_records['telemetry'].append(record)
        
        # Send batch if we've reached the batch size or timeout
        if (len(self.pending_records['telemetry']) >= self.batch_size or 
            time.time() - self.last_batch_time >= self.batch_timeout):
            self._flush_telemetry_batch()
    
    def send_race_event(self, event_data: Dict[str, Any]):
        """Send race event to Data Cloud"""
        if not self.authenticate():
            return False
            
        record = self._transform_race_event(event_data)
        self.pending_records['events'].append(record)
        
        # Events are sent immediately (not batched) as they're less frequent
        self._send_records('events', self.pending_records['events'])
        self.pending_records['events'] = []
    
    def send_session_info(self, session_data: Dict[str, Any]):
        """Send session info to Data Cloud"""
        if not self.authenticate():
            return False
            
        record = self._transform_session_info(session_data)
        self._send_single_record('sessions', record)
    
    def _transform_telemetry_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform telemetry payload to Data Cloud format"""
        now_iso = datetime.now(timezone.utc).isoformat()
        
        return {
            "telemetry_id": data.get("telemetryId", f"{data.get('sessionId', '')}-{int(time.time()*1000)}"),
            "session_id": data.get("sessionId", ""),
            "timestamp": now_iso,
            "driver_name": data.get("driverName", ""),
            "track_name": data.get("track", ""),
            "frame_id": data.get("frameId", 0),
            "player_car_index": data.get("playerCarIndex", 0),
            "session_time": data.get("sessionTime", 0),
            "last_lap_time_ms": data.get("lastLapTime", 0) * 1000 if data.get("lastLapTime") else 0,
            "current_lap_time_ms": data.get("lapTimeSoFar", 0) * 1000 if data.get("lapTimeSoFar") else 0,
            "lap_number": data.get("lapNumber", 0),
            "position": data.get("position", 0),
            "sector": data.get("sector", 0),
            "lap_valid": data.get("lapValid", True),
            "pit_status": data.get("pitStatus", 0),
            "speed": data.get("speed", {}).get("current", 0),
            "throttle": data.get("throttle", {}).get("current", 0),
            "brake": data.get("brake", {}).get("current", 0),
            "steer": data.get("steer", {}).get("current", 0),
            "gear": data.get("gear", {}).get("current", 0),
            "engine_rpm": data.get("engineRPM", {}).get("current", 0),
            "drs_active": data.get("drsActive", False),
            "drs_allowed": data.get("drsAllowed", False),
            "fuel_in_tank": data.get("fuelInTank", 0),
            "fuel_remaining_laps": data.get("fuelRemainingLaps", 0),
            "ers_store_energy": data.get("ersStoreEnergy", 0),
            "ers_deploy_mode": data.get("ersDeployMode", ""),
            "actual_tyre_compound": data.get("tyreCompound", ""),
            "engine_temperature": data.get("engineTemperature", 0),
            # Add brake temperatures
            "brake_temp_front_left": data.get("brakeTemperature", {}).get("frontLeft", 0),
            "brake_temp_front_right": data.get("brakeTemperature", {}).get("frontRight", 0),
            "brake_temp_rear_left": data.get("brakeTemperature", {}).get("rearLeft", 0),
            "brake_temp_rear_right": data.get("brakeTemperature", {}).get("rearRight", 0),
            # Add tyre wear
            "tyre_wear_front_left": data.get("tyreWear", {}).get("frontLeft", 0),
            "tyre_wear_front_right": data.get("tyreWear", {}).get("frontRight", 0),
            "tyre_wear_rear_left": data.get("tyreWear", {}).get("rearLeft", 0),
            "tyre_wear_rear_right": data.get("tyreWear", {}).get("rearRight", 0),
            # Add damage data
            "front_left_wing_damage": data.get("damage", {}).get("frontLeftWing", 0),
            "front_right_wing_damage": data.get("damage", {}).get("frontRightWing", 0),
            "rear_wing_damage": data.get("damage", {}).get("rearWing", 0),
            "floor_damage": data.get("damage", {}).get("floor", 0),
            "gearbox_damage": data.get("damage", {}).get("gearBox", 0),
            "engine_damage": data.get("damage", {}).get("engine", 0),
            "drs_fault": data.get("damage", {}).get("drsFault", False),
            "ers_fault": data.get("damage", {}).get("ersFault", False)
        }
    
    def _transform_race_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform race event to Data Cloud format matching OpenAPI schema"""
        now_iso = datetime.now(timezone.utc).isoformat()
        
        return {
            "event_id": f"{event_data.get('sessionId', '')}-{event_data.get('type', 'unknown')}-{int(time.time()*1000)}",
            "timestamp": now_iso,
            "event_time": now_iso,  # Event occurrence time
            "session_id": event_data.get("sessionId", ""),
            "event_type": event_data.get("type", "unknown"),
            "description": event_data.get("message", ""),
            "driver_name": event_data.get("driverName", ""),
            "lap_number": event_data.get("lapNumber", 0),
            "vehicle_index": event_data.get("playerCarIndex", 0),  # Primary car involved
            "secondary_vehicle_index": event_data.get("secondaryCarIndex", 0)  # For multi-car events
        }
    
    def _transform_session_info(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform session info to Data Cloud format matching OpenAPI schema"""
        now_iso = datetime.now(timezone.utc).isoformat()
        
        return {
            "session_id": session_data.get("sessionId", ""),
            "timestamp": now_iso,
            "track_name": session_data.get("track", ""),
            "track_id": session_data.get("trackId", -1),
            "session_type": session_data.get("sessionType", "race"),  # practice, qualifying, race, etc.
            "session_duration": session_data.get("sessionDuration", 0),
            "session_time_left": session_data.get("sessionTimeLeft", 0),
            "total_laps": session_data.get("totalLaps", 0),
            "track_length": session_data.get("trackLength", 0),
            "track_temperature": session_data.get("trackTemperature", 0),
            "air_temperature": session_data.get("airTemperature", 0),
            "weather": session_data.get("weather", "clear"),
            "safety_car_status": session_data.get("safetyCarStatus", "none"),
            "pit_speed_limit": session_data.get("pitSpeedLimit", 80),
            "game_mode": session_data.get("gameMode", "F1_24"),
            "formula": session_data.get("formula", "F1")
        }
    
    def _send_single_record(self, stream_type: str, record: Dict[str, Any]):
        """Send a single record to Data Cloud"""
        self._send_records(stream_type, [record])
    
    def _send_records(self, stream_type: str, records: List[Dict[str, Any]]):
        """Send records to Data Cloud events endpoint"""
        if not records or stream_type not in self.stream_endpoints:
            return
            
        try:
            endpoint = self.stream_endpoints[stream_type]
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Use original Data Cloud ingestion format (not events format)
            payload = {
                "data": records
            }
            
            if self.debug:
                logging.info(f"Sending {len(records)} records to Data Cloud ingestion API")
                logging.info(f"Payload preview: {json.dumps(payload, indent=2)[:500]}...")
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            if response.status_code in [200, 201]:
                if self.debug:
                    logging.info(f"Successfully sent {len(records)} {stream_type} records to Data Cloud")
            else:
                # For 401 errors, try to re-authenticate and retry once
                if response.status_code == 401:
                    logging.warning(f"401 Unauthorized for {stream_type} - attempting re-authentication")
                    self.access_token = None  # Force re-authentication
                    if self.authenticate():
                        # Retry with new token
                        headers["Authorization"] = f"Bearer {self.access_token}"
                        retry_response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
                        if retry_response.status_code in [200, 201]:
                            if self.debug:
                                logging.info(f"Successfully sent {len(records)} {stream_type} records to Data Cloud (after retry)")
                            return
                        else:
                            logging.error(f"Retry failed for {stream_type} to Data Cloud: {retry_response.status_code}")
                    else:
                        logging.error(f"Re-authentication failed for {stream_type}")
                
                logging.error(f"Failed to send {stream_type} to Data Cloud: {response.status_code}")
                if self.debug:
                    logging.error(f"Request URL: {endpoint}")
                    logging.error(f"Request headers: {headers}")
                    logging.error(f"Response text: {response.text}")
                    logging.error(f"Response headers: {dict(response.headers)}")
                
        except Exception as e:
            logging.error(f"Error sending {stream_type} to Data Cloud: {e}")
    
    def _flush_telemetry_batch(self):
        """Send accumulated telemetry records"""
        if self.pending_records['telemetry']:
            self._send_records('telemetry', self.pending_records['telemetry'])
            self.pending_records['telemetry'] = []
            self.last_batch_time = time.time()
    
    def flush_all_batches(self):
        """Flush all pending batches - call on shutdown"""
        for stream_type, records in self.pending_records.items():
            if records:
                self._send_records(stream_type, records)
        
        # Clear all batches
        for stream_type in self.pending_records:
            self.pending_records[stream_type] = []


# Configuration helper
def create_datacloud_client(
    salesforce_domain: str,
    client_id: str,
    private_key_path: str,
    username: str,
    debug: bool = False
) -> DataCloudClient:
    """
    Create a Data Cloud client with JWT Bearer Flow authentication.
    You'll need to update these URLs with your actual Data Cloud stream endpoints.
    """
    
    # Load Data Cloud endpoints from environment or use defaults
    # Data Cloud uses the Ingestion API format: https://subdomain.c360a.salesforce.com/api/v1/ingest/sources/SOURCE_NAME/STREAM_NAME
    dc_telemetry_endpoint = os.environ.get("DC_TELEMETRY_ENDPOINT", "")
    dc_events_endpoint = os.environ.get("DC_EVENTS_ENDPOINT", "")
    dc_sessions_endpoint = os.environ.get("DC_SESSIONS_ENDPOINT", "")
    dc_participants_endpoint = os.environ.get("DC_PARTICIPANTS_ENDPOINT", "")
    dc_motion_endpoint = os.environ.get("DC_MOTION_ENDPOINT", "")
    
    stream_endpoints = {
        'telemetry': dc_telemetry_endpoint,
        'events': dc_events_endpoint,
        'sessions': dc_sessions_endpoint,
        'participants': dc_participants_endpoint,
        'motion': dc_motion_endpoint
    }
    
    # Configure logging if debug is enabled
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    
    return DataCloudClient(
        salesforce_domain=salesforce_domain,
        client_id=client_id, 
        private_key_path=private_key_path,
        username=username,
        stream_endpoints=stream_endpoints,
        debug=debug
    )


