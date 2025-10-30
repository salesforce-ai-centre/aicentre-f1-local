// Dual-Rig F1 Telemetry Dashboard JavaScript

console.log('Dual-rig dashboard initializing...');

// F1 game tire array indices (RL, RR, FL, FR)
const TIRE_INDEX_RL = 0;
const TIRE_INDEX_RR = 1;
const TIRE_INDEX_FL = 2;
const TIRE_INDEX_FR = 3;

// Tire temperature thresholds
const TIRE_TEMP_MIN = 80;
const TIRE_TEMP_MAX = 105;

// RPM limits
const RPM_MAX = 15000;
const RPM_REDLINE = 12000;

// WebSocket connection
const socket = io();

// Rig state
const rigState = {
    RIG_A: { lastUpdate: 0, sessionUID: null, isActive: false },
    RIG_B: { lastUpdate: 0, sessionUID: null, isActive: false }
};

// Connection handlers
socket.on('connect', () => {
    console.log('✓ Connected to telemetry gateway');
    updateConnectionStatus('connected');

    // Subscribe to all rigs
    socket.emit('subscribe_all');
});

socket.on('disconnect', () => {
    console.log('✗ Disconnected from gateway');
    updateConnectionStatus('disconnected');
});

socket.on('connection_status', (data) => {
    console.log('Connection status:', data.status);
});

// Telemetry update handler
socket.on('telemetry_update', (data) => {
    const rigId = data.rig_id;
    if (!rigId) return;

    const now = Date.now();
    const previousSessionUID = rigState[rigId].sessionUID;
    const currentSessionUID = data.sessionUID;

    // Detect new session
    if (previousSessionUID && currentSessionUID && previousSessionUID !== currentSessionUID) {
        console.log(`[${rigId}] New session detected: ${currentSessionUID}`);
        // Clear old data on session change
        rigState[rigId] = { lastUpdate: 0, sessionUID: null, isActive: false };
    }

    // Update state
    rigState[rigId] = {...data};
    rigState[rigId].lastUpdate = now;
    rigState[rigId].sessionUID = currentSessionUID;
    rigState[rigId].isActive = true;

    // Update display
    updateRigDisplay(rigId, data);
});

/**
 * Update dashboard display for a rig
 */
function updateRigDisplay(rigId, data) {
    const prefix = rigId === 'RIG_A' ? 'rigA' : 'rigB';

    // Status is now handled by checkDataFreshness() interval

    // Session info
    if (data.sessionUID) {
        const sessionId = String(data.sessionUID).slice(-6);
        updateElement(`${prefix}-sessionId`, sessionId);
    }

    if (data.overallFrameIdentifier !== undefined) {
        updateElement(`${prefix}-frame`, data.overallFrameIdentifier);
    }

    // Track and session type
    if (data.trackName) {
        updateElement(`${prefix}-trackName`, data.trackName);
    }

    if (data.sessionTypeName) {
        updateElement(`${prefix}-sessionType`, data.sessionTypeName);
    }

    // Telemetry data (packet ID 6)
    if (data.speed !== undefined) {
        updateElement(`${prefix}-speed`, Math.round(data.speed));
    }

    if (data.engineRPM !== undefined) {
        const rpm = Math.round(data.engineRPM);
        updateElement(`${prefix}-rpm`, rpm);
        updateRPMBar(`${prefix}-rpmBar`, rpm);
    }

    if (data.gear !== undefined) {
        const gear = data.gear === 0 ? 'N' : data.gear === -1 ? 'R' : data.gear;
        updateElement(`${prefix}-gear`, gear);
    }

    if (data.throttle !== undefined) {
        const throttle = data.throttle * 100;
        updateProgressBar(`${prefix}-throttleBar`, throttle);
        updateElement(`${prefix}-throttle`, `${Math.round(throttle)}%`);
    }

    if (data.brake !== undefined) {
        const brake = data.brake * 100;
        updateProgressBar(`${prefix}-brakeBar`, brake);
        updateElement(`${prefix}-brake`, `${Math.round(brake)}%`);
    }

    if (data.steer !== undefined) {
        // Steer is -1.0 (full left) to +1.0 (full right)
        const steerAngle = data.steer * 90; // Convert to degrees (-90 to +90)
        updateSteeringGauge(prefix, data.steer);
        updateElement(`${prefix}-steer`, `${steerAngle >= 0 ? '+' : ''}${Math.round(steerAngle)}°`);
    }

    // Tyre temps (RL, RR, FL, FR indices: 0, 1, 2, 3)
    if (data.tyresSurfaceTemperature) {
        const temps = data.tyresSurfaceTemperature;
        updateTyre(`${prefix}-tyreFL`, temps[TIRE_INDEX_FL]);
        updateTyre(`${prefix}-tyreFR`, temps[TIRE_INDEX_FR]);
        updateTyre(`${prefix}-tyreRL`, temps[TIRE_INDEX_RL]);
        updateTyre(`${prefix}-tyreRR`, temps[TIRE_INDEX_RR]);
    }

    // G-Forces (packet ID 0 - CarMotionData)
    if (data.gForceLateral !== undefined) {
        updateElement(`${prefix}-gLat`, data.gForceLateral.toFixed(1));
    }
    if (data.gForceLongitudinal !== undefined) {
        updateElement(`${prefix}-gLong`, data.gForceLongitudinal.toFixed(1));
    }
    if (data.gForceVertical !== undefined) {
        updateElement(`${prefix}-gVert`, data.gForceVertical.toFixed(1));
    }

    // DRS status (packet ID 6 - CarTelemetryData)
    if (data.drs !== undefined) {
        updateDRS(prefix, data.drs, data.drsActivationDistance);
    }

    // Fuel data (packet ID 7 - CarStatusData)
    if (data.fuelInTank !== undefined) {
        updateElement(`${prefix}-fuel`, `${data.fuelInTank.toFixed(1)} kg`);
    }
    if (data.fuelRemainingLaps !== undefined) {
        updateElement(`${prefix}-fuelLaps`, `${data.fuelRemainingLaps.toFixed(1)} laps`);
    }

    // ERS energy (packet ID 7 - CarStatusData)
    if (data.ersStoreEnergy !== undefined) {
        const energyMJ = (data.ersStoreEnergy / 1000000).toFixed(2); // Convert J to MJ
        const maxEnergy = 4000000; // 4 MJ max
        const percentage = (data.ersStoreEnergy / maxEnergy) * 100;
        updateElement(`${prefix}-ersEnergy`, `${energyMJ} MJ`);
        updateProgressBar(`${prefix}-ersBar`, Math.min(percentage, 100));
    }

    // Tyre wear (packet ID 10 - CarDamageData)
    if (data.tyresWear) {
        const wear = data.tyresWear;
        updateTyreWear(`${prefix}-wearFL`, wear[TIRE_INDEX_FL]);
        updateTyreWear(`${prefix}-wearFR`, wear[TIRE_INDEX_FR]);
        updateTyreWear(`${prefix}-wearRL`, wear[TIRE_INDEX_RL]);
        updateTyreWear(`${prefix}-wearRR`, wear[TIRE_INDEX_RR]);
    }

    // Lap data (packet ID 2)
    if (data.carPosition !== undefined) {
        updateElement(`${prefix}-position`, data.carPosition);
    }

    if (data.currentLapNum !== undefined) {
        updateElement(`${prefix}-lapNum`, data.currentLapNum);
    }

    // Current lap time (always show even if 0)
    if (data.currentLapTimeInMS !== undefined) {
        const currentLap = formatLapTime(data.currentLapTimeInMS);
        updateElement(`${prefix}-currentLap`, currentLap);
    }

    // Last lap time (only show if greater than 0)
    if (data.lastLapTimeInMS !== undefined) {
        if (data.lastLapTimeInMS > 0) {
            const lastLap = formatLapTime(data.lastLapTimeInMS);
            updateElement(`${prefix}-lastLap`, lastLap);
        } else {
            updateElement(`${prefix}-lastLap`, '--:--.---');
        }
    }
}

/**
 * Update a DOM element's text content
 */
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element && element.textContent !== String(value)) {
        element.textContent = value;
    }
}

/**
 * Update a progress bar width
 */
function updateProgressBar(id, percentage) {
    const bar = document.getElementById(id);
    if (bar) {
        bar.style.width = `${percentage}%`;
    }
}

/**
 * Update RPM bar with color zones
 */
function updateRPMBar(id, rpm) {
    const bar = document.getElementById(id);
    if (!bar) return;

    const percentage = (rpm / RPM_MAX) * 100;
    bar.style.width = `${Math.min(percentage, 100)}%`;
}

/**
 * Update steering wheel rotation and indicators
 * steerValue: -1.0 = full left, 0 = center, +1.0 = full right
 */
function updateSteeringGauge(prefix, steerValue) {
    const wheelRotate = document.getElementById(`${prefix}-wheelRotate`);
    const leftIndicator = document.getElementById(`${prefix}-steerLeft`);
    const rightIndicator = document.getElementById(`${prefix}-steerRight`);

    if (!wheelRotate || !leftIndicator || !rightIndicator) return;

    // Rotate wheel: -450° (full left) to +450° (full right) for dramatic effect
    // This gives 1.25 full rotations in each direction
    const angle = steerValue * 450;

    // Use CSS transform with proper transform-origin instead of SVG transform attribute
    wheelRotate.style.transform = `rotate(${angle}deg)`;
    wheelRotate.style.transformOrigin = 'center';

    // Update direction indicators
    if (steerValue < -0.05) {
        // Turning left
        leftIndicator.classList.add('active');
        rightIndicator.classList.remove('active');
    } else if (steerValue > 0.05) {
        // Turning right
        rightIndicator.classList.add('active');
        leftIndicator.classList.remove('active');
    } else {
        // Center - both off
        leftIndicator.classList.remove('active');
        rightIndicator.classList.remove('active');
    }
}

/**
 * Update tyre display with temperature color coding
 */
function updateTyre(id, temp) {
    const tyre = document.getElementById(id);
    if (!tyre) return;

    const tempSpan = tyre.querySelector('.tyre-temp');
    if (tempSpan) {
        tempSpan.textContent = temp ? Math.round(temp) : '--';
    }

    // Color coding
    tyre.classList.remove('cold', 'optimal', 'hot');
    if (temp) {
        if (temp < TIRE_TEMP_MIN) {
            tyre.classList.add('cold');
        } else if (temp > TIRE_TEMP_MAX) {
            tyre.classList.add('hot');
        } else {
            tyre.classList.add('optimal');
        }
    }
}

/**
 * Format milliseconds to MM:SS.mmm
 */
function formatLapTime(ms) {
    if (!ms || ms <= 0) return '--:--.---';

    const totalSeconds = ms / 1000;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = (totalSeconds % 60).toFixed(3);

    return `${minutes}:${seconds.padStart(6, '0')}`;
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(status) {
    const indicator = document.getElementById('connectionStatus');
    const text = document.getElementById('connectionText');

    if (indicator) {
        indicator.className = `status-indicator ${status}`;
    }

    if (text) {
        text.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    }
}

/**
 * Check for stale data and show warnings
 */
function checkDataFreshness() {
    const now = Date.now();
    const staleThreshold = 5000; // 5 seconds

    ['RIG_A', 'RIG_B'].forEach(rigId => {
        const prefix = rigId === 'RIG_A' ? 'rigA' : 'rigB';
        const state = rigState[rigId];
        const lastUpdate = state.lastUpdate;

        if (!lastUpdate || lastUpdate === 0) {
            // Never received data
            updateRigStatus(rigId, 'Waiting for data...', '#a0a0a0');
        } else {
            const age = now - lastUpdate;

            if (age > staleThreshold) {
                // Data is stale - session likely ended
                if (state.isActive) {
                    state.isActive = false;
                    console.log(`[${rigId}] Session appears to have ended (no data for ${(age/1000).toFixed(1)}s)`);
                }
                updateRigStatus(rigId, 'Session ended / No data', '#e74c3c');
            } else if (state.isActive) {
                // Data is fresh and active
                updateRigStatus(rigId, 'Receiving data...', '#2ecc71');
            }
        }
    });
}

/**
 * Update rig status indicator
 */
function updateRigStatus(rigIdOrPrefix, message, color) {
    // Accept either rigId (RIG_A/RIG_B) or prefix (rigA/rigB)
    const prefix = rigIdOrPrefix.includes('RIG_')
        ? (rigIdOrPrefix === 'RIG_A' ? 'rigA' : 'rigB')
        : rigIdOrPrefix;

    const statusElement = document.getElementById(`${prefix}Status`);
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.style.color = color;
    }
}

// Check data freshness every 2 seconds
setInterval(checkDataFreshness, 2000);

/**
 * Update DRS status indicator
 */
function updateDRS(prefix, drsStatus, drsDistance) {
    const indicator = document.getElementById(`${prefix}-drsIndicator`);
    const distance = document.getElementById(`${prefix}-drsDistance`);

    if (!indicator) return;

    if (drsStatus === 1) {
        // DRS is ON
        indicator.textContent = 'ENABLED';
        indicator.classList.remove('available');
        indicator.classList.add('enabled');
        if (distance) distance.textContent = 'Active';
    } else if (drsDistance !== undefined && drsDistance > 0) {
        // DRS is available soon
        indicator.textContent = 'AVAILABLE';
        indicator.classList.remove('enabled');
        indicator.classList.add('available');
        if (distance) distance.textContent = `${Math.round(drsDistance)}m`;
    } else {
        // DRS is disabled
        indicator.textContent = 'DISABLED';
        indicator.classList.remove('enabled', 'available');
        if (distance) distance.textContent = '--';
    }
}

/**
 * Update tyre wear percentage
 */
function updateTyreWear(id, wearValue) {
    const element = document.getElementById(id);
    if (!element) return;

    const wearPercent = Math.round(wearValue);
    const valueElement = element.querySelector('.wear-value');
    if (valueElement) {
        valueElement.textContent = `${wearPercent}%`;
    }

    // Color coding based on wear level
    element.classList.remove('high-wear', 'critical-wear');
    if (wearPercent >= 80) {
        element.classList.add('critical-wear');
    } else if (wearPercent >= 60) {
        element.classList.add('high-wear');
    }
}

console.log('✓ Dual-rig dashboard ready');
