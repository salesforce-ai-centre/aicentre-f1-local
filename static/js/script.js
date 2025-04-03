document.addEventListener('DOMContentLoaded', (event) => {
    console.log("Dashboard script loaded.");

    // --- Gauge Configuration ---
    const gaugeOptions = {
        angle: 0.15, // The span of the gauge arc
        lineWidth: 0.2, // The line thickness
        radiusScale: 0.9, // Relative radius
        pointer: {
            length: 0.6, // Relative to gauge radius
            strokeWidth: 0.035, // The thickness
            color: '#000000' // Fill color
        },
        limitMax: false,     // If false, max value increases automatically if value > max
        limitMin: false,     // If true, the min value of the gauge will be fixed
        colorStart: '#6FADCF',   // Colors
        colorStop: '#8FC0DA',    // just experiment with them
        strokeColor: '#E0E0E0',  // to see which ones work best for you
        generateGradient: true,
        highDpiSupport: true,     // High resolution support
        staticZones: [
           // Define zones for color changes if desired (e.g., RPM redline)
           // {strokeStyle: "#F03E3E", min: 10000, max: 13000}, // Red RPM Example
           // {strokeStyle: "#FFDD00", min: 8500, max: 10000} // Yellow RPM Example
        ],
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
    const rpmGauge = new Gauge(rpmGaugeElement).setOptions(gaugeOptions);
    rpmGauge.maxValue = 13000; // Set initial max RPM
    rpmGauge.setMinValue(0);
    rpmGauge.animationSpeed = 32;
    rpmGauge.set(0);

    // Element References (Cache them for performance)
    const elements = {
        driverName: document.getElementById('driverName'),
        trackName: document.getElementById('trackName'),
        lapNumber: document.getElementById('lapNumber'),
        position: document.getElementById('position'), // Added
        lapTimeSoFar: document.getElementById('lapTimeSoFar'),
        lastLapTime: document.getElementById('lastLapTime'),
        sector: document.getElementById('sector'),
        lapValid: document.getElementById('lapValid'),
        gear: document.getElementById('gear'),
        throttleBar: document.getElementById('throttleBar'),
        throttleValue: document.getElementById('throttleValue'),
        brakeBar: document.getElementById('brakeBar'),
        brakeValue: document.getElementById('brakeValue'),
        tyreCompound: document.getElementById('tyreCompound'),
        tyreWearFL: document.getElementById('tyreWearFL'),
        tyreWearFR: document.getElementById('tyreWearFR'),
        tyreWearRL: document.getElementById('tyreWearRL'),
        tyreWearRR: document.getElementById('tyreWearRR'),
        brakeTempFL: document.getElementById('brakeTempFL'),
        brakeTempFR: document.getElementById('brakeTempFR'),
        brakeTempRL: document.getElementById('brakeTempRL'),
        brakeTempRR: document.getElementById('brakeTempRR'),
        drsStatus: document.getElementById('drsStatus'),
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
        eventList: document.getElementById('eventList')
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
        const numValue = parseInt(value, 10) || 0;
        element.textContent = numValue;
        element.classList.remove('damage-value-low', 'damage-value-medium', 'damage-value-high');
        if (numValue > 50) {
            element.classList.add('damage-value-high');
        } else if (numValue > 20) {
            element.classList.add('damage-value-medium');
        } else if (numValue > 0) {
             element.classList.add('damage-value-low');
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


    // --- SSE Connection ---
    console.log("Attempting to connect to SSE stream at /stream");
    const eventSource = new EventSource('/stream');

    eventSource.onopen = function() {
        console.log("SSE Connection Opened.");
         addEventToList("Connected to telemetry stream.", "info");
    };

    eventSource.onerror = function(err) {
        console.error("SSE Error:", err);
        addEventToList("Connection error or stream closed.", "alert");
        // Optionally try to reconnect or inform the user permanently
        // eventSource.close(); // Close to prevent constant retries if server is down
    };

    eventSource.onmessage = function(event) {
        // console.log("Raw SSE Data:", event.data); // Debugging
        try {
            const data = JSON.parse(event.data);
            // console.log("Parsed Data:", data); // Debugging

            // --- Update Dashboard Elements ---

            // Session Info
            updateText(elements.driverName, data.driverName);
            updateText(elements.trackName, data.track);
            updateText(elements.lapNumber, data.lapNumber);
            updateText(elements.position, data.position); // Needs position in payload
            updateText(elements.lapTimeSoFar, formatTime(data.lapTimeSoFar));
            updateText(elements.lastLapTime, formatTime(data.lastLapTime));
            updateText(elements.sector, data.sector);
            updateText(elements.lapValid, data.lapValid ? 'Valid' : 'Invalid');
            if(elements.lapValid) elements.lapValid.style.color = data.lapValid ? 'green' : 'red';


            // Gauges & Gear
            if (speedGauge) speedGauge.set(data.speed?.current || 0);
            if (rpmGauge) rpmGauge.set(data.engineRPM?.current || 0);
            let gearDisplay = data.gear?.current;
            if (gearDisplay === 0) gearDisplay = 'N';
            if (gearDisplay === -1) gearDisplay = 'R';
            updateText(elements.gear, gearDisplay, 'N');

            // Inputs
            updateProgress(elements.throttleBar, elements.throttleValue, data.throttle?.current || 0);
            updateProgress(elements.brakeBar, elements.brakeValue, data.brake?.current || 0);

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
             }
            updateProgress(elements.ersStoreBar, elements.ersStoreValue, data.ersStoreEnergy || 0, 4000000); // Use data.ersStoreEnergy from CarStatus
            updateText(elements.ersDeployMode, data.ersDeployMode);

            // Damage
            updateDamageValue(elements.damageWingFL, data.damage?.frontLeftWing);
            updateDamageValue(elements.damageWingFR, data.damage?.frontRightWing);
            updateDamageValue(elements.damageWingR, data.damage?.rearWing);
            updateDamageValue(elements.damageFloor, data.damage?.floor);
            updateDamageValue(elements.damageGearbox, data.damage?.gearBox);
            updateDamageValue(elements.damageEngine, data.damage?.engine);

            // --- Event Handling ---
            // Check for specific events/alerts within the data
            if (data.event) { // Check if an 'event' field exists
                 addEventToList(data.event.message, data.event.type || 'info');
            } else {
                 // Generate events from data changes (e.g., lap completion)
                 if (data.lapCompleted) {
                     // Avoid duplicate lap completion messages if state isn't managed perfectly
                     // This might need state management if the 'lapCompleted' flag stays true for multiple packets
                    addEventToList(`Lap ${data.lapNumber -1} completed: ${formatTime(data.lastLapTime)}`, 'lap');
                 }
                 // Add more event detection here: Penalties, Flags, Damage thresholds etc.
                 // Example: Check for significant damage change
                 // This requires comparing with previous state, which is complex here.
                 // Better to have the server push specific event messages.
            }


        } catch (e) {
            console.error("Error processing SSE message:", e);
            console.error("Received data:", event.data); // Log the problematic data
            addEventToList("Error processing telemetry data.", "alert");
        }
    };

    console.log("EventSource initialized.");
});