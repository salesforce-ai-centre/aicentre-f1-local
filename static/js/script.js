document.addEventListener('DOMContentLoaded', (event) => {
    console.log("Dashboard script loaded.");
    
    // Performance data arrays for charts
    const lapData = {
        labels: [],        // Lap numbers
        times: [],         // Lap times in seconds
        personalBest: null // Personal best time
    };
    
    const sectorData = {
        labels: [],              // Lap numbers
        sector1: [],             // Sector 1 times
        sector2: [],             // Sector 2 times
        sector3: [],             // Sector 3 times
        bestSector1: null,       // Best sector 1 time
        bestSector2: null,       // Best sector 2 time
        bestSector3: null        // Best sector 3 time
    };
    
    const speedTraceData = {
        labels: [],        // Distance points
        currentLap: [],    // Speed at each point for current lap
        bestLap: []        // Speed at each point for best lap
    };

    // --- Gauge Configuration ---
    const gaugeOptions = {
        angle: 0.2, // The span of the gauge arc
        lineWidth: 0.25, // The line thickness
        radiusScale: 0.9, // Relative radius
        pointer: {
            length: 0.6, // Relative to gauge radius
            strokeWidth: 0.04, // The thickness
            color: '#FFFFFF' // Fill color - white for dark theme
        },
        limitMax: false,     // If false, max value increases automatically if value > max
        limitMin: false,     // If true, the min value of the gauge will be fixed
        colorStart: '#0176d3',   // Salesforce blue
        colorStop: '#0176d3',    
        strokeColor: 'rgba(255, 255, 255, 0.1)',  // Light stroke for dark theme
        generateGradient: true,
        highDpiSupport: true,     // High resolution support
        percentColors: [[0.0, "#0176d3"], [0.5, "#30c5ff"], [1.0, "#47daff"]], // Blue to light blue gradient
        renderTicks: {
            divisions: 5,
            divWidth: 1.2,
            divLength: 0.7,
            divColor: 'rgba(255, 255, 255, 0.4)',
            subDivisions: 3,
            subWidth: 0.6,
            subLength: 0.5,
            subColor: 'rgba(255, 255, 255, 0.2)'
        }
    };
    
    // RPM specific options with red line
    const rpmGaugeOptions = {
        ...gaugeOptions,
        staticZones: [
           {strokeStyle: "rgba(255, 255, 255, 0.2)", min: 0, max: 8000}, // Normal range
           {strokeStyle: "#FFC107", min: 8000, max: 10500}, // Yellow zone
           {strokeStyle: "#EA001E", min: 10500, max: 13000} // Red zone/redline
        ],
        renderTicks: {
            divisions: 10,
            divWidth: 1.2,
            divLength: 0.7,
            divColor: 'rgba(255, 255, 255, 0.3)',
            subDivisions: 3,
            subWidth: 0.6,
            subLength: 0.5,
            subColor: 'rgba(255, 255, 255, 0.2)'
        }
    };

    // Speed Gauge
    const speedGaugeElement = document.getElementById('speedGauge');
    const speedGauge = new Gauge(speedGaugeElement).setOptions(gaugeOptions);
    speedGauge.maxValue = 370; // Set initial max KM/H
    speedGauge.setMinValue(0);
    speedGauge.animationSpeed = 32; // Smoothness
    speedGauge.set(0); // Initial value

    // RPM Gauge
    const rpmGaugeElement = document.getElementById('rpmGauge');
    const rpmGauge = new Gauge(rpmGaugeElement).setOptions(rpmGaugeOptions);
    rpmGauge.maxValue = 13000; // Set initial max RPM
    rpmGauge.setMinValue(0);
    rpmGauge.animationSpeed = 32;
    rpmGauge.set(0);

    // Performance tracking variables
    let personalBestLapTime = null;
    let bestSectorTimes = [null, null, null];
    let previousLapTime = null;
    let fuelConsumptionHistory = [];
    let currentLapStartFuel = null;

    // Element References (Cache them for performance)
    const elements = {
        // Session Info
        driverName: document.getElementById('driverName'),
        trackName: document.getElementById('trackName'),
        lapNumber: document.getElementById('lapNumber'),
        position: document.getElementById('position'),
        lapTimeSoFar: document.getElementById('lapTimeSoFar'),
        lastLapTime: document.getElementById('lastLapTime'),
        sector: document.getElementById('sector'),
        lapValid: document.getElementById('lapValid'),
        
        // New timing elements
        deltaTime: document.getElementById('deltaTime'),
        personalBest: document.getElementById('personalBest'),
        sector1Time: document.getElementById('sector1Time'),
        sector2Time: document.getElementById('sector2Time'),
        sector3Time: document.getElementById('sector3Time'),
        sector1: document.getElementById('sector1'),
        sector2: document.getElementById('sector2'),
        sector3: document.getElementById('sector3'),
        
        // Gauges & Vitals
        gear: document.getElementById('gear'),
        speedValue: document.getElementById('speedValue'),
        rpmValue: document.getElementById('rpmValue'),
        
        // Inputs
        throttleBar: document.getElementById('throttleBar'),
        throttleValue: document.getElementById('throttleValue'),
        brakeBar: document.getElementById('brakeBar'),
        brakeValue: document.getElementById('brakeValue'),
        steeringIndicator: document.getElementById('steeringIndicator'),
        steeringValue: document.getElementById('steeringValue'),
        
        // Tyres & Temps
        tyreCompound: document.getElementById('tyreCompound'),
        tyreWearFL: document.getElementById('tyreWearFL'),
        tyreWearFR: document.getElementById('tyreWearFR'),
        tyreWearRL: document.getElementById('tyreWearRL'),
        tyreWearRR: document.getElementById('tyreWearRR'),
        brakeTempFL: document.getElementById('brakeTempFL'),
        brakeTempFR: document.getElementById('brakeTempFR'),
        brakeTempRL: document.getElementById('brakeTempRL'),
        brakeTempRR: document.getElementById('brakeTempRR'),
        
        // ERS & DRS
        drsStatus: document.getElementById('drsStatus'),
        wingStatus: document.getElementById('wing-status'),
        ersStoreBar: document.getElementById('ersStoreBar'),
        ersStoreValue: document.getElementById('ersStoreValue'),
        ersDeployMode: document.getElementById('ersDeployMode'),
        
        // Damage Elements
        damageWingFL: document.getElementById('damageWingFL'),
        damageWingFR: document.getElementById('damageWingFR'),
        damageWingR: document.getElementById('damageWingR'),
        damageFloor: document.getElementById('damageFloor'),
        damageGearbox: document.getElementById('damageGearbox'),
        damageEngine: document.getElementById('damageEngine'),
        
        // Charts & Events
        lapTimeChart: document.getElementById('lapTimeChart'),
        sectorChart: document.getElementById('sectorChart'),
        speedTraceChart: document.getElementById('speedTraceChart'),
        eventList: document.getElementById('eventList'),
        aiCoachMessages: document.getElementById('ai-coach-messages'),
        
        // Advanced Analytics
        gForceLateral: document.getElementById('gForceLateral'),
        gForceLongitudinal: document.getElementById('gForceLongitudinal'),
        inputOverlayChart: document.getElementById('inputOverlayChart'),
        fuelConsumption: document.getElementById('fuelConsumption'),
        pitWindow: document.getElementById('pitWindow'),
        
        // Strategy Alerts
        tireAlert: document.getElementById('tireAlert'),
        fuelAlert: document.getElementById('fuelAlert'),
        weatherAlert: document.getElementById('weatherAlert')
    };

    // --- Helper Functions ---
    function formatTime(timeInSeconds) {
        if (timeInSeconds === null || timeInSeconds === undefined || timeInSeconds <= 0) {
            return "--:--.---";
        }
        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = Math.floor(timeInSeconds % 60);
        const milliseconds = Math.floor((timeInSeconds * 1000) % 1000);
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`;
    }

    function updateText(element, value, defaultValue = '---') {
        if (element) {
            element.textContent = (value !== null && value !== undefined) ? value : defaultValue;
        }
    }

    function updateProgress(barElement, valueElement, value, max = 1) {
        if (barElement) barElement.value = value;
        if (valueElement) valueElement.textContent = `${Math.round(value / max * 100)}%`;
    }

     function updateDamageValue(element, value) {
        if (!element) return;
        
        // Ensure we're working with a number
        const numValue = parseInt(value, 10) || 0;
        
        // Update the text content
        element.textContent = numValue;
        
        // Remove existing classes
        element.classList.remove('damage-value-low', 'damage-value-medium', 'damage-value-high');
        
        // Add appropriate class based on damage amount
        if (numValue > 50) {
            element.classList.add('damage-value-high');
        } else if (numValue > 20) {
            element.classList.add('damage-value-medium');
        } else if (numValue > 0) {
            element.classList.add('damage-value-low');
        }
    }

    // Delta timing calculation and display
    function updateDeltaTiming(currentLapTime, referenceLapTime) {
        if (!elements.deltaTime || !currentLapTime || !referenceLapTime) return;
        
        const delta = currentLapTime - referenceLapTime;
        const deltaText = delta >= 0 ? `+${delta.toFixed(3)}` : delta.toFixed(3);
        
        elements.deltaTime.textContent = deltaText;
        elements.deltaTime.classList.remove('delta-positive', 'delta-negative', 'delta-neutral');
        
        if (delta > 0.1) {
            elements.deltaTime.classList.add('delta-positive');
        } else if (delta < -0.1) {
            elements.deltaTime.classList.add('delta-negative');
        } else {
            elements.deltaTime.classList.add('delta-neutral');
        }
    }

    // Sector time analysis
    function updateSectorAnalysis(sectorIndex, sectorTime) {
        const sectorElements = [elements.sector1, elements.sector2, elements.sector3];
        const sectorTimeElements = [elements.sector1Time, elements.sector2Time, elements.sector3Time];
        
        if (sectorIndex < 0 || sectorIndex > 2 || !sectorTimeElements[sectorIndex]) return;
        
        // Update sector time display
        sectorTimeElements[sectorIndex].textContent = sectorTime ? sectorTime.toFixed(1) : '--.-';
        
        // Compare with personal best
        if (sectorTime && bestSectorTimes[sectorIndex]) {
            const element = sectorElements[sectorIndex];
            element.classList.remove('personal-best', 'session-best', 'slower');
            
            if (sectorTime < bestSectorTimes[sectorIndex]) {
                // New personal best
                bestSectorTimes[sectorIndex] = sectorTime;
                element.classList.add('personal-best');
            } else if (sectorTime < bestSectorTimes[sectorIndex] * 1.02) {
                // Within 2% of best - good sector
                element.classList.add('session-best');
            } else {
                // Slower sector
                element.classList.add('slower');
            }
        } else if (sectorTime) {
            // First sector time
            bestSectorTimes[sectorIndex] = sectorTime;
            sectorElements[sectorIndex].classList.add('personal-best');
        }
    }

    // Calculate G-Forces from telemetry
    function calculateGForces(speed, steer, throttle, brake) {
        // Simplified G-force calculation
        // Lateral G = steering input * speed factor
        const speedFactor = speed / 100; // Normalize speed
        const lateralG = Math.abs(steer) * speedFactor * 2.5; // Approximate lateral G
        
        // Longitudinal G = acceleration/deceleration
        const accelerationG = throttle * 1.2; // Positive G from acceleration
        const brakingG = brake * -2.8; // Negative G from braking
        const longitudinalG = accelerationG + brakingG;
        
        return {
            lateral: Math.min(lateralG, 4.0), // Cap at realistic values
            longitudinal: Math.max(-4.0, Math.min(longitudinalG, 2.0))
        };
    }

    // Update fuel strategy calculations
    function updateFuelStrategy(currentFuel, lapNumber, totalLaps = 50) {
        if (!currentLapStartFuel || currentLapStartFuel === currentFuel) return;
        
        // Calculate fuel consumption for this lap
        const lapConsumption = currentLapStartFuel - currentFuel;
        if (lapConsumption > 0) {
            fuelConsumptionHistory.push(lapConsumption);
            
            // Keep only last 5 laps for average
            if (fuelConsumptionHistory.length > 5) {
                fuelConsumptionHistory.shift();
            }
        }
        
        // Calculate average consumption
        if (fuelConsumptionHistory.length > 0) {
            const avgConsumption = fuelConsumptionHistory.reduce((a, b) => a + b) / fuelConsumptionHistory.length;
            
            if (elements.fuelConsumption) {
                elements.fuelConsumption.textContent = `${avgConsumption.toFixed(2)} kg/lap`;
            }
            
            // Calculate pit window
            const remainingLaps = totalLaps - lapNumber;
            const lapsWithCurrentFuel = Math.floor(currentFuel / avgConsumption);
            
            if (lapsWithCurrentFuel < remainingLaps && elements.pitWindow) {
                const pitLapStart = Math.max(lapNumber + 1, lapNumber + lapsWithCurrentFuel - 3);
                const pitLapEnd = lapNumber + lapsWithCurrentFuel;
                elements.pitWindow.textContent = `Lap ${pitLapStart}-${pitLapEnd}`;
                
                // Show fuel alert if pit stop needed soon
                if (lapsWithCurrentFuel <= 5 && elements.fuelAlert) {
                    elements.fuelAlert.style.display = 'flex';
                }
            }
        }
        
        currentLapStartFuel = currentFuel;
    }

    // Advanced strategy alerts
    function checkStrategyAlerts(data) {
        // Tire degradation alert
        if (data.tyreWear && elements.tireAlert) {
            const maxWear = Math.max(
                data.tyreWear.frontLeft || 0,
                data.tyreWear.frontRight || 0,
                data.tyreWear.rearLeft || 0,
                data.tyreWear.rearRight || 0
            );
            
            if (maxWear > 0.8) { // 80% wear
                elements.tireAlert.style.display = 'flex';
            } else {
                elements.tireAlert.style.display = 'none';
            }
        }
        
        // Weather alert (placeholder - would need weather data)
        if (Math.random() < 0.001) { // Very rare random weather alert for demo
            if (elements.weatherAlert) {
                elements.weatherAlert.style.display = 'flex';
                setTimeout(() => {
                    elements.weatherAlert.style.display = 'none';
                }, 30000); // Hide after 30 seconds
            }
        }
    }

    function addEventToList(message, type = 'info') {
        if (!elements.eventList) return;
        // Remove placeholder if present
        const placeholder = elements.eventList.querySelector('.placeholder');
        if (placeholder) placeholder.remove();

        const li = document.createElement('li');
        const timeSpan = document.createElement('span');
        timeSpan.className = 'event-time';
        timeSpan.textContent = new Date().toLocaleTimeString();
        li.appendChild(timeSpan);
        li.appendChild(document.createTextNode(message));
        li.classList.add(`event-${type}`); // Add class for styling

        elements.eventList.appendChild(li); // Add to bottom
        // Keep list trimmed (e.g., last 50 events)
        while (elements.eventList.children.length > 50) {
            elements.eventList.removeChild(elements.eventList.firstChild);
        }
        // Scroll to bottom
        elements.eventList.scrollTop = elements.eventList.scrollHeight;
    }

     // Initial placeholder
    if (elements.eventList && elements.eventList.children.length === 0) {
       const li = document.createElement('li');
       li.textContent = 'Waiting for connection...';
       li.className = 'placeholder';
       elements.eventList.appendChild(li);
    }


    // --- SSE Connection with Performance Options ---
    console.log("Connecting to SSE stream with high-performance options");
    // Use a custom EventSource with a tiny retry timeout for local operation
    const eventSource = new EventSource('/stream');
    
    // Performance optimization - disable default retry backoff for local operation
    eventSource.reconnectionTime = 50; // 50ms reconnection time
    
    // Flag to track if we're getting rapid updates
    let lastMessageTime = 0;
    let messageCount = 0;
    let performanceMode = true; // Enable high-performance mode by default for local operation
    
    eventSource.onopen = function() {
        console.log("SSE Connection Opened with high-performance mode");
        addEventToList("Connected to telemetry stream.", "info");
    };

    eventSource.onerror = function(err) {
        console.error("SSE Error:", err);
        addEventToList("Connection error or stream closed.", "alert");
        // For local operation, attempt aggressive reconnection
        setTimeout(() => {
            if (eventSource.readyState === EventSource.CLOSED) {
                console.log("Attempting aggressive reconnection...");
                location.reload(); // Force page reload for local development
            }
        }, 1000);
    };

    eventSource.onmessage = function(event) {
        // Performance monitoring
        const now = performance.now();
        if (lastMessageTime) {
            const timeDiff = now - lastMessageTime;
            if (timeDiff < 50) { // If we're getting updates faster than 50ms
                messageCount++;
                if (messageCount > 10 && !performanceMode) {
                    console.log("Switching to high-performance mode");
                    performanceMode = true;
                }
            } else {
                messageCount = 0;
            }
        }
        lastMessageTime = now;
        // console.log("Raw SSE Data:", event.data); // Debugging
        try {
            const data = JSON.parse(event.data);
            // console.log("Parsed Data:", data); // Debugging

            // --- Update Dashboard Elements ---

            // Session Info
            updateText(elements.driverName, data.driverName);
            updateText(elements.trackName, data.track);
            updateText(elements.lapNumber, data.lapNumber);
            // Update position with styling for podium spots
            if (elements.position) {
                let position = data.position;
                elements.position.textContent = position;
                
                // Remove all position classes first
                elements.position.classList.remove('position-first', 'position-second', 'position-third');
                
                // Add appropriate class
                if (position === 1) {
                    elements.position.classList.add('position-first');
                } else if (position === 2) {
                    elements.position.classList.add('position-second');
                } else if (position === 3) {
                    elements.position.classList.add('position-third');
                }
            }
            updateText(elements.lapTimeSoFar, formatTime(data.lapTimeSoFar));
            updateText(elements.lastLapTime, formatTime(data.lastLapTime));
            updateText(elements.sector, data.sector);
            
            // Update personal best display
            if (data.lastLapTime && (!personalBestLapTime || data.lastLapTime < personalBestLapTime)) {
                personalBestLapTime = data.lastLapTime;
            }
            if (elements.personalBest) {
                elements.personalBest.textContent = personalBestLapTime ? `PB: ${formatTime(personalBestLapTime)}` : 'PB: --:--.---';
            }
            
            // Update delta timing
            if (personalBestLapTime && data.lapTimeSoFar) {
                updateDeltaTiming(data.lapTimeSoFar, personalBestLapTime);
            }
            
            // Update sector analysis (simplified - would need actual sector times from telemetry)
            if (data.sector !== undefined && data.lapTimeSoFar) {
                const estimatedSectorTime = data.lapTimeSoFar / (data.sector + 1) * 20; // Rough estimate
                updateSectorAnalysis(data.sector, estimatedSectorTime);
            }
            // Update lap validity with proper styling
            updateText(elements.lapValid, data.lapValid ? 'Valid' : 'Invalid');
            if(elements.lapValid) {
                elements.lapValid.classList.remove('valid', 'invalid');
                elements.lapValid.classList.add(data.lapValid ? 'valid' : 'invalid');
            }


            // Check if this is a waiting status message
            if (data.connectionStatus === "waiting_for_data") {
                console.log("Waiting for telemetry data from F1 game...");
                // Keep the dashboard alive but don't update values
                return;
            }
            
            // Gauges & Gear - Direct DOM manipulation for speed
            // Use optional chaining for nested properties and provide defaults
            let currentSpeed = data.speed?.current || 0;
            let currentRPM = data.engineRPM?.current || 0;
            
            // Direct DOM updates for fastest response on critical gauges
            if (speedGauge) speedGauge.set(currentSpeed);
            if (rpmGauge) rpmGauge.set(currentRPM);
            
            // Update gauge value displays directly
            if (elements.speedValue) elements.speedValue.textContent = Math.round(currentSpeed);
            if (elements.rpmValue) elements.rpmValue.textContent = Math.round(currentRPM);
            
            // Update gear display directly
            let gearDisplay = data.gear?.current;
            if (gearDisplay === 0) gearDisplay = 'N';
            if (gearDisplay === -1) gearDisplay = 'R';
            if (elements.gear) elements.gear.textContent = gearDisplay || '1';

            // Inputs - Direct DOM updates for fastest response
            // Throttle
            const throttleValue = data.throttle?.current || 0;
            if (elements.throttleBar) elements.throttleBar.value = throttleValue;
            if (elements.throttleValue) elements.throttleValue.textContent = `${Math.round(throttleValue * 100)}%`;
            
            // Brake
            const brakeValue = data.brake?.current || 0;
            if (elements.brakeBar) elements.brakeBar.value = brakeValue;
            if (elements.brakeValue) elements.brakeValue.textContent = `${Math.round(brakeValue * 100)}%`;
            
            // Update steering if available - accessing property correctly
            if (elements.steeringIndicator) {
                // Access the steering property properly (it's inside data.steer.current)
                const steerValue = data.steer?.current || 0;
                // Map to reasonable rotation range (-90 to 90 degrees)
                const steerAngle = steerValue * 90; 
                elements.steeringIndicator.style.transform = `rotate(${steerAngle}deg)`;
                if (elements.steeringValue) {
                    elements.steeringValue.textContent = `${Math.round(steerValue * 100)}%`;
                }
            }

            // Tyres & Temps
            updateText(elements.tyreCompound, data.tyreCompound);
            updateText(elements.tyreWearFL, (data.tyreWear?.frontLeft * 100)?.toFixed(1), '--');
            updateText(elements.tyreWearFR, (data.tyreWear?.frontRight * 100)?.toFixed(1), '--');
            updateText(elements.tyreWearRL, (data.tyreWear?.rearLeft * 100)?.toFixed(1), '--');
            updateText(elements.tyreWearRR, (data.tyreWear?.rearRight * 100)?.toFixed(1), '--');
            updateText(elements.brakeTempFL, data.brakeTemperature?.frontLeft, '--');
            updateText(elements.brakeTempFR, data.brakeTemperature?.frontRight, '--');
            updateText(elements.brakeTempRL, data.brakeTemperature?.rearLeft, '--');
            updateText(elements.brakeTempRR, data.brakeTemperature?.rearRight, '--');

            // ERS & DRS
             if (elements.drsStatus) {
                 // Check data.drsAvailable and data.drsActive (need drsAvailable from CarStatus packet)
                 const drsAllowed = data.drsAllowed === 1; // Need this field in payload
                 const drsActive = data.drsActive === true;
                 
                 // Update DRS status indicator
                 if (drsActive) {
                     elements.drsStatus.textContent = 'ACTIVE';
                     elements.drsStatus.className = 'status-on';
                 } else if (drsAllowed) {
                     elements.drsStatus.textContent = 'AVAILABLE';
                     elements.drsStatus.className = 'status-available';
                 } else {
                     elements.drsStatus.textContent = 'INACTIVE';
                     elements.drsStatus.className = 'status-off';
                 }
                 
                 // Update wing visual
                 const wingStatus = document.getElementById('wing-status');
                 if (wingStatus) {
                     if (drsActive) {
                         wingStatus.classList.add('open');
                     } else {
                         wingStatus.classList.remove('open');
                     }
                 }
                 
                 // Highlight active ERS mode
                 if (data.ersDeployMode) {
                     document.querySelectorAll('.mode-item').forEach(item => {
                         item.classList.remove('active');
                         if (item.dataset.mode === data.ersDeployMode) {
                             item.classList.add('active');
                         }
                     });
                 }
             }
            updateProgress(elements.ersStoreBar, elements.ersStoreValue, data.ersStoreEnergy || 0, 4000000); // Use data.ersStoreEnergy from CarStatus
            updateText(elements.ersDeployMode, data.ersDeployMode);

            // Advanced Analytics Updates
            // Calculate and display G-Forces
            const gForces = calculateGForces(
                data.speed?.current || 0,
                data.steer?.current || 0,
                data.throttle?.current || 0,
                data.brake?.current || 0
            );
            
            if (elements.gForceLateral) {
                elements.gForceLateral.textContent = `${gForces.lateral.toFixed(1)}G`;
            }
            if (elements.gForceLongitudinal) {
                elements.gForceLongitudinal.textContent = `${gForces.longitudinal.toFixed(1)}G`;
            }
            
            // Update fuel strategy
            if (data.fuelInTank && data.lapNumber) {
                updateFuelStrategy(data.fuelInTank, data.lapNumber);
            }
            
            // Check for strategy alerts
            checkStrategyAlerts(data);
            
            // Update input overlay chart
            updateInputOverlay(
                data.throttle?.current || 0,
                data.brake?.current || 0
            );

            // Damage
            // Damage handling - direct DOM updates for performance
            if (data.damage) {
                // Update damage values directly
                if (elements.damageWingFL) updateDamageValue(elements.damageWingFL, data.damage.frontLeftWing);
                if (elements.damageWingFR) updateDamageValue(elements.damageWingFR, data.damage.frontRightWing);
                if (elements.damageWingR) updateDamageValue(elements.damageWingR, data.damage.rearWing);
                if (elements.damageFloor) updateDamageValue(elements.damageFloor, data.damage.floor);
                if (elements.damageGearbox) updateDamageValue(elements.damageGearbox, data.damage.gearBox);
                if (elements.damageEngine) updateDamageValue(elements.damageEngine, data.damage.engine);
                
                // Update visual indicators for all damage components
                updateDamageVisuals('WingFL', data.damage.frontLeftWing);
                updateDamageVisuals('WingFR', data.damage.frontRightWing);
                updateDamageVisuals('WingR', data.damage.rearWing);
                updateDamageVisuals('Floor', data.damage.floor);
                updateDamageVisuals('Gearbox', data.damage.gearBox);
                updateDamageVisuals('Engine', data.damage.engine);
                
                // Update damage bars if they exist
                const updateDamageBar = (barId, value) => {
                    const bar = document.getElementById(barId);
                    if (bar) {
                        bar.style.width = `${value}%`;
                        // Update color based on damage level
                        bar.classList.remove('damaged-medium', 'damaged-high');
                        if (value > 50) bar.classList.add('damaged-high');
                        else if (value > 20) bar.classList.add('damaged-medium');
                    }
                };
                
                // Update all damage bars
                updateDamageBar('damageBarWingFL', data.damage.frontLeftWing);
                updateDamageBar('damageBarWingFR', data.damage.frontRightWing);
                updateDamageBar('damageBarWingR', data.damage.rearWing);
                updateDamageBar('damageBarFloor', data.damage.floor);
                updateDamageBar('damageBarGearbox', data.damage.gearBox);
                updateDamageBar('damageBarEngine', data.damage.engine);
            }

            // --- Event Handling ---
            // Check for F1 game events (custom format for F1 24 events)
            if (data.event) {
                // Check if this is an F1 game event with code and description
                const eventCode = data.event.code;
                const eventDescription = data.event.description;
                
                if (eventDescription) {
                    // Add event to the list 
                    addEventToList(eventDescription, eventCode);
                    
                    // Handle specific events for special actions
                    switch(eventCode) {
                        case 'SSTA': // Session started
                            // Clear any charts
                            if (window.lapTimeChart) window.lapTimeChart.data.labels = [];
                            if (window.lapTimeChart) window.lapTimeChart.data.datasets[0].data = [];
                            if (window.lapTimeChart) window.lapTimeChart.update();
                            
                            // Play team radio sound (session started)
                            audioContext.playTeamRadio();
                            
                            // Session start message
                            addAICoachMessage('Race Engineer', 'Session started. Good luck out there!');
                            break;
                            
                        // Other events will now be handled by the AI coach system
                        // The server will detect these events and generate appropriate messages
                    }
                }
            }
            
            // Check for AI coach messages from the server
            if (data.aiCoach) {
                const messageType = data.aiCoach.messageType || 'Race Engineer';
                const messageText = data.aiCoach.messageText || 'We\'re analyzing your telemetry data.';
                
                // Add the AI-generated message to the chat
                addAICoachMessage(messageType, messageText);
            }
            
            // Generate additional events from data changes
            if (data.lapCompleted && data.lastLapTime) {
                addEventToList(`Lap ${data.lapNumber - 1} completed: ${formatTime(data.lastLapTime)}`, 'lap');
                
                // If charts are initialized, update them
                if (window.lapTimeChart && data.lastLapTime > 0) {
                    // Add new lap time to chart
                    window.lapTimeChart.data.labels.push(data.lapNumber - 1);
                    window.lapTimeChart.data.datasets[0].data.push(data.lastLapTime);
                    window.lapTimeChart.update();
                }
            }


        } catch (e) {
            console.error("Error processing SSE message:", e);
            console.error("Received data:", event.data); // Log the problematic data
            addEventToList("Error processing telemetry data.", "alert");
        }
    };

    // Input overlay chart data
    let inputHistory = [];
    const MAX_INPUT_HISTORY = 100;

    // Initialize charts and make them globally accessible
    let lapTimeChart, sectorChart, speedTraceChart;
    initializeCharts();
    initializeInputOverlay();
    
    // Function to initialize all charts
    function initializeCharts() {
        // Lap Time Chart
        const lapTimeCtx = document.getElementById('lapTimeChart').getContext('2d');
        window.lapTimeChart = new Chart(lapTimeCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Lap Times',
                    data: [],
                    borderColor: 'rgba(1, 118, 211, 1)',
                    backgroundColor: 'rgba(1, 118, 211, 0.1)',
                    borderWidth: 2,
                    tension: 0.2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return formatTime(context.raw);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            callback: function(value) {
                                return formatTime(value);
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
        
        // Sector Performance Chart
        const sectorCtx = document.getElementById('sectorChart').getContext('2d');
        window.sectorChart = new Chart(sectorCtx, {
            type: 'bar',
            data: {
                labels: ['Sector 1', 'Sector 2', 'Sector 3'],
                datasets: [{
                    label: 'Current Lap',
                    data: [null, null, null],
                    backgroundColor: 'rgba(1, 118, 211, 0.7)',
                    borderWidth: 0
                }, {
                    label: 'Best Lap',
                    data: [null, null, null],
                    backgroundColor: 'rgba(46, 132, 74, 0.7)',
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            boxWidth: 12,
                            padding: 10
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatTime(context.raw);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            callback: function(value) {
                                return formatTime(value);
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
        
        // Speed Trace Chart
        const speedTraceCtx = document.getElementById('speedTraceChart').getContext('2d');
        window.speedTraceChart = new Chart(speedTraceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Current Lap',
                    data: [],
                    borderColor: 'rgba(1, 118, 211, 1)',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0
                }, {
                    label: 'Best Lap',
                    data: [],
                    borderColor: 'rgba(46, 132, 74, 0.7)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            boxWidth: 12,
                            padding: 10
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 350,
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        title: {
                            display: true,
                            text: 'Speed (km/h)',
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        title: {
                            display: true,
                            text: 'Lap Distance',
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                }
            }
        });
    }
    
    // Initialize input overlay chart
    function initializeInputOverlay() {
        const canvas = elements.inputOverlayChart;
        if (!canvas) return;
        
        // Set canvas size
        canvas.width = canvas.offsetWidth * 2; // High DPI
        canvas.height = canvas.offsetHeight * 2;
        canvas.style.width = canvas.offsetWidth + 'px';
        canvas.style.height = canvas.offsetHeight + 'px';
        
        const ctx = canvas.getContext('2d');
        ctx.scale(2, 2); // Scale for high DPI
        
        // Store context for later use
        canvas.ctx = ctx;
    }
    
    // Update input overlay chart
    function updateInputOverlay(throttle, brake) {
        const canvas = elements.inputOverlayChart;
        if (!canvas || !canvas.ctx) return;
        
        const ctx = canvas.ctx;
        const width = canvas.offsetWidth;
        const height = canvas.offsetHeight;
        
        // Add current input data to history
        inputHistory.push({ throttle, brake, time: Date.now() });
        
        // Limit history size
        if (inputHistory.length > MAX_INPUT_HISTORY) {
            inputHistory.shift();
        }
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        if (inputHistory.length < 2) return;
        
        // Draw throttle line (green)
        ctx.strokeStyle = '#2ecc71';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        inputHistory.forEach((point, index) => {
            const x = (index / MAX_INPUT_HISTORY) * width;
            const y = height - (point.throttle * height);
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
        
        // Draw brake line (red)
        ctx.strokeStyle = '#e74c3c';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        inputHistory.forEach((point, index) => {
            const x = (index / MAX_INPUT_HISTORY) * width;
            const y = height - (point.brake * height);
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
        
        // Draw center line
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.stroke();
    }
    
    // Updated functions for updating charts with real data
    function updateLapTimeChart(chart, lapNumber, lapTime) {
        // Add new lap data
        lapData.labels.push(lapNumber);
        lapData.times.push(lapTime);
        
        // Update personal best if applicable
        if (lapData.personalBest === null || lapTime < lapData.personalBest) {
            lapData.personalBest = lapTime;
        }
        
        // Update chart
        chart.data.labels = lapData.labels;
        chart.data.datasets[0].data = lapData.times;
        chart.update();
    }
    
    function updateSectorChart(chart, sectorTimes, lapNumber) {
        // Add new sector data
        if (sectorTimes && sectorTimes.length === 3) {
            sectorData.labels.push(lapNumber);
            sectorData.sector1.push(sectorTimes[0]);
            sectorData.sector2.push(sectorTimes[1]);
            sectorData.sector3.push(sectorTimes[2]);
            
            // Update best sectors if applicable
            if (sectorData.bestSector1 === null || sectorTimes[0] < sectorData.bestSector1) {
                sectorData.bestSector1 = sectorTimes[0];
            }
            if (sectorData.bestSector2 === null || sectorTimes[1] < sectorData.bestSector2) {
                sectorData.bestSector2 = sectorTimes[1];
            }
            if (sectorData.bestSector3 === null || sectorTimes[2] < sectorData.bestSector3) {
                sectorData.bestSector3 = sectorTimes[2];
            }
            
            // Update chart
            chart.data.datasets[0].data = [sectorTimes[0], sectorTimes[1], sectorTimes[2]];
            chart.data.datasets[1].data = [
                sectorData.bestSector1, 
                sectorData.bestSector2, 
                sectorData.bestSector3
            ];
            chart.update();
        }
    }
    
    function updateSpeedTraceChart(chart, distancePoints, speeds, isBestLap) {
        // Clear current lap data if starting new lap
        if (distancePoints[0] === 0) {
            speedTraceData.labels = distancePoints.map(d => d + '%');
            speedTraceData.currentLap = speeds;
            
            // If this is marked as best lap, update best lap data
            if (isBestLap) {
                speedTraceData.bestLap = speeds;
            }
            
            // Update chart
            chart.data.labels = speedTraceData.labels;
            chart.data.datasets[0].data = speedTraceData.currentLap;
            chart.data.datasets[1].data = speedTraceData.bestLap;
            chart.update();
        }
    }
    
    // Function to create and set up audio context for team radio
    const audioContext = {
        sound: null,
        initialized: false,
        
        init: function() {
            if (this.initialized) return true;
            
            try {
                // Create the audio element
                this.sound = new Audio('/static/assets/TeamRadioF1FX.wav');
                
                // Add event listeners
                this.sound.addEventListener('error', (e) => {
                    console.error('Audio error:', e);
                    // Try to reload if there was an error
                    this.sound.src = '/static/assets/TeamRadioF1FX.wav';
                });
                
                // Mark as initialized
                this.initialized = true;
                console.log('Audio system initialized successfully');
                
                // Play a silent sound to unlock audio in browsers that require user interaction
                this.unlockAudio();
                
                return true;
            } catch (e) {
                console.error('Error initializing audio:', e);
                return false;
            }
        },
        
        // Try to unlock audio playback (many browsers require user interaction)
        unlockAudio: function() {
            document.addEventListener('click', () => {
                // Create and play a silent sound to unlock audio
                const silentSound = new Audio("data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABBwBXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/7UGQAAAAwsTABMAGRBQMCAgABsQwQAAcvZ32pz4sIAACcAAAAAIEgm0HCbAAUZ8C0xwS6wYbFXWf7f9fd1/t2b3+rKdHAQZFgIQCHfBARjCBKfbX8oGAQQSCGSBQAZQwBjlBAoDgYBkG0gGMgJ5gZoB4eDhEJMAzwDaQCWAGmAM6AGGAMkASkA7UAH4APIA3QAgIAZYATIAOEAA0ABEAE9AASQGqAD7AEZABGAB8AC2gFcAE0BxgFvALYAFIAHWAGEACcgJAQ0FBb/+1JkAP/wAABpAAAACAAADSAAAAEAAAGkAAAAIAAANIAAAAT/qpC2goLPKaU3//XUdX//1f/////1qOB0FBQUFD0dBQUFBQcjgoKCgoO40FBQUF1oKCgoKCkLgoKCgpXdBQVE0PW+oDhKr9///0///65///9f2ovHgoKCgoejoKCgoIEYKCiQUSgqqDAqpMQU1FMy45OS41VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/7UmQAD/AAAGkAAAAIAAANIAAAAQAAAaQAAAAgAAA0gAAABFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV");
                silentSound.play().catch(e => console.log('Silent sound playback prevented, need user interaction first'));
                
                // Also try to play the real sound
                this.sound.play().catch(e => console.log('Radio sound playback prevented, need user interaction first'));
                
                // Only needs to happen once
                document.removeEventListener('click', this.unlockAudio);
            }, { once: true });
        },
        
        playTeamRadio: function() {
            if (!this.initialized && !this.init()) return;
            
            try {
                // Reset audio position
                this.sound.currentTime = 0;
                
                // Try to play (will fail silently if browser needs user interaction first)
                const playPromise = this.sound.play();
                
                // Handle play promise
                if (playPromise !== undefined) {
                    playPromise.catch(e => {
                        console.warn('Could not play team radio sound:', e);
                        // Log detailed error info
                        if (e.name === 'NotAllowedError') {
                            console.info('Audio playback requires user interaction first - click anywhere on the page');
                        }
                    });
                }
            } catch (e) {
                console.error('Error playing team radio:', e);
            }
        }
    };
    
    // Initialize audio system
    audioContext.init();

    // Text-to-Speech setup for race radio messages
    const speechSynthesis = window.speechSynthesis;
    const ttsContext = {
        enabled: true,
        speaking: false,
        voice: null,
        rate: 1.1,
        pitch: 0.9,
        volume: 1.0,
        
        // Initialize TTS with proper voice
        init: function() {
            // Check if speech synthesis is available
            if (!window.speechSynthesis) {
                console.error("Speech synthesis not supported in this browser");
                return false;
            }
            
            // Wait for voices to be loaded
            if (speechSynthesis.onvoiceschanged !== undefined) {
                speechSynthesis.onvoiceschanged = this.setVoice.bind(this);
            }
            
            // Initial voice setup (may be called before voices are loaded)
            this.setVoice();
            
            // Try to unlock TTS with user interaction (similar to audio context unlock)
            document.addEventListener('click', () => {
                // Try to speak a silent message to unlock TTS
                this.speak("");
                console.log("Attempting to unlock speech synthesis");
            }, { once: true });
            
            return true;
        },
        
        // Select a good male voice for race engineer
        setVoice: function() {
            let voices = speechSynthesis.getVoices();
            if (!voices || voices.length === 0) {
                console.warn("No voices available yet, will retry later");
                // Retry after a short delay if no voices are available
                setTimeout(() => {
                    voices = speechSynthesis.getVoices();
                    if (voices && voices.length > 0) {
                        console.log(`Found ${voices.length} voices after delay`);
                        this.selectVoiceFromList(voices);
                    } else {
                        console.error("Still no voices available after delay");
                    }
                }, 1000);
                return;
            }
            
            this.selectVoiceFromList(voices);
        },
        
        selectVoiceFromList: function(voices) {
            console.log(`Selecting from ${voices.length} available voices`);
            
            // Log all available voices for debugging
            voices.forEach((voice, i) => {
                console.log(`Voice ${i}: ${voice.name} (${voice.lang}) - Default: ${voice.default}`);
            });
            
            // Try to find a male English voice
            // Preferred voices in order: UK English Male > US English Male > Any English > Default
            const preferredVoices = [
                'UK English Male',
                'Google UK English Male',
                'Microsoft George - English (United Kingdom)',
                'English United Kingdom',
                'US English Male',
                'Google US English',
                'Microsoft David - English (United States)',
                'English United States'
            ];
            
            // Look for preferred voices
            for (const preferredName of preferredVoices) {
                const found = voices.find(voice => 
                    voice.name.includes(preferredName) || 
                    (voice.name.toLowerCase().includes('male') && voice.lang.startsWith('en'))
                );
                if (found) {
                    this.voice = found;
                    console.log(`Selected TTS voice: ${found.name} (${found.lang})`);
                    return;
                }
            }
            
            // Fallback to any English voice
            const anyEnglishVoice = voices.find(voice => voice.lang.startsWith('en'));
            if (anyEnglishVoice) {
                this.voice = anyEnglishVoice;
                console.log(`Using fallback English voice: ${anyEnglishVoice.name}`);
                return;
            }
            
            // Last resort: use the first available voice
            if (voices.length > 0) {
                this.voice = voices[0];
                console.log(`Using default voice: ${voices[0].name}`);
            }
        },
        
        // Speak a message with radio effect
        speak: function(text) {
            if (!this.enabled) return;
            if (text === "") {
                // Special case for unlocking speech synthesis
                const utterance = new SpeechSynthesisUtterance(" ");
                speechSynthesis.speak(utterance);
                return;
            }
            if (this.speaking) {
                console.log("Already speaking, canceling current speech");
                speechSynthesis.cancel();
            }
            
            try {
                console.log("Attempting to speak:", text);
                
                // Workaround for Chrome and other browsers that pause speech synthesis after 15 seconds
                // See: https://bugs.chromium.org/p/chromium/issues/detail?id=679437
                if (speechSynthesis.paused || speechSynthesis.pending) {
                    console.log("Speech synthesis paused or pending, resetting...");
                    speechSynthesis.cancel();
                }
                
                // Create utterance
                const utterance = new SpeechSynthesisUtterance(text);
                
                // Set voice and parameters for "radio" effect
                if (this.voice) {
                    console.log("Using voice:", this.voice.name);
                    utterance.voice = this.voice;
                } else {
                    // If no voice is selected yet, try to get one now
                    const voices = speechSynthesis.getVoices();
                    console.log(`Found ${voices.length} voices on demand`);
                    if (voices.length > 0) {
                        // Just use the default system voice
                        utterance.voice = voices[0];
                        console.log(`Using system default voice: ${voices[0].name}`);
                    } else {
                        console.warn("No voices available for TTS");
                    }
                }
                
                // Always set these properties to ensure they take effect
                utterance.rate = this.rate;     // Slightly faster for radio feel
                utterance.pitch = this.pitch;   // Lower pitch for male race engineer
                utterance.volume = 1.0;         // Maximum volume to ensure audibility
                
                // Track speaking state
                this.speaking = true;
                utterance.onstart = () => {
                    console.log("Speech started successfully");
                };
                utterance.onend = () => {
                    console.log("Speech completed");
                    this.speaking = false;
                };
                utterance.onerror = (event) => {
                    this.speaking = false;
                    console.error("TTS error occurred:", event);
                    
                    // Try one more time with default settings
                    if (event.error !== "interrupted") {
                        console.log("Retrying with default settings");
                        const retryUtterance = new SpeechSynthesisUtterance(text);
                        retryUtterance.volume = 1.0;
                        speechSynthesis.speak(retryUtterance);
                    }
                };
                
                // Start speaking
                speechSynthesis.speak(utterance);
                
                // Chrome bug workaround - keep speech synthesis active
                const resumeInterval = setInterval(() => {
                    if (!this.speaking) {
                        clearInterval(resumeInterval);
                        return;
                    }
                    
                    if (speechSynthesis.paused) {
                        console.log("Resuming paused speech synthesis");
                        speechSynthesis.resume();
                    }
                }, 1000);
            } catch (e) {
                console.error('TTS error:', e);
                this.speaking = false;
                
                // Fallback to a simple alert for debugging
                alert("Speech synthesis failed. Check browser console for details.");
            }
        },
        
        // Toggle TTS on/off
        toggle: function() {
            this.enabled = !this.enabled;
            return this.enabled;
        }
    };
    
    // Add a test button to ensure TTS works
    const testButton = document.createElement('button');
    testButton.textContent = 'Test TTS';
    testButton.style.position = 'fixed';
    testButton.style.bottom = '10px';
    testButton.style.right = '10px';
    testButton.style.zIndex = '9999';
    testButton.style.padding = '10px';
    testButton.style.backgroundColor = '#0176d3';
    testButton.style.color = 'white';
    testButton.style.border = 'none';
    testButton.style.borderRadius = '4px';
    
    testButton.addEventListener('click', function() {
        console.log("Testing TTS manually");
        // First reset any existing speech synthesis state
        window.speechSynthesis.cancel();
        
        // Try speaking directly with the Web Speech API
        const directUtterance = new SpeechSynthesisUtterance("Testing speech synthesis directly");
        directUtterance.volume = 1.0;
        directUtterance.rate = 1.0;
        directUtterance.pitch = 1.0;
        
        // Add event listeners to diagnose issues
        directUtterance.onstart = () => console.log("Direct speech started");
        directUtterance.onend = () => console.log("Direct speech ended");
        directUtterance.onerror = (e) => console.error("Direct speech error:", e);
        
        window.speechSynthesis.speak(directUtterance);
        
        // Then try with our TTS system after a delay
        setTimeout(() => {
            ttsContext.speak("Testing our TTS system after direct test");
        }, 2000);
    });
    
    document.body.appendChild(testButton);
    
    // Initialize TTS
    ttsContext.init();
    
    // Add a welcome message when the dashboard loads
    addAICoachMessage('Race Engineer', 'Welcome to your AI race engineer. I\'ll provide feedback on your driving and suggest improvements throughout the session.');

    // Function for adding AI coach messages
    function addAICoachMessage(messageType, messageText) {
        const messagesContainer = document.getElementById('ai-coach-messages');
        if (!messagesContainer) return;
        
        // Play team radio notification sound first
        audioContext.playTeamRadio();
        
        // Then speak the message using TTS (after a longer delay to let sound finish and avoid conflicts)
        setTimeout(() => {
            console.log("Sending message to TTS:", messageText);
            // Force unlock speech synthesis if it's still locked
            if (speechSynthesis.speaking) {
                console.log("Speech synthesis still speaking, canceling...");
                speechSynthesis.cancel();
            }
            ttsContext.speak(messageText);
        }, 800);
        
        const currentTime = new Date();
        const timeString = currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const messageEl = document.createElement('div');
        messageEl.className = 'message new-message';
        
        const headerEl = document.createElement('div');
        headerEl.className = 'message-header';
        
        const timeEl = document.createElement('span');
        timeEl.className = 'message-time';
        timeEl.textContent = timeString;
        
        const typeEl = document.createElement('span');
        typeEl.className = 'message-type';
        typeEl.textContent = messageType;
        
        const bodyEl = document.createElement('div');
        bodyEl.className = 'message-body';
        bodyEl.textContent = messageText;
        
        headerEl.appendChild(timeEl);
        headerEl.appendChild(typeEl);
        messageEl.appendChild(headerEl);
        messageEl.appendChild(bodyEl);
        
        messagesContainer.appendChild(messageEl);
        
        // Auto-scroll to the bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Add animation effect then remove it
        setTimeout(() => {
            messageEl.classList.remove('new-message');
        }, 1000);
    }
    
    // Function to update damage indicators on car outline
    function updateDamageVisuals(component, value) {
        // Update indicator on car outline
        const indicator = document.getElementById(`damage-ind-${component.toLowerCase()}`);
        if (indicator) {
            indicator.dataset.value = value || 0;
            
            // Remove existing classes first to avoid stacking
            indicator.classList.remove('damaged-medium', 'damaged-high');
            
            // Add appropriate class based on damage value
            if (value > 50) {
                indicator.classList.add('damaged-high');
            } else if (value > 20) {
                indicator.classList.add('damaged-medium');
            }
            
            // Make sure the indicator is visible if there's any damage
            if (value > 0) {
                indicator.style.display = 'block';
            } else {
                indicator.style.display = 'none';
            }
        }
    }
    
    console.log("EventSource initialized.");
});