// Track Map Visualization for F1 Dual-Rig Dashboard
// Adapted from f1-25-telemetry-application Canvas.py

// Track ID to track name and scaling parameters mapping
const TRACK_DICTIONARY = {
    0: { name: "melbourne", scale: 3.5, offsetX: 300, offsetZ: 300 },
    1: { name: "paul_ricard", scale: 2.5, offsetX: 500, offsetZ: 300 },
    2: { name: "shanghai", scale: 2, offsetX: 300, offsetZ: 300 },
    3: { name: "sakhir", scale: 2, offsetX: 600, offsetZ: 350 },
    4: { name: "catalunya", scale: 2.5, offsetX: 400, offsetZ: 300 },
    5: { name: "monaco", scale: 2, offsetX: 300, offsetZ: 300 },
    6: { name: "montreal", scale: 3, offsetX: 300, offsetZ: 100 },
    7: { name: "silverstone", scale: 3.5, offsetX: 400, offsetZ: 250 },
    8: { name: "hockenheim", scale: 2, offsetX: 300, offsetZ: 300 },
    9: { name: "hungaroring", scale: 2.5, offsetX: 400, offsetZ: 300 },
    10: { name: "spa", scale: 3.5, offsetX: 500, offsetZ: 350 },
    11: { name: "monza", scale: 4, offsetX: 400, offsetZ: 300 },
    12: { name: "singapore", scale: 2, offsetX: 400, offsetZ: 300 },
    13: { name: "suzuka", scale: 2.5, offsetX: 500, offsetZ: 300 },
    14: { name: "abu_dhabi", scale: 2, offsetX: 500, offsetZ: 250 },
    15: { name: "texas", scale: 2, offsetX: 400, offsetZ: 50 },
    16: { name: "brazil", scale: 2, offsetX: 600, offsetZ: 250 },
    17: { name: "austria", scale: 2, offsetX: 300, offsetZ: 300 },
    18: { name: "sochi", scale: 2, offsetX: 300, offsetZ: 300 },
    19: { name: "mexico", scale: 2.5, offsetX: 500, offsetZ: 500 },
    20: { name: "baku", scale: 3, offsetX: 400, offsetZ: 400 },
    21: { name: "sakhir_short", scale: 2, offsetX: 300, offsetZ: 300 },
    22: { name: "silverstone_short", scale: 2, offsetX: 300, offsetZ: 300 },
    23: { name: "texas_short", scale: 2, offsetX: 300, offsetZ: 300 },
    24: { name: "suzuka_short", scale: 2, offsetX: 300, offsetZ: 300 },
    25: { name: "hanoi", scale: 2, offsetX: 300, offsetZ: 300 },
    26: { name: "zandvoort", scale: 2, offsetX: 500, offsetZ: 300 },
    27: { name: "imola", scale: 2, offsetX: 500, offsetZ: 300 },
    28: { name: "portimao", scale: 2, offsetX: 300, offsetZ: 300 },
    29: { name: "jeddah", scale: 4, offsetX: 500, offsetZ: 350 },
    30: { name: "miami", scale: 2, offsetX: 400, offsetZ: 300 },
    31: { name: "Las Vegas", scale: 4, offsetX: 400, offsetZ: 300 },
    32: { name: "losail", scale: 2.5, offsetX: 400, offsetZ: 300 },
    39: { name: "silverstone", scale: 3.5, offsetX: 400, offsetZ: 250 },
    40: { name: "austria", scale: 2, offsetX: 300, offsetZ: 300 },
    41: { name: "zandvoort", scale: 2, offsetX: 500, offsetZ: 300 }
};

// Marshal zone flag colors
const FLAG_COLORS = {
    '-1': 'rgba(255, 255, 255, 0.1)',  // None/Unknown
    '0': 'rgba(255, 255, 255, 0.1)',   // None
    '1': '#2ecc71',                     // Green
    '2': '#3498db',                     // Blue
    '3': '#f39c12',                     // Yellow
    '4': '#e74c3c'                      // Red
};

// Rig colors (matching dashboard theme)
const RIG_COLORS = {
    'RIG_A': '#e63946',  // Red
    'RIG_B': '#0077b6'   // Blue
};

class TrackMap {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`Canvas with id '${canvasId}' not found`);
            return;
        }

        this.ctx = this.canvas.getContext('2d');
        this.padding = 40;  /* More padding for 4K TV */
        this.carRadius = 10;  /* Larger car markers for 4K TV */

        // Track data
        this.trackData = null;
        this.trackId = null;
        this.trackName = null;
        this.marshalZones = [];
        this.trackLength = 0;

        // Scaling parameters
        this.coeff = 1;
        this.offsetX = 0;
        this.offsetZ = 0;

        // Car positions
        this.cars = {
            RIG_A: { x: 0, z: 0, name: 'Driver 1', visible: false },
            RIG_B: { x: 0, z: 0, name: 'Driver 2', visible: false }
        };

        // Segments for rendering marshal zones
        this.segments = [];

        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        // Set canvas size to match its display size
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;

        if (this.trackData) {
            this.calculateScaling();
            this.render();
        }
    }

    async loadTrack(trackId) {
        const track = TRACK_DICTIONARY[trackId];
        if (!track) {
            console.warn(`Track ID ${trackId} not found in dictionary`);
            return false;
        }

        this.trackId = trackId;
        this.trackName = track.name;

        try {
            const response = await fetch(`/static/tracks/${track.name}_2020_racingline.txt`);
            const text = await response.text();
            this.parseTrackData(text);
            this.calculateScaling();
            this.render();
            return true;
        } catch (error) {
            console.error(`Failed to load track ${track.name}:`, error);
            return false;
        }
    }

    parseTrackData(csvText) {
        const lines = csvText.trim().split('\n');
        this.trackData = [];

        // Skip first two header lines
        for (let i = 2; i < lines.length; i++) {
            const parts = lines[i].split(',');
            if (parts.length >= 4) {
                this.trackData.push({
                    distance: parseFloat(parts[0]),
                    z: parseFloat(parts[1]),
                    x: parseFloat(parts[2]),
                    y: parseFloat(parts[3])  // elevation, not used for 2D map
                });
            }
        }

        console.log(`Loaded ${this.trackData.length} track points for ${this.trackName}`);
    }

    calculateScaling() {
        if (!this.trackData || this.trackData.length === 0) return;

        // Find bounding box
        let minX = Infinity, maxX = -Infinity;
        let minZ = Infinity, maxZ = -Infinity;

        for (const point of this.trackData) {
            if (point.x < minX) minX = point.x;
            if (point.x > maxX) maxX = point.x;
            if (point.z < minZ) minZ = point.z;
            if (point.z > maxZ) maxZ = point.z;
        }

        // Calculate available canvas space
        const canvasWidth = this.canvas.width - 2 * this.padding;
        const canvasHeight = this.canvas.height - 2 * this.padding;

        // Calculate scaling coefficients
        const coeffX = (maxX - minX) / canvasWidth;
        const coeffZ = (maxZ - minZ) / canvasHeight;

        // Use the larger coefficient to ensure track fits in both dimensions
        this.coeff = Math.max(coeffX, coeffZ);

        // Calculate offsets to center the track
        this.offsetX = -minX / this.coeff + (canvasWidth - (maxX - minX) / this.coeff) / 2 + this.padding;
        this.offsetZ = -minZ / this.coeff + (canvasHeight - (maxZ - minZ) / this.coeff) / 2 + this.padding;
    }

    setMarshalZones(zones, trackLength) {
        this.marshalZones = zones || [];
        this.trackLength = trackLength || 0;
        this.createSegments();
    }

    createSegments() {
        if (!this.trackData || this.trackData.length === 0 || this.marshalZones.length === 0) {
            return;
        }

        this.segments = [];
        let currentSegment = [];
        let zoneIndex = 0;

        for (const point of this.trackData) {
            const distanceFraction = point.distance / this.trackLength;

            // Check if we've moved to the next marshal zone
            if (zoneIndex < this.marshalZones.length - 1 &&
                distanceFraction >= this.marshalZones[zoneIndex + 1].m_zone_start) {
                // Save current segment
                if (currentSegment.length > 0) {
                    this.segments.push({
                        points: currentSegment,
                        flag: this.marshalZones[zoneIndex].m_zone_flag
                    });
                }
                currentSegment = [];
                zoneIndex++;
            }

            currentSegment.push(point);
        }

        // Save last segment
        if (currentSegment.length > 0) {
            this.segments.push({
                points: currentSegment,
                flag: this.marshalZones[zoneIndex].m_zone_flag
            });
        }
    }

    updateCarPosition(rigId, worldX, worldZ, driverName) {
        if (this.cars[rigId]) {
            this.cars[rigId].x = worldX;
            this.cars[rigId].z = worldZ;
            this.cars[rigId].name = driverName || this.cars[rigId].name;
            this.cars[rigId].visible = true;
        }
    }

    worldToCanvas(worldX, worldZ) {
        return {
            x: worldX / this.coeff + this.offsetX,
            z: worldZ / this.coeff + this.offsetZ
        };
    }

    render() {
        if (!this.ctx) return;

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        if (!this.trackData) {
            this.drawNoTrackMessage();
            return;
        }

        // Draw marshal zone segments or plain track
        if (this.segments.length > 0) {
            this.drawSegments();
        } else {
            this.drawPlainTrack();
        }

        // Draw car positions
        this.drawCars();
    }

    drawNoTrackMessage() {
        this.ctx.fillStyle = '#a0a0a0';
        this.ctx.font = '16px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText('Waiting for session data...', this.canvas.width / 2, this.canvas.height / 2);
    }

    drawSegments() {
        for (const segment of this.segments) {
            const color = FLAG_COLORS[segment.flag] || FLAG_COLORS['0'];
            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = 5;  /* Thicker line for 4K TV */
            this.ctx.beginPath();

            let first = true;
            for (const point of segment.points) {
                const pos = this.worldToCanvas(point.x, point.z);
                if (first) {
                    this.ctx.moveTo(pos.x, pos.z);
                    first = false;
                } else {
                    this.ctx.lineTo(pos.x, pos.z);
                }
            }

            this.ctx.stroke();
        }
    }

    drawPlainTrack() {
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        this.ctx.lineWidth = 5;  /* Thicker line for 4K TV */
        this.ctx.beginPath();

        let first = true;
        for (const point of this.trackData) {
            const pos = this.worldToCanvas(point.x, point.z);
            if (first) {
                this.ctx.moveTo(pos.x, pos.z);
                first = false;
            } else {
                this.ctx.lineTo(pos.x, pos.z);
            }
        }

        this.ctx.stroke();
    }

    drawCars() {
        for (const [rigId, car] of Object.entries(this.cars)) {
            if (!car.visible) continue;

            const pos = this.worldToCanvas(car.x, car.z);
            const color = RIG_COLORS[rigId] || '#FFFFFF';

            // Draw car circle
            this.ctx.fillStyle = color;
            this.ctx.beginPath();
            this.ctx.arc(pos.x, pos.z, this.carRadius, 0, 2 * Math.PI);
            this.ctx.fill();

            // Draw border
            this.ctx.strokeStyle = '#FFFFFF';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();

            // Draw driver name
            this.ctx.fillStyle = '#FFFFFF';
            this.ctx.font = 'bold 16px Arial';  /* Larger font for 4K TV */
            this.ctx.textAlign = 'left';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(car.name, pos.x + 15, pos.z);
        }
    }
}
