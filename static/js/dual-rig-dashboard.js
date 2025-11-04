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
    // Check both 'carPosition' (simulator) and 'position' (real receiver)
    const position = data.carPosition !== undefined ? data.carPosition : data.position;
    if (position !== undefined) {
        updateElement(`${prefix}-position`, position);
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

// ===========================
// LEADERBOARD FUNCTIONALITY
// ===========================

// Leaderboard state
const leaderboardState = {
    RIG_A: {
        sessionBest: null,  // { lapTime, lapNum, trackName, sessionUID }
        savedLaps: []       // Array of saved best laps with player names
    },
    RIG_B: {
        sessionBest: null,
        savedLaps: []
    },
    viewMode: 'combined'  // 'combined' or 'split'
};

// localStorage keys
const STORAGE_KEY_RIG_A = 'f1_leaderboard_RIG_A';
const STORAGE_KEY_RIG_B = 'f1_leaderboard_RIG_B';
const STORAGE_KEY_VIEW_MODE = 'f1_leaderboard_viewMode';

/**
 * Initialize leaderboard from localStorage
 */
function initLeaderboard() {
    console.log('Initializing leaderboard...');

    // Load RIG_A leaderboard
    try {
        const rigAData = localStorage.getItem(STORAGE_KEY_RIG_A);
        if (rigAData) {
            leaderboardState.RIG_A.savedLaps = JSON.parse(rigAData);
            console.log(`Loaded ${leaderboardState.RIG_A.savedLaps.length} RIG_A entries from localStorage`);
        }
    } catch (error) {
        console.error('Error loading RIG_A leaderboard:', error);
        leaderboardState.RIG_A.savedLaps = [];
    }

    // Load RIG_B leaderboard
    try {
        const rigBData = localStorage.getItem(STORAGE_KEY_RIG_B);
        if (rigBData) {
            leaderboardState.RIG_B.savedLaps = JSON.parse(rigBData);
            console.log(`Loaded ${leaderboardState.RIG_B.savedLaps.length} RIG_B entries from localStorage`);
        }
    } catch (error) {
        console.error('Error loading RIG_B leaderboard:', error);
        leaderboardState.RIG_B.savedLaps = [];
    }

    // Load view mode preference
    try {
        const viewMode = localStorage.getItem(STORAGE_KEY_VIEW_MODE);
        if (viewMode) {
            leaderboardState.viewMode = viewMode;
        }
    } catch (error) {
        console.error('Error loading view mode:', error);
    }

    // Add test session best times (only if no real data exists)
    // if (!leaderboardState.RIG_A.sessionBest) {
    //     leaderboardState.RIG_A.sessionBest = {
    //         lapTime: 78950,
    //         lapNum: 12,
    //         trackName: 'Silverstone',
    //         sessionUID: 'TEST_SESSION_A',
    //         timestamp: Date.now()
    //     };
    // }

    // if (!leaderboardState.RIG_B.sessionBest) {
    //     leaderboardState.RIG_B.sessionBest = {
    //         lapTime: 77650,  // Faster than RIG_A
    //         lapNum: 9,
    //         trackName: 'Silverstone',
    //         sessionUID: 'TEST_SESSION_B',
    //         timestamp: Date.now()
    //     };
    // }

    // Setup button handlers
    setupLeaderboardControls();

    // Apply initial view mode
    applyViewMode(leaderboardState.viewMode);
}

/**
 * Setup button event handlers
 */
function setupLeaderboardControls() {
    // View toggle button
    const viewToggleBtn = document.getElementById('viewToggleBtn');

    // Combined view buttons
    const saveSessionBtn = document.getElementById('saveSessionBtn');
    const resetCurrentBtn = document.getElementById('resetCurrentBtn');

    // Split view buttons
    const saveSessionBtnSplit = document.getElementById('saveSessionBtnSplit');
    const resetCurrentBtnSplit = document.getElementById('resetCurrentBtnSplit');

    // Modal buttons
    const confirmSaveBtn = document.getElementById('confirmSaveBtn');
    const cancelSaveBtn = document.getElementById('cancelSaveBtn');

    if (viewToggleBtn) {
        viewToggleBtn.addEventListener('click', toggleViewMode);
    }

    // Combined view button handlers
    if (saveSessionBtn) {
        saveSessionBtn.addEventListener('click', () => showSaveSessionModal('BOTH'));
    }

    if (resetCurrentBtn) {
        resetCurrentBtn.addEventListener('click', () => resetCurrentSession('BOTH'));
    }

    // Split view button handlers
    if (saveSessionBtnSplit) {
        saveSessionBtnSplit.addEventListener('click', () => showSaveSessionModal('BOTH'));
    }

    if (resetCurrentBtnSplit) {
        resetCurrentBtnSplit.addEventListener('click', () => resetCurrentSession('BOTH'));
    }

    // Modal handlers
    if (confirmSaveBtn) {
        confirmSaveBtn.addEventListener('click', confirmSaveSession);
    }

    if (cancelSaveBtn) {
        cancelSaveBtn.addEventListener('click', closeSaveSessionModal);
    }
}

/**
 * Track lap times and update session best
 */
function trackLapTime(rigId, data) {
    // Only track valid completed laps
    if (!data.lastLapTimeInMS || data.lastLapTimeInMS <= 0) return;
    if (data.currentLapInvalid) return;

    const state = leaderboardState[rigId];
    const currentLapTime = data.lastLapTimeInMS;

    // Check if this is a new session best
    if (!state.sessionBest || currentLapTime < state.sessionBest.lapTime) {
        const previousBest = state.sessionBest ? state.sessionBest.lapTime : null;

        state.sessionBest = {
            lapTime: currentLapTime,
            lapNum: data.currentLapNum - 1,  // Last lap was previous lap number
            trackName: data.trackName || 'Unknown Track',
            sessionUID: data.sessionUID,
            timestamp: Date.now()
        };

        console.log(`[${rigId}] New session best: ${formatLapTime(currentLapTime)} (Lap ${state.sessionBest.lapNum})`);

        // Update display with animation based on current view mode
        if (leaderboardState.viewMode === 'combined') {
            updateSessionBestDisplay(rigId, true);
        } else {
            updateSessionBestDisplaySplit(rigId, true);
        }

        // Calculate improvement
        if (previousBest) {
            const improvement = previousBest - currentLapTime;
            console.log(`[${rigId}] Improved by ${formatLapTime(improvement)}`);
        }
    }
}

/**
 * Update session best lap display (for combined view - shows overall fastest from leaderboard)
 */
function updateSessionBestDisplay(rigId = null, isNewBest = false) {
    const timeElement = document.getElementById('overallSessionBest');
    const rigBadgeElement = document.getElementById('overallSessionBestRig');
    const lapElement = document.getElementById('overallSessionBestLap');
    const playerElement = document.getElementById('overallSessionBestPlayer');

    if (!timeElement || !rigBadgeElement || !lapElement || !playerElement) return;

    // Combine all saved laps from both rigs
    const allSavedLaps = [
        ...leaderboardState.RIG_A.savedLaps.map(lap => ({ ...lap, rigId: 'RIG_A' })),
        ...leaderboardState.RIG_B.savedLaps.map(lap => ({ ...lap, rigId: 'RIG_B' }))
    ];

    // Sort by lap time to find the fastest
    allSavedLaps.sort((a, b) => a.lapTime - b.lapTime);

    // Get the fastest saved lap
    if (allSavedLaps.length > 0) {
        const fastestEntry = allSavedLaps[0];

        // Display all data from the fastest saved lap
        timeElement.textContent = formatLapTime(fastestEntry.lapTime);
        lapElement.textContent = `Lap ${fastestEntry.lapNum}`;
        playerElement.textContent = fastestEntry.playerName;

        // Update rig badge
        const rigLabel = fastestEntry.rigId === 'RIG_A' ? '🔴 Simulator 1' : '🔵 Simulator 2';
        const rigClass = fastestEntry.rigId === 'RIG_A' ? 'rig-a' : 'rig-b';
        rigBadgeElement.textContent = rigLabel;
        rigBadgeElement.className = `session-best-rig-badge ${rigClass}`;

        // Flash animation for new best
        if (isNewBest) {
            timeElement.classList.add('new-best');
            setTimeout(() => {
                timeElement.classList.remove('new-best');
            }, 1000);
        }
    } else {
        timeElement.textContent = '--:--.---';
        lapElement.textContent = 'Lap --';
        playerElement.textContent = '--';
        rigBadgeElement.textContent = '';
        rigBadgeElement.className = 'session-best-rig-badge';
    }
}

/**
 * Update session best lap display (for split view)
 */
function updateSessionBestDisplaySplit(rigId, isNewBest = false) {
    const prefix = rigId === 'RIG_A' ? 'rigA' : 'rigB';
    const state = leaderboardState[rigId];

    const timeElement = document.getElementById(`${prefix}-sessionBestSplit`);
    const lapElement = document.getElementById(`${prefix}-sessionBestLapSplit`);

    if (!timeElement || !lapElement) return;

    if (state.sessionBest) {
        const formattedTime = formatLapTime(state.sessionBest.lapTime);
        timeElement.textContent = formattedTime;
        lapElement.textContent = `Lap ${state.sessionBest.lapNum}`;

        // Flash animation for new best
        if (isNewBest) {
            timeElement.classList.add('new-best');
            setTimeout(() => {
                timeElement.classList.remove('new-best');
            }, 1000);
        }
    } else {
        timeElement.textContent = '--:--.---';
        lapElement.textContent = 'Lap --';
    }
}

/**
 * Show modal to save session
 */
function showSaveSessionModal(rigId = null) {
    // If rigId specified, only save that rig
    // Otherwise show modal for both rigs
    const hasRigABest = leaderboardState.RIG_A.sessionBest !== null;
    const hasRigBBest = leaderboardState.RIG_B.sessionBest !== null;

    // If specific rig requested, check if it has a best lap
    if (rigId === 'RIG_A' && !hasRigABest) {
        alert('No session best lap for Rig 1. Complete at least one valid lap first.');
        return;
    }
    if (rigId === 'RIG_B' && !hasRigBBest) {
        alert('No session best lap for Rig 2. Complete at least one valid lap first.');
        return;
    }

    // If no rig specified and neither has a best, warn
    if (!rigId && !hasRigABest && !hasRigBBest) {
        alert('No session best laps to save. Complete at least one valid lap first.');
        return;
    }

    const modal = document.getElementById('playerNameModal');
    const rigAInput = document.getElementById('rigA-playerName');
    const rigBInput = document.getElementById('rigB-playerName');
    const rigABestTime = document.getElementById('rigA-modalBestTime');
    const rigBBestTime = document.getElementById('rigB-modalBestTime');

    // Pre-fill with current driver names from the dashboard
    const rigADriver = document.getElementById('rigADriver');
    const rigBDriver = document.getElementById('rigBDriver');

    if (rigAInput && rigADriver) {
        rigAInput.value = rigADriver.textContent || 'Player 1';
    }
    if (rigBInput && rigBDriver) {
        rigBInput.value = rigBDriver.textContent || 'Player 2';
    }

    // Show best times
    if (rigABestTime) {
        rigABestTime.textContent = hasRigABest
            ? formatLapTime(leaderboardState.RIG_A.sessionBest.lapTime)
            : 'No lap completed';
    }
    if (rigBBestTime) {
        rigBBestTime.textContent = hasRigBBest
            ? formatLapTime(leaderboardState.RIG_B.sessionBest.lapTime)
            : 'No lap completed';
    }

    // Store which rig(s) to save
    modal.dataset.saveRigId = rigId || 'BOTH';

    // Show modal
    if (modal) {
        modal.classList.add('show');
    }
}

/**
 * Close save session modal
 */
function closeSaveSessionModal() {
    const modal = document.getElementById('playerNameModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

/**
 * Confirm and save session to leaderboard
 */
function confirmSaveSession() {
    const modal = document.getElementById('playerNameModal');
    const saveRigId = modal ? modal.dataset.saveRigId : 'BOTH';
    const rigAInput = document.getElementById('rigA-playerName');
    const rigBInput = document.getElementById('rigB-playerName');

    // Save based on which rig(s) were requested
    if ((saveRigId === 'BOTH' || saveRigId === 'RIG_A') && leaderboardState.RIG_A.sessionBest && rigAInput) {
        const playerName = rigAInput.value.trim() || 'Anonymous';
        saveToLeaderboard('RIG_A', playerName);
    }

    if ((saveRigId === 'BOTH' || saveRigId === 'RIG_B') && leaderboardState.RIG_B.sessionBest && rigBInput) {
        const playerName = rigBInput.value.trim() || 'Anonymous';
        saveToLeaderboard('RIG_B', playerName);
    }

    closeSaveSessionModal();
}

/**
 * Save session best to leaderboard
 */
function saveToLeaderboard(rigId, playerName) {
    const state = leaderboardState[rigId];

    if (!state.sessionBest) {
        console.warn(`[${rigId}] No session best to save`);
        return;
    }

    const entry = {
        playerName: playerName,
        lapTime: state.sessionBest.lapTime,
        lapNum: state.sessionBest.lapNum,
        trackName: state.sessionBest.trackName,
        sessionUID: state.sessionBest.sessionUID,
        timestamp: Date.now(),
        saved: true
    };

    // Add to saved laps
    state.savedLaps.push(entry);

    // Sort by lap time (fastest first)
    state.savedLaps.sort((a, b) => a.lapTime - b.lapTime);

    // Keep only top 10
    if (state.savedLaps.length > 10) {
        state.savedLaps = state.savedLaps.slice(0, 10);
    }

    // Save to localStorage
    const storageKey = rigId === 'RIG_A' ? STORAGE_KEY_RIG_A : STORAGE_KEY_RIG_B;
    try {
        localStorage.setItem(storageKey, JSON.stringify(state.savedLaps));
        console.log(`[${rigId}] Saved ${playerName}'s lap to leaderboard: ${formatLapTime(entry.lapTime)}`);
    } catch (error) {
        console.error(`Error saving ${rigId} leaderboard:`, error);
    }

    // Render updated leaderboard based on current view mode
    if (leaderboardState.viewMode === 'combined') {
        renderCombinedLeaderboard();
    } else {
        renderLeaderboard(rigId);
    }
}

/**
 * Reset current session best laps
 */
function resetCurrentSession(rigId = null) {
    const message = rigId && rigId !== 'BOTH'
        ? `Reset current session best for ${rigId === 'RIG_A' ? 'Simulator 1' : 'Simulator 2'}?`
        : 'Reset current session best laps for both rigs?';

    if (!confirm(message + ' This will clear the temporary session data but keep saved leaderboard entries.')) {
        return;
    }

    if (!rigId || rigId === 'BOTH' || rigId === 'RIG_A') {
        leaderboardState.RIG_A.sessionBest = null;
    }

    if (!rigId || rigId === 'BOTH' || rigId === 'RIG_B') {
        leaderboardState.RIG_B.sessionBest = null;
    }

    // Update display based on current view mode
    if (leaderboardState.viewMode === 'combined') {
        updateSessionBestDisplay();
    } else {
        updateSessionBestDisplaySplit('RIG_A');
        updateSessionBestDisplaySplit('RIG_B');
    }

    console.log(`Current session best laps reset${rigId && rigId !== 'BOTH' ? ' for ' + rigId : ''}`);
}

/**
 * Render leaderboard entries (compact version)
 */
function renderLeaderboard(rigId) {
    const prefix = rigId === 'RIG_A' ? 'rigA' : 'rigB';
    const container = document.getElementById(`${prefix}-leaderboardEntries`);

    if (!container) return;

    const state = leaderboardState[rigId];

    // Clear existing entries
    container.innerHTML = '';

    if (state.savedLaps.length === 0) {
        container.innerHTML = '<div class="no-data-compact">No saved laps</div>';
        return;
    }

    // Render each entry (compact format)
    state.savedLaps.forEach((entry, index) => {
        const rank = index + 1;
        const entryDiv = document.createElement('div');
        entryDiv.className = `leaderboard-entry-compact rank-${rank}`;
        entryDiv.dataset.rigId = rigId;
        entryDiv.dataset.index = index;
        entryDiv.onclick = () => editPlayerName(rigId, index);

        entryDiv.innerHTML = `
            <div class="entry-compact-left">
                <div class="entry-rank-compact">${rank}</div>
                <div class="entry-player-compact" title="${entry.playerName} - ${entry.trackName}">${entry.playerName}</div>
            </div>
            <div class="entry-time-compact">${formatLapTime(entry.lapTime)}</div>
        `;

        container.appendChild(entryDiv);
    });
}

/**
 * Edit player name inline
 */
function editPlayerName(rigId, index) {
    const state = leaderboardState[rigId];
    const entry = state.savedLaps[index];

    if (!entry) return;

    const newName = prompt('Edit player name:', entry.playerName);

    if (newName !== null && newName.trim() !== '') {
        entry.playerName = newName.trim();

        // Save to localStorage
        const storageKey = rigId === 'RIG_A' ? STORAGE_KEY_RIG_A : STORAGE_KEY_RIG_B;
        try {
            localStorage.setItem(storageKey, JSON.stringify(state.savedLaps));
            console.log(`[${rigId}] Updated player name to: ${entry.playerName}`);
        } catch (error) {
            console.error(`Error updating ${rigId} leaderboard:`, error);
        }

        // Re-render leaderboard based on current view mode
        if (leaderboardState.viewMode === 'combined') {
            renderCombinedLeaderboard();
        } else {
            renderLeaderboard(rigId);
        }
    }
}

/**
 * Toggle between combined and split view
 */
function toggleViewMode() {
    const newMode = leaderboardState.viewMode === 'combined' ? 'split' : 'combined';
    applyViewMode(newMode);

    // Save preference
    try {
        localStorage.setItem(STORAGE_KEY_VIEW_MODE, newMode);
    } catch (error) {
        console.error('Error saving view mode:', error);
    }
}

/**
 * Apply view mode
 */
function applyViewMode(mode) {
    leaderboardState.viewMode = mode;

    const viewToggleBtn = document.getElementById('viewToggleBtn');
    const combinedView = document.getElementById('combinedLeaderboard');
    const splitView = document.getElementById('splitLeaderboard');

    if (mode === 'combined') {
        // Show combined view, hide split view
        if (combinedView) combinedView.style.display = 'flex';
        if (splitView) splitView.style.display = 'none';
        if (viewToggleBtn) viewToggleBtn.textContent = 'Split';

        // Update overall session best display
        updateSessionBestDisplay();

        // Render combined leaderboard
        renderCombinedLeaderboard();
    } else {
        // Show split view, hide combined view
        if (combinedView) combinedView.style.display = 'none';
        if (splitView) splitView.style.display = 'flex';
        if (viewToggleBtn) viewToggleBtn.textContent = 'Combined';

        // Update session bests for split view
        updateSessionBestDisplaySplit('RIG_A');
        updateSessionBestDisplaySplit('RIG_B');

        // Render individual leaderboards
        renderLeaderboard('RIG_A');
        renderLeaderboard('RIG_B');
    }
}

/**
 * Render combined leaderboard (both rigs)
 */
function renderCombinedLeaderboard() {
    const container = document.getElementById('combinedLeaderboardEntries');
    if (!container) return;

    // Combine and sort all laps from both rigs
    const allLaps = [];

    leaderboardState.RIG_A.savedLaps.forEach(lap => {
        allLaps.push({ ...lap, rigId: 'RIG_A', rigName: 'Rig 1' });
    });

    leaderboardState.RIG_B.savedLaps.forEach(lap => {
        allLaps.push({ ...lap, rigId: 'RIG_B', rigName: 'Rig 2' });
    });

    // Sort by lap time (fastest first)
    allLaps.sort((a, b) => a.lapTime - b.lapTime);

    // Clear existing entries
    container.innerHTML = '';

    if (allLaps.length === 0) {
        container.innerHTML = '<div class="no-data">No saved laps</div>';
        return;
    }

    // Render combined entries
    allLaps.forEach((entry, index) => {
        const rank = index + 1;
        const entryDiv = document.createElement('div');
        entryDiv.className = `combined-entry rank-${rank}`;
        entryDiv.dataset.rigId = entry.rigId;
        entryDiv.onclick = () => {
            // Find the index in the original rig's savedLaps
            const rigState = leaderboardState[entry.rigId];
            const originalIndex = rigState.savedLaps.findIndex(lap =>
                lap.lapTime === entry.lapTime && lap.playerName === entry.playerName
            );
            if (originalIndex !== -1) {
                editPlayerName(entry.rigId, originalIndex);
            }
        };

        const rigBadgeClass = entry.rigId === 'RIG_A' ? 'rig-a' : 'rig-b';
        const rigLabel = entry.rigId === 'RIG_A' ? 'R1' : 'R2';

        entryDiv.innerHTML = `
            <div class="combined-entry-left">
                <div class="entry-rank-compact">${rank}</div>
                <div class="combined-entry-rig-badge ${rigBadgeClass}">${rigLabel}</div>
                <div class="entry-player-compact" title="${entry.playerName} - ${entry.trackName} - ${entry.rigName}">${entry.playerName}</div>
            </div>
            <div class="entry-time-compact">${formatLapTime(entry.lapTime)}</div>
        `;

        container.appendChild(entryDiv);
    });
}

// Make editPlayerName globally accessible
window.editPlayerName = editPlayerName;

// Initialize leaderboard on page load
document.addEventListener('DOMContentLoaded', initLeaderboard);

// Update telemetry handler to track lap times
const originalTelemetryHandler = socket._callbacks['$telemetry_update'] || [];
socket.on('telemetry_update', (data) => {
    const rigId = data.rig_id;
    if (!rigId) return;

    // Track lap times for leaderboard
    trackLapTime(rigId, data);

    // Update session best display based on current view mode
    if (leaderboardState.viewMode === 'combined') {
        updateSessionBestDisplay();
    } else {
        updateSessionBestDisplaySplit(rigId);
    }
});

console.log('✓ Dual-rig dashboard ready');
