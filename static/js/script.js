document.addEventListener('DOMContentLoaded', (event) => {
    console.log("Enhanced Dashboard script loaded.");

    // Theme Management
    const themeManager = {
        init() {
            const savedTheme = localStorage.getItem('dashboardTheme') || 'dark';
            this.setTheme(savedTheme);

            const toggleBtn = document.getElementById('themeToggle');
            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => this.toggleTheme());
            }
        },

        setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('dashboardTheme', theme);
            this.updateToggleButton(theme);
        },

        toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            this.setTheme(newTheme);
        },

        updateToggleButton(theme) {
            const icon = document.getElementById('themeIcon');
            const text = document.querySelector('.theme-toggle-text');
            if (icon && text) {
                if (theme === 'dark') {
                    icon.textContent = '🌙';
                    text.textContent = 'Light Mode';
                } else {
                    icon.textContent = '☀️';
                    text.textContent = 'Dark Mode';
                }
            }
        }
    };

    // Initialize theme
    themeManager.init();

    // Simple helper to update DOM elements only when value changes
    function updateElement(element, newValue, formatter = null) {
        if (!element) return;

        const displayValue = formatter ? formatter(newValue) : newValue;
        if (element.textContent !== displayValue) {
            element.textContent = displayValue;
        }
    }

    // Icon mapping for events
    const eventIcons = {
        'lap': '🏁',
        'damage': '⚠️',
        'warning': '⚡',
        'tire': '🔧',
        'fuel': '⛽',
        'drs': '🚀',
        'pit': '🔧',
        'info': 'ℹ️',
        'success': '✅'
    };

    // Get event icon based on message content
    function getEventIcon(message) {
        const lowerMsg = message.toLowerCase();
        if (lowerMsg.includes('lap')) return eventIcons.lap;
        if (lowerMsg.includes('damage')) return eventIcons.damage;
        if (lowerMsg.includes('tyre') || lowerMsg.includes('tire')) return eventIcons.tire;
        if (lowerMsg.includes('fuel')) return eventIcons.fuel;
        if (lowerMsg.includes('drs')) return eventIcons.drs;
        if (lowerMsg.includes('pit')) return eventIcons.pit;
        if (lowerMsg.includes('warning') || lowerMsg.includes('critical')) return eventIcons.warning;
        return eventIcons.info;
    }

    // Get event class based on message type
    function getEventClass(message) {
        const lowerMsg = message.toLowerCase();
        if (lowerMsg.includes('damage') || lowerMsg.includes('critical')) return 'event-damage';
        if (lowerMsg.includes('warning') || lowerMsg.includes('tire')) return 'event-warning';
        if (lowerMsg.includes('lap') || lowerMsg.includes('best')) return 'event-success';
        return 'event-info';
    }

    // Enhanced event logging with icons
    function addEventMessage(message, timestamp = null) {
        const eventContainer = document.querySelector('.event-messages') || document.getElementById('eventLog');
        if (!eventContainer) return;

        const eventDiv = document.createElement('div');
        eventDiv.className = `event-message ${getEventClass(message)} new-message`;

        const icon = document.createElement('span');
        icon.className = 'event-icon';
        icon.textContent = getEventIcon(message);

        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;

        const timeSpan = document.createElement('span');
        timeSpan.className = 'event-timestamp';
        timeSpan.textContent = timestamp || new Date().toLocaleTimeString('en-US', { hour12: false });

        eventDiv.appendChild(icon);
        eventDiv.appendChild(messageSpan);
        eventDiv.appendChild(timeSpan);

        eventContainer.insertBefore(eventDiv, eventContainer.firstChild);

        // Remove "new-message" class after animation
        setTimeout(() => eventDiv.classList.remove('new-message'), 800);

        // Limit to 20 events
        while (eventContainer.children.length > 20) {
            eventContainer.removeChild(eventContainer.lastChild);
        }
    }

    // Enhanced AI Coach messages with icons
    function addAIMessage(message, type = 'info') {
        const container = document.getElementById('aiCoachMessages');
        if (!container) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'ai-message new-message';

        const icon = document.createElement('span');
        icon.className = 'ai-message-icon';
        icon.textContent = type === 'strategy' ? '🎯' :
                          type === 'warning' ? '⚠️' :
                          type === 'tip' ? '💡' : 'ℹ️';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'ai-message-content';

        const typeDiv = document.createElement('div');
        typeDiv.className = 'ai-message-type';
        typeDiv.textContent = type.charAt(0).toUpperCase() + type.slice(1);

        const textDiv = document.createElement('div');
        textDiv.className = 'ai-message-text';
        textDiv.textContent = message;

        contentDiv.appendChild(typeDiv);
        contentDiv.appendChild(textDiv);

        messageDiv.appendChild(icon);
        messageDiv.appendChild(contentDiv);

        container.insertBefore(messageDiv, container.firstChild);

        // Remove animation class
        setTimeout(() => messageDiv.classList.remove('new-message'), 800);

        // Limit messages
        while (container.children.length > 10) {
            container.removeChild(container.lastChild);
        }
    }

    // Initialize gauges
    let speedGauge = null;
    let rpmGauge = null;

    function initGauges() {
        const speedCanvas = document.getElementById('speedGauge');
        const rpmCanvas = document.getElementById('rpmGauge');

        if (speedCanvas && typeof Gauge !== 'undefined') {
            const opts = {
                angle: -0.15,
                lineWidth: 0.2,
                radiusScale: 0.8,
                pointer: {
                    length: 0.6,
                    strokeWidth: 0.035,
                    color: '#000000'
                },
                limitMax: false,
                limitMin: false,
                colorStart: '#0176d3',
                colorStop: '#0176d3',
                strokeColor: '#E0E0E0',
                generateGradient: true,
                highDpiSupport: true,
                staticZones: [
                    {strokeStyle: "#30B32D", min: 0, max: 200},
                    {strokeStyle: "#FFDD00", min: 200, max: 280},
                    {strokeStyle: "#F03E3E", min: 280, max: 350}
                ],
                staticLabels: {
                    font: "10px sans-serif",
                    labels: [0, 50, 100, 150, 200, 250, 300, 350],
                    color: "#000000",
                    fractionDigits: 0
                }
            };

            speedGauge = new Gauge(speedCanvas).setOptions(opts);
            speedGauge.maxValue = 350;
            speedGauge.setMinValue(0);
            speedGauge.animationSpeed = 32;
            speedGauge.set(0);
        }

        if (rpmCanvas && typeof Gauge !== 'undefined') {
            const rpmOpts = {
                angle: -0.15,
                lineWidth: 0.2,
                radiusScale: 0.8,
                pointer: {
                    length: 0.6,
                    strokeWidth: 0.035,
                    color: '#000000'
                },
                limitMax: false,
                limitMin: false,
                percentColors: [[0.0, "#30B32D"], [0.80, "#FFDD00"], [1.0, "#F03E3E"]],
                strokeColor: '#E0E0E0',
                generateGradient: true,
                highDpiSupport: true
            };

            rpmGauge = new Gauge(rpmCanvas).setOptions(rpmOpts);
            rpmGauge.maxValue = 15000;
            rpmGauge.setMinValue(0);
            rpmGauge.animationSpeed = 32;
            rpmGauge.set(0);
        }
    }

    // Initialize lap chart
    let lapChart = null;
    function initLapChart() {
        const ctx = document.getElementById('lapChart');
        if (ctx && typeof Chart !== 'undefined') {
            // Get computed styles for theming
            const styles = getComputedStyle(document.documentElement);
            const textColor = styles.getPropertyValue('--chart-text-color') || '#666';
            const gridColor = styles.getPropertyValue('--chart-grid-color') || 'rgba(0,0,0,0.1)';

            lapChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Lap Time',
                        data: [],
                        borderColor: '#0176d3',
                        backgroundColor: 'rgba(1, 118, 211, 0.1)',
                        borderWidth: 2,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: gridColor
                            },
                            ticks: {
                                color: textColor
                            }
                        },
                        y: {
                            grid: {
                                color: gridColor
                            },
                            ticks: {
                                color: textColor,
                                callback: function(value) {
                                    return formatLapTime(value);
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // Initialize throttle/brake overlay chart
    let inputChart = null;
    function initInputChart() {
        const ctx = document.getElementById('inputOverlayChart');
        if (ctx && typeof Chart !== 'undefined') {
            const styles = getComputedStyle(document.documentElement);
            const gridColor = styles.getPropertyValue('--chart-grid-color') || 'rgba(0,0,0,0.1)';

            inputChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Array(50).fill(''),
                    datasets: [{
                        label: 'Throttle',
                        data: Array(50).fill(0),
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        borderWidth: 2,
                        tension: 0
                    }, {
                        label: 'Brake',
                        data: Array(50).fill(0),
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        borderWidth: 2,
                        tension: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            display: false
                        },
                        y: {
                            min: 0,
                            max: 100,
                            display: false
                        }
                    }
                }
            });
        }
    }

    // Update input chart with new data
    function updateInputChart(throttle, brake) {
        if (!inputChart) return;

        // Shift and add new data
        inputChart.data.datasets[0].data.shift();
        inputChart.data.datasets[0].data.push(throttle);

        inputChart.data.datasets[1].data.shift();
        inputChart.data.datasets[1].data.push(brake);

        inputChart.update('none');
    }

    // Helper function to format lap time
    function formatLapTime(seconds) {
        if (seconds === null || seconds === undefined || seconds === 0) return "--:--.---";
        const minutes = Math.floor(seconds / 60);
        const secs = (seconds % 60).toFixed(3);
        return `${minutes}:${secs.padStart(6, '0')}`;
    }

    // F1 game tire array indices (matches game spec: RL, RR, FL, FR)
    const TIRE_INDEX_RL = 0;
    const TIRE_INDEX_RR = 1;
    const TIRE_INDEX_FL = 2;
    const TIRE_INDEX_FR = 3;

    // Tire temperature and wear thresholds
    const TIRE_TEMP_MIN = 80;   // Below this is too cold
    const TIRE_TEMP_MAX = 105;  // Above this is too hot
    const TIRE_WEAR_CRITICAL = 70;  // Percent

    // Enhanced tyre visualization with critical highlighting
    function updateTyreVisualization(tyreData) {
        const tyres = ['FrontLeft', 'FrontRight', 'RearLeft', 'RearRight'];

        tyres.forEach(tyre => {
            const tyreElement = document.getElementById(`tyre${tyre}`);
            if (!tyreElement) return;

            const wear = tyreData[`${tyre.toLowerCase()}Wear`] || 0;
            const temp = tyreData[`${tyre.toLowerCase()}Temp`] || 0;

            // Remove existing classes
            tyreElement.classList.remove('critical-wear', 'critical-temp');

            // Add critical wear highlighting
            if (wear > TIRE_WEAR_CRITICAL) {
                tyreElement.classList.add('critical-wear');
            }

            // Add critical temp highlighting
            if (temp > TIRE_TEMP_MAX || temp < TIRE_TEMP_MIN) {
                tyreElement.classList.add('critical-temp');
            }
        });
    }

    // 2D G-Force meter update
    function updateGForceMeter(lateral, longitudinal) {
        const dot = document.getElementById('gForceDot');
        if (!dot) return;

        // Clamp values to -2g to +2g range
        const maxG = 2;
        lateral = Math.max(-maxG, Math.min(maxG, lateral));
        longitudinal = Math.max(-maxG, Math.min(maxG, longitudinal));

        // Convert to percentage (50% = center)
        const x = 50 + (lateral / maxG) * 40;
        const y = 50 - (longitudinal / maxG) * 40;

        dot.style.left = `${x}%`;
        dot.style.top = `${y}%`;

        // Update text values
        updateElement(document.getElementById('gLateral'), `${lateral.toFixed(1)}g`);
        updateElement(document.getElementById('gLongitudinal'), `${longitudinal.toFixed(1)}g`);
    }

    // Enhanced visual progress bars for throttle/brake
    function updateVisualInputs(throttle, brake) {
        const throttleBar = document.getElementById('throttleVisual');
        const brakeBar = document.getElementById('brakeVisual');

        if (throttleBar) {
            throttleBar.style.width = `${throttle}%`;
            const throttleText = document.getElementById('throttlePercent');
            if (throttleText) throttleText.textContent = `${Math.round(throttle)}%`;
        }

        if (brakeBar) {
            brakeBar.style.width = `${brake}%`;
            const brakeText = document.getElementById('brakePercent');
            if (brakeText) brakeText.textContent = `${Math.round(brake)}%`;
        }

        // Update overlay chart
        updateInputChart(throttle, brake);
    }

    // Initialize everything
    initGauges();
    initLapChart();
    initInputChart();

    // SSE Connection
    let eventSource = null;
    let reconnectTimer = null;
    let reconnectAttempts = 0;

    function connectSSE() {
        if (eventSource) {
            eventSource.close();
        }

        eventSource = new EventSource('/stream');

        eventSource.onopen = function() {
            console.log('SSE connection established');
            reconnectAttempts = 0;
            updateConnectionStatus('connected');
            addEventMessage('Connected to telemetry stream');
        };

        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };

        eventSource.onerror = function(error) {
            console.error('SSE error:', error);
            updateConnectionStatus('disconnected');
            eventSource.close();

            // Exponential backoff reconnection
            reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);

            if (reconnectTimer) clearTimeout(reconnectTimer);
            reconnectTimer = setTimeout(() => {
                console.log(`Reconnecting SSE (attempt ${reconnectAttempts})...`);
                connectSSE();
            }, delay);
        };
    }

    function updateConnectionStatus(status) {
        const indicator = document.getElementById('connectionStatus');
        const text = document.getElementById('connectionText');

        if (indicator) {
            indicator.className = 'status-indicator ' + status;
        }

        if (text) {
            text.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
    }

    function updateDashboard(data) {
        if (!data) return;

        // Update connection quality
        updateDataQuality(data);

        // Session info
        updateElement(document.getElementById('driverName'), data.driverName || '-');
        updateElement(document.getElementById('trackName'), data.trackName || '-');
        updateElement(document.getElementById('position'), data.position || '-');
        updateElement(document.getElementById('currentLap'), data.currentLap || '-');

        // Update position badge
        const posBadge = document.getElementById('positionBadge');
        if (posBadge) {
            posBadge.textContent = data.position || '-';
            posBadge.className = 'position-badge';
            if (data.position == 1) posBadge.classList.add('position-first');
            else if (data.position == 2) posBadge.classList.add('position-second');
            else if (data.position == 3) posBadge.classList.add('position-third');
        }

        // Lap times
        updateElement(document.getElementById('currentLapTime'),
            formatLapTime(data.currentLapTime), null, 100);
        updateElement(document.getElementById('lastLapTime'),
            formatLapTime(data.lastLapTime), null, 100);

        // Lap validity
        const lapValid = document.getElementById('lapValid');
        if (lapValid) {
            const isValid = data.currentLapInvalid === false;
            lapValid.textContent = isValid ? 'VALID' : 'INVALID';
            lapValid.className = 'metric-value status-pill ' + (isValid ? 'valid' : 'invalid');
        }

        // Speed and RPM
        if (speedGauge) speedGauge.set(data.speed || 0);
        if (rpmGauge) rpmGauge.set(data.engineRPM || 0);

        updateElement(document.getElementById('speedValue'),
            `${Math.round(data.speed || 0)} km/h`, null, 50);
        updateElement(document.getElementById('rpmValue'),
            Math.round(data.engineRPM || 0), null, 50);

        // Gear
        updateElement(document.getElementById('gear'),
            data.gear === 0 ? 'N' : data.gear === -1 ? 'R' : data.gear || 'N');

        // Enhanced visual inputs
        updateVisualInputs(
            (data.throttle || 0) * 100,
            (data.brake || 0) * 100
        );

        // Steering
        const steeringDegrees = (data.steer || 0) * 90;
        const steeringIndicator = document.getElementById('steeringIndicator');
        if (steeringIndicator) {
            steeringIndicator.style.transform = `rotate(${steeringDegrees}deg)`;
        }
        updateElement(document.getElementById('steeringValue'),
            `${steeringDegrees.toFixed(0)}°`, null, 50);

        // Tyres with critical highlighting
        if (data.tyresWear) {
            const tyreData = {
                frontleftWear: data.tyresWear[TIRE_INDEX_FL] || 0,
                frontrightWear: data.tyresWear[TIRE_INDEX_FR] || 0,
                rearleftWear: data.tyresWear[TIRE_INDEX_RL] || 0,
                rearrightWear: data.tyresWear[TIRE_INDEX_RR] || 0,
                frontleftTemp: data.tyresSurfaceTemperature?.[TIRE_INDEX_FL] || 0,
                frontrightTemp: data.tyresSurfaceTemperature?.[TIRE_INDEX_FR] || 0,
                rearleftTemp: data.tyresSurfaceTemperature?.[TIRE_INDEX_RL] || 0,
                rearrightTemp: data.tyresSurfaceTemperature?.[TIRE_INDEX_RR] || 0
            };

            updateTyreVisualization(tyreData);

            // Update individual tyre values
            updateElement(document.getElementById('tyreFLWear'),
                `${Math.round(tyreData.frontleftWear)}%`);
            updateElement(document.getElementById('tyreFRWear'),
                `${Math.round(tyreData.frontrightWear)}%`);
            updateElement(document.getElementById('tyreRLWear'),
                `${Math.round(tyreData.rearleftWear)}%`);
            updateElement(document.getElementById('tyreRRWear'),
                `${Math.round(tyreData.rearrightWear)}%`);

            updateElement(document.getElementById('tyreFLTemp'),
                `${Math.round(tyreData.frontleftTemp)}°C`);
            updateElement(document.getElementById('tyreFRTemp'),
                `${Math.round(tyreData.frontrightTemp)}°C`);
            updateElement(document.getElementById('tyreRLTemp'),
                `${Math.round(tyreData.rearleftTemp)}°C`);
            updateElement(document.getElementById('tyreRRTemp'),
                `${Math.round(tyreData.rearrightTemp)}°C`);
        }

        updateElement(document.getElementById('tyreCompound'),
            data.actualTyreCompound || '-');

        // ERS & DRS
        const drsStatus = document.getElementById('drsStatus');
        if (drsStatus && data.drs !== undefined) {
            const status = data.drs === 1 ? 'ACTIVE' :
                          data.drsAvailable ? 'AVAILABLE' : 'INACTIVE';
            drsStatus.textContent = status;
            drsStatus.className = data.drs === 1 ? 'status-on' :
                                 data.drsAvailable ? 'status-available' : 'status-off';
        }

        const ersBar = document.getElementById('ersStoreBar');
        if (ersBar) ersBar.value = data.ersStoreEnergy || 0;
        updateElement(document.getElementById('ersPercent'),
            `${Math.round((data.ersStoreEnergy || 0) / 4000000 * 100)}%`);
        updateElement(document.getElementById('ersDeployMode'),
            data.ersDeployMode || 'None');

        // Damage
        updateDamageDisplay(data);

        // G-Force meter
        updateGForceMeter(data.gForceLateral || 0, data.gForceLongitudinal || 0);

        // Fuel info
        updateElement(document.getElementById('fuelLoad'),
            `${(data.fuelInTank || 0).toFixed(1)}kg`);
        updateElement(document.getElementById('fuelMix'),
            data.fuelMix || 'Standard');
        updateElement(document.getElementById('fuelLaps'),
            data.fuelRemainingLaps ? data.fuelRemainingLaps.toFixed(1) : '-');

        // Events
        if (data.event) {
            addEventMessage(data.event.message);

            // AI Coach message
            if (data.aiCoachMessage) {
                addAIMessage(data.aiCoachMessage, data.event.type || 'info');
            }
        }

        // Lap chart
        if (data.lapCompleted && lapChart) {
            const lapNum = lapChart.data.labels.length + 1;
            lapChart.data.labels.push(`Lap ${lapNum}`);
            lapChart.data.datasets[0].data.push(data.lastLapTime);

            // Keep only last 20 laps
            if (lapChart.data.labels.length > 20) {
                lapChart.data.labels.shift();
                lapChart.data.datasets[0].data.shift();
            }

            lapChart.update();
        }
    }

    function updateDamageDisplay(data) {
        const components = [
            { id: 'FL', value: data.frontLeftWingDamage },
            { id: 'FR', value: data.frontRightWingDamage },
            { id: 'Rear', value: data.rearWingDamage },
            { id: 'Floor', value: data.floorDamage },
            { id: 'Engine', value: data.engineDamage },
            { id: 'Gearbox', value: data.gearBoxDamage }
        ];

        components.forEach(comp => {
            const damage = comp.value || 0;
            const bar = document.getElementById(`damageBar${comp.id}`);
            const text = document.getElementById(`damage${comp.id}`);

            if (bar) {
                bar.style.width = `${damage}%`;
                bar.className = 'damage-bar';
                if (damage > 50) bar.classList.add('damaged-high');
                else if (damage > 20) bar.classList.add('damaged-medium');
            }

            if (text) {
                text.textContent = `${damage}%`;
                text.className = 'damage-value';
                if (damage > 50) text.className += ' damage-value-high';
                else if (damage > 20) text.className += ' damage-value-medium';
                else text.className += ' damage-value-low';
            }
        });
    }

    function updateDataQuality(data) {
        const indicator = document.getElementById('dataQuality');
        const text = document.getElementById('dataQualityText');

        if (!indicator || !text) return;

        // Simple quality assessment based on data completeness
        let quality = 'excellent';
        let qualityText = 'Excellent';

        if (!data.speed || !data.engineRPM) {
            quality = 'bad';
            qualityText = 'No Data';
        } else if (data.packetLoss > 5) {
            quality = 'poor';
            qualityText = 'Poor';
        } else if (data.packetLoss > 1) {
            quality = 'good';
            qualityText = 'Good';
        }

        indicator.className = `quality-indicator ${quality}`;
        text.textContent = qualityText;
    }

    // Start SSE connection
    connectSSE();

    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            console.log('Page hidden, closing SSE connection');
            if (eventSource) eventSource.close();
        } else {
            console.log('Page visible, reconnecting SSE');
            connectSSE();
        }
    });

    console.log('Enhanced dashboard initialized successfully');
});