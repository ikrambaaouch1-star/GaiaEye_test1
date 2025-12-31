// Backend API URL
const API_URL = 'http://127.0.0.1:5000/api/analyze';

// Global state
let currentIndicator = 'NDVI';
let currentCoords = null; // Store coords to re-fetch when indicator changes

// Initialize Map
const map = L.map('map', {
    zoomControl: false // Move zoom control if needed, but default is top-left which is fine
}).setView([20, 0], 3);

// Add Satellite Basemap
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri'
}).addTo(map);

// Add Labels overlay
L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/toner-labels/{z}/{x}/{y}{r}.png', {
    attribution: 'Map tiles by Stamen Design, CC BY 3.0 -- Map data &copy; OpenStreetMap',
    subdomains: 'abcd',
    minZoom: 0,
    maxZoom: 20,
    ext: 'png'
}).addTo(map);

// Feature Group for Drawings
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

// Draw Control
const drawControl = new L.Control.Draw({
    draw: {
        polygon: false,
        polyline: false,
        circle: false,
        marker: false,
        circlemarker: false,
        rectangle: {
            shapeOptions: {
                color: '#4ade80',
                weight: 2
            }
        }
    },
    edit: {
        featureGroup: drawnItems,
        remove: true
    }
});
map.addControl(drawControl);

// Store the current GEE layer
let currentLayer = null;

// ==========================================
// DATE SLIDER LOGIC
// ==========================================

// Configuration
const START_YEAR = 2021;
const startEpoch = new Date(START_YEAR, 0, 1); // Jan 1, 2021
const today = new Date();

// Calculate total months since Start Epoch
const totalMonths = (today.getFullYear() - START_YEAR) * 12 + today.getMonth();

// Initialize Slider
const timeSlider = document.getElementById('time-slider');
if (timeSlider) {
    timeSlider.min = 0;
    timeSlider.max = totalMonths;
    timeSlider.value = totalMonths; // Default to now
}

// State for selected month
let selectedDate = new Date(today.getFullYear(), today.getMonth(), 1);

function updateDateFromSlider() {
    if (!timeSlider) return;

    const monthsSinceStart = parseInt(timeSlider.value);
    const date = new Date(startEpoch);
    date.setMonth(startEpoch.getMonth() + monthsSinceStart);
    selectedDate = date;

    // Update Text Display
    const display = document.getElementById('date-display');
    if (display) {
        display.textContent = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    }

    // Trigger Analysis (Debounced ideally, but direct for now)
    if (currentCoords) {
        fetchAnalysis();
    }
}

if (timeSlider) {
    timeSlider.addEventListener('input', updateDateFromSlider);
}

// Button Nav
const prevBtn = document.getElementById('prev-month');
if (prevBtn) {
    prevBtn.addEventListener('click', () => {
        if (timeSlider && timeSlider.value > 0) {
            timeSlider.value = parseInt(timeSlider.value) - 1;
            updateDateFromSlider();
        }
    });
}

const nextBtn = document.getElementById('next-month');
if (nextBtn) {
    nextBtn.addEventListener('click', () => {
        if (timeSlider && timeSlider.value < timeSlider.max) {
            timeSlider.value = parseInt(timeSlider.value) + 1;
            updateDateFromSlider();
        }
    });
}

// Trigger initial update to set text
updateDateFromSlider();


// ==========================================
// UI INTERACTION LOGIC
// ==========================================

// 1. Sidebar Category Selection
document.querySelectorAll('.sidebar-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.stopPropagation();

        // Update Active State
        document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');

        // Show Corresponding Sub-menu
        const cat = item.dataset.cat;
        document.querySelectorAll('.sub-menu').forEach(m => m.classList.remove('visible'));

        const targetMenu = document.getElementById(`sub-${cat}`);
        if (targetMenu) {
            targetMenu.classList.add('visible');

            // UX Improvement: Auto-select the first indicator of this category
            // This ensures clicking the icon "displays data" immediately (if area drawn)
            const firstBtn = targetMenu.querySelector('.indicator-btn');
            if (firstBtn) {
                firstBtn.click();
            }
        }
    });
});

// 2. Hide Sub-menus when clicking map or outside
document.addEventListener('click', (e) => {
    const isSidebar = e.target.closest('.sidebar');
    const isSubMenu = e.target.closest('.sub-menu');

    if (!isSidebar && !isSubMenu) {
        document.querySelectorAll('.sub-menu').forEach(m => m.classList.remove('visible'));
        document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
    }
});


// 3. Indicator Selection
document.querySelectorAll('.indicator-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent closing menu immediately on selection

        // Update UI
        document.querySelectorAll('.indicator-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update State
        currentIndicator = btn.dataset.ind;

        // Trigger Analysis
        if (currentCoords) {
            fetchAnalysis();
        } else {
            const statusMsg = document.getElementById('status-msg');
            if (statusMsg) {
                statusMsg.textContent = "⚠️ Please draw an area on the map first.";
                statusMsg.className = 'status-text error';
            }
        }
    });
});

// 4. Update Button Logic (Deprecated but keep for compatibility if element exists?)
// We removed update-btn in index.html in favor of Slider. 
// But if it were there:
const updateBtn = document.getElementById('update-btn');
if (updateBtn) {
    updateBtn.addEventListener('click', () => {
        if (currentCoords) {
            fetchAnalysis();
        } else {
            alert("Please draw a region on the map first.");
        }
    });
}


// ==========================================
// CORE ANALYSIS LOGIC
// ==========================================

// Handle Draw Created Event
map.on(L.Draw.Event.CREATED, function (e) {
    const layer = e.layer;
    drawnItems.clearLayers();
    if (currentLayer) map.removeLayer(currentLayer);
    drawnItems.addLayer(layer);

    const bounds = layer.getBounds();
    currentCoords = {
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest()
    };

    fetchAnalysis();
    fetchRawData();
    fetchTerroirAnalysis(); // Trigger the intelligence audit
});

async function fetchAnalysis() {
    if (!currentCoords) return;

    const statusMsg = document.getElementById('status-msg');

    // Calculate First and Last Day of selected month
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();

    const firstDay = new Date(year, month, 1);

    // Last day: Using new Date(year, month + 1, 0) gives the last day of 'month'
    const lastDay = new Date(year, month + 1, 0);

    const formatDate = (d) => {
        // Adjust for timezone offset to ensure we get YYYY-MM-DD correctly
        const offset = d.getTimezoneOffset();
        const adjustedDate = new Date(d.getTime() - (offset * 60 * 1000));
        return adjustedDate.toISOString().split('T')[0];
    };

    const payload = {
        ...currentCoords,
        date_start: formatDate(firstDay),
        date_end: formatDate(lastDay),
        indicator: currentIndicator
    };

    if (statusMsg) {
        statusMsg.className = 'status-text loading';
        statusMsg.textContent = `Computing ${currentIndicator} for ${firstDay.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}...`;
    }

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.error || 'Server Error');

        if (data.success && data.tile_url) {
            updateLayer(data.tile_url);
            if (statusMsg) {
                statusMsg.className = 'status-text success';
                statusMsg.textContent = `${currentIndicator} Loaded.`;
            }
        } else {
            throw new Error('Invalid response from server');
        }

    } catch (error) {
        console.error('Error:', error);
        if (statusMsg) {
            statusMsg.className = 'status-text error';
            statusMsg.textContent = `Error: ${error.message}`;
        }
    }
}

function updateLayer(tileUrlFormat) {
    if (currentLayer) {
        map.removeLayer(currentLayer);
    }

    currentLayer = L.tileLayer(tileUrlFormat, {
        attribution: `Google Earth Engine`,
        opacity: 0.8
    }).addTo(map);
}

// ==========================================
// AGRICULTURAL DASHBOARD LOGIC
// ==========================================

const dashboardOverlay = document.getElementById('agri-dashboard');
const dashboardToggle = document.getElementById('dashboard-toggle');
const closeDashboard = document.getElementById('close-dashboard');
const calculateDashboard = document.getElementById('calculate-dashboard');

// Toggle Dashboard
if (dashboardToggle) {
    dashboardToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!currentCoords) {
            alert("Please draw an area on the map first to view agricultural metrics.");
            return;
        }
        dashboardOverlay.classList.remove('hidden');
    });
}

// Close Dashboard
if (closeDashboard) {
    closeDashboard.addEventListener('click', () => {
        dashboardOverlay.classList.add('hidden');
    });
}

// Calculate Dashboard Metrics
if (calculateDashboard) {
    calculateDashboard.addEventListener('click', async () => {
        if (!currentCoords) {
            alert("Please draw an area on the map first.");
            return;
        }

        const cropType = document.getElementById('crop-type').value;
        const inputCosts = parseFloat(document.getElementById('input-costs').value);

        // Calculate dates (last 90 days for better analysis)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - 90);

        const formatDate = (d) => {
            const offset = d.getTimezoneOffset();
            const adjustedDate = new Date(d.getTime() - (offset * 60 * 1000));
            return adjustedDate.toISOString().split('T')[0];
        };

        const payload = {
            ...currentCoords,
            date_start: formatDate(startDate),
            date_end: formatDate(endDate),
            crop_type: cropType,
            input_costs: inputCosts
        };

        // Show loading state
        calculateDashboard.textContent = 'Calculating...';
        calculateDashboard.disabled = true;

        try {
            const response = await fetch('/api/dashboard_stats', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Server Error');

            if (data.success && data.stats) {
                updateDashboardUI(data.stats);
            } else {
                throw new Error('Invalid response from server');
            }

        } catch (error) {
            console.error('Dashboard Error:', error);
            alert(`Error calculating metrics: ${error.message}`);
        } finally {
            calculateDashboard.textContent = 'Calculate Metrics';
            calculateDashboard.disabled = false;
        }
    });
}

function updateDashboardUI(stats) {
    // Productivity
    const prod = stats.productivity_index;
    document.getElementById('productivity-ndvi').textContent = prod.mean_ndvi;
    document.getElementById('productivity-status').textContent = prod.health_status.toUpperCase();
    document.getElementById('productivity-yield').textContent = `Expected: ${prod.expected_yield_tons_ha} tons/ha`;

    // Apply health color
    const prodValue = document.getElementById('productivity-ndvi');
    prodValue.className = 'metric-value health-' + prod.health_status;

    // Financial
    const fin = stats.financial;
    document.getElementById('financial-profit').textContent = `$${fin.net_profit_usd.toLocaleString()}`;
    document.getElementById('financial-roi').textContent = `ROI: ${fin.roi_percent}%`;
    document.getElementById('financial-revenue').textContent = `Revenue: $${fin.expected_revenue_usd.toLocaleString()}`;

    // Weather Risk
    const weather = stats.weather_risk;
    document.getElementById('weather-risk').textContent = weather.overall_risk.toUpperCase();
    document.getElementById('weather-temp').textContent = `Temp: ${weather.avg_temperature_c}°C`;
    document.getElementById('weather-rain').textContent = `Rain: ${weather.total_rainfall_mm} mm`;

    const weatherValue = document.getElementById('weather-risk');
    weatherValue.className = 'metric-value risk-' + weather.overall_risk;

    // Pest Risk
    const pest = stats.pest_risk;
    document.getElementById('pest-risk').textContent = pest.risk_level.toUpperCase();
    document.getElementById('pest-recommendation').textContent = pest.recommendation;

    const pestValue = document.getElementById('pest-risk');
    pestValue.className = 'metric-value risk-' + pest.risk_level;

    // Soil Health
    const soil = stats.soil_health;
    document.getElementById('soil-health').textContent = soil.health_status.toUpperCase();
    document.getElementById('soil-nitrogen').textContent = `N: ${soil.nitrogen_status}`;
    document.getElementById('soil-moisture').textContent = `Moisture: ${soil.moisture_index}`;

    const soilValue = document.getElementById('soil-health');
    soilValue.className = 'metric-value health-' + soil.health_status;

    // Irrigation
    const irrig = stats.irrigation;
    document.getElementById('irrigation-urgency').textContent = irrig.urgency.toUpperCase();
    document.getElementById('irrigation-frequency').textContent = irrig.recommended_frequency;
    document.getElementById('irrigation-amount').textContent = `${irrig.amount_per_session_mm} mm/session`;

    const irrigValue = document.getElementById('irrigation-urgency');
    irrigValue.className = 'metric-value risk-' + irrig.urgency;

    // Fertilization
    const fert = stats.fertilization;
    document.getElementById('fert-n').textContent = `${fert.nitrogen_kg_ha} kg/ha`;
    document.getElementById('fert-p').textContent = `${fert.phosphorus_kg_ha} kg/ha`;
    document.getElementById('fert-k').textContent = `${fert.potassium_kg_ha} kg/ha`;
    document.getElementById('fert-priority').textContent = fert.priority.toUpperCase();

    // Plot Info
    document.getElementById('plot-area').textContent = stats.area_hectares;
    document.getElementById('plot-crop').textContent = stats.crop_type.charAt(0).toUpperCase() + stats.crop_type.slice(1);
}

// ==========================================
// AI ANALYTICS DASHBOARD LOGIC
// ==========================================

const aiDashboard = document.getElementById('ai-analytics-dashboard');
const aiToggle = document.getElementById('ai-analytics-toggle');
const closeAIDashboard = document.getElementById('close-ai-dashboard');
const runAIAnalysis = document.getElementById('run-ai-analysis');

// Toggle AI Dashboard
if (aiToggle) {
    aiToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!currentCoords) {
            alert("Please draw an area on the map first to run AI analytics.");
            return;
        }
        aiDashboard.classList.remove('hidden');
    });
}

// Close AI Dashboard
if (closeAIDashboard) {
    closeAIDashboard.addEventListener('click', () => {
        aiDashboard.classList.add('hidden');
    });
}

// Run AI Analysis
if (runAIAnalysis) {
    runAIAnalysis.addEventListener('click', async () => {
        if (!currentCoords) {
            alert("Please draw an area on the map first.");
            return;
        }

        // Calculate dates (last 90 days for comprehensive analysis)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - 90);

        const formatDate = (d) => {
            const offset = d.getTimezoneOffset();
            const adjustedDate = new Date(d.getTime() - (offset * 60 * 1000));
            return adjustedDate.toISOString().split('T')[0];
        };

        const payload = {
            ...currentCoords,
            date_start: formatDate(startDate),
            date_end: formatDate(endDate)
        };

        // Show loading state
        runAIAnalysis.textContent = '🔄 Analyzing...';
        runAIAnalysis.disabled = true;
        document.getElementById('ai-insight-text').textContent = 'Fetching satellite data and running AI analysis...';

        try {
            const response = await fetch('/api/advanced_analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (!response.ok) throw new Error(result.error || 'Server Error');

            if (result.success && result.data) {
                updateAIDashboard(result.data);
            } else {
                throw new Error('Invalid response from server');
            }

        } catch (error) {
            console.error('AI Analysis Error:', error);
            document.getElementById('ai-insight-text').textContent = `Error: ${error.message}. Make sure the backend server is running.`;
            alert(`Error running AI analysis: ${error.message}`);
        } finally {
            runAIAnalysis.innerHTML = '<span class="btn-icon">🚀</span> Run AI Analysis';
            runAIAnalysis.disabled = false;
        }
    });
}

function updateAIDashboard(data) {
    // 1. Update Global Score
    const globalScore = data.global_score;
    document.getElementById('global-score-number').textContent = Math.round(globalScore);

    const interpretation = getScoreInterpretation(globalScore);
    document.getElementById('global-score-interpretation').textContent = interpretation;

    // 2. Update Composite Scores with animated bars
    const scores = data.scores;

    updateScoreBar('veg-health', scores.vegetation_health);
    updateScoreBar('water-stress', scores.water_stress);
    updateScoreBar('productivity', scores.productivity);
    updateScoreBar('env-risk', scores.environmental_risk);

    // 3. Update AI Insights
    document.getElementById('ai-insight-text').textContent = data.ai_insight;

    // 4. Update Zones (if available)
    const zones = data.zones_analysis;
    if (zones && zones.length > 0) {
        document.getElementById('zones-section').style.display = 'block';
        renderZones(zones);
    } else {
        document.getElementById('zones-section').style.display = 'none';
    }

    // 5. Update Alerts
    const alerts = data.alerts;
    if (alerts && alerts.length > 0) {
        document.getElementById('alerts-section').style.display = 'block';
        renderAlerts(alerts);
    } else {
        document.getElementById('alerts-section').style.display = 'none';
    }

    // 6. Update Recommendations
    const recommendations = data.recommendations;
    if (recommendations && recommendations.length > 0) {
        renderRecommendations(recommendations);
    }

    // 7. Update Detailed Scientific Report
    const reportFull = data.detailed_report;
    const reportEl = document.getElementById('ai-detailed-report');
    if (reportEl && reportFull) {
        // Simple formatting: replace double newlines with sections or just preserve white-space
        // The CSS has white-space: pre-wrap, so we can just set textContent
        // But for "Scientific" feel, we might want to highlight headers
        reportEl.textContent = reportFull;
    }
}

function updateScoreBar(prefix, value) {
    const bar = document.getElementById(`${prefix}-bar`);
    const valueEl = document.getElementById(`${prefix}-value`);

    if (bar && valueEl) {
        // Animate bar width
        setTimeout(() => {
            bar.style.width = `${value}%`;
        }, 100);

        valueEl.textContent = Math.round(value);
    }
}

function renderZones(zones) {
    const zonesGrid = document.getElementById('zones-grid');
    zonesGrid.innerHTML = '';

    zones.forEach(zone => {
        const zoneCard = document.createElement('div');
        zoneCard.className = 'zone-card';
        zoneCard.innerHTML = `
            <h4>Zone ${zone.zone_id}</h4>
            <p><strong>Health:</strong> ${zone.health_status}</p>
            <p><strong>Risk:</strong> ${zone.risk_level}</p>
            <p><strong>NDVI:</strong> ${zone.avg_ndvi.toFixed(3)}</p>
            <p><strong>Area:</strong> ${zone.area_percent}%</p>
        `;
        zonesGrid.appendChild(zoneCard);
    });
}

function renderAlerts(alerts) {
    const alertsContainer = document.getElementById('alerts-container');
    alertsContainer.innerHTML = '';

    alerts.forEach(alert => {
        const alertItem = document.createElement('div');
        alertItem.className = `alert-item ${alert.severity}`;
        alertItem.innerHTML = `
            <strong>${alert.type.replace('_', ' ').toUpperCase()}</strong>: ${alert.message}
        `;
        alertsContainer.appendChild(alertItem);
    });
}

function renderRecommendations(recommendations) {
    const recList = document.getElementById('ai-recommendations-list');
    recList.innerHTML = '';

    recommendations.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        recList.appendChild(li);
    });
}

function getScoreInterpretation(score) {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Moderate';
    if (score >= 20) return 'Poor';
    return 'Critical';
}

// ==========================================
// RAW DATA DASHBOARD LOGIC
// ==========================================

const rawDashboard = document.getElementById('raw-data-dashboard');
const rawToggle = document.getElementById('raw-data-toggle');
const closeRawDashboard = document.getElementById('close-raw-dashboard');
let lastRawData = null;

// Toggle Raw Dashboard
if (rawToggle) {
    rawToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!currentCoords) {
            alert("Veuillez sélectionner une zone sur la carte pour voir les données brutes.");
            return;
        }
        rawDashboard.classList.remove('hidden');
    });
}

// Close Raw Dashboard
if (closeRawDashboard) {
    closeRawDashboard.addEventListener('click', () => {
        rawDashboard.classList.add('hidden');
    });
}

// Tab Switching Logic
document.querySelectorAll('.raw-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.raw-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.raw-tab-content').forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        const tabId = `raw-${btn.dataset.tab}`;
        document.getElementById(tabId).classList.add('active');
    });
});

async function fetchRawData() {
    if (!currentCoords) return;

    try {
        const response = await fetch('/api/raw_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentCoords)
        });

        const data = await response.json();
        if (data.success) {
            lastRawData = data;
            updateRawDataUI(data);
        }
    } catch (error) {
        console.error('Raw Data Error:', error);
        const optTable = document.getElementById('table-s2-bands');
        if (optTable) optTable.innerHTML = `<div class="error-msg">⚠️ Erreur de chargement : ${error.message}</div>`;
    }
}

function updateRawDataUI(data) {
    // A. Optical
    renderTable('table-s2-bands', [
        { key: 'Band B1 (Aerosols)', val: data.a_optical.bands.B1 },
        { key: 'Band B2 (Blue)', val: data.a_optical.bands.B2 },
        { key: 'Band B3 (Green)', val: data.a_optical.bands.B3 },
        { key: 'Band B4 (Red)', val: data.a_optical.bands.B4 },
        { key: 'Band B8 (NIR)', val: data.a_optical.bands.B8 },
        { key: 'Band B11 (SWIR1)', val: data.a_optical.bands.B11 },
        { key: 'Band B12 (SWIR2)', val: data.a_optical.bands.B12 },
    ]);

    renderTable('table-s2-indices', [
        { key: 'NDVI (Visual Health)', val: data.a_optical.indices.NDVI },
        { key: 'NDWI (Water Content)', val: data.a_optical.indices.NDWI },
        { key: 'NDMI (Moisture)', val: data.a_optical.indices.NDMI }
    ]);

    // B. Radar & 3D
    renderTable('table-s1', [
        { key: 'Backscatter VV (dB)', val: data.b_radar_3d.vv },
        { key: 'Backscatter VH (dB)', val: data.b_radar_3d.vh },
        { key: 'Rugosity Index', val: data.b_radar_3d.rugosity }
    ]);

    renderTable('table-gedi', [
        { key: 'Canopy Height (m)', val: data.b_radar_3d.canopy_height || 'N/A' },
        { key: 'Biomass Index (PAI)', val: data.b_radar_3d.biomass_index || 'N/A' },
        { key: 'Vertical Profile FHD', val: data.b_radar_3d.vertical_profile || 'N/A' }
    ]);

    // C. Hyperspectral
    renderTable('table-prisma', [
        { key: 'Bands Count', val: data.c_hyperspectral.bands_count },
        { key: 'Mineral Signs', val: data.c_hyperspectral.mineral_signatures.join(', ') },
        { key: 'Status', val: data.c_hyperspectral.status }
    ]);

    // D. Climate
    renderTable('table-climate', [
        { key: 'LST Day Mean (°C)', val: data.d_climate.lst_celsius },
        { key: 'Precip GPM (mm)', val: data.d_climate.precip_gpm_mm },
        { key: 'Precip CHIRPS (mm)', val: data.d_climate.precip_chirps_mm }
    ]);

    // E. Topography
    renderTable('table-topo', [
        { key: 'Elevation (m)', val: data.e_topography.elevation },
        { key: 'Slope (deg)', val: data.e_topography.slope },
        { key: 'Aspect (deg)', val: data.e_topography.aspect },
        { key: 'Water Accumulation', val: data.e_topography.water_accumulation }
    ]);

    // F. Soil & Bio
    const soil = data.f_soil_biology || {};
    renderTable('table-soil', [
        { key: 'Texture', val: (soil.physical?.texture || []).join(', ') },
        { key: 'Organic Matter', val: soil.chemical?.organic_matter },
        { key: 'CEC', val: soil.chemical?.cec },
        { key: 'Active Limestone', val: soil.chemical?.active_limestone },
        { key: 'Microbiome Index', val: soil.soil_microbiome?.diversity_index }
    ]);

    // G. Plant
    const plant = data.g_plant_phenology || {};
    renderTable('table-plant', [
        { key: 'Phenology Stages', val: (plant.phenology || []).join(', ') },
        { key: 'Chlorophyll Content', val: plant.status?.chlorophyll_content },
        { key: 'Leaf Water Potential', val: plant.status?.leaf_water_potential }
    ]);
}

function renderTable(containerId, rows) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let html = '<table class="raw-data-table"><thead><tr><th>Paramètre</th><th>Valeur</th></tr></thead><tbody>';
    rows.forEach(row => {
        const val = typeof row.val === 'number' ? row.val.toFixed(4) : row.val;
        html += `<tr><td>${row.key}</td><td class="val-num">${val}</td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

// Export Logic
if (document.getElementById('export-json')) {
    document.getElementById('export-json').addEventListener('click', () => {
        if (!lastRawData) return;
        const blob = new Blob([JSON.stringify(lastRawData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'gaiaeye_raw_data.json';
        a.click();
    });
}

// Terroir Intelligence Logic
async function fetchTerroirAnalysis() {
    if (!currentCoords) return;

    const reportEl = document.getElementById('terroir-audit-report');
    const matchEl = document.getElementById('terroir-match-result');
    const gapsEl = document.getElementById('terroir-gaps-list');
    const btnTab = document.getElementById('btn-tab-audit');

    if (reportEl) reportEl.textContent = "🧠 Analyse neuronale en cours via Ollama/Qwen...";
    if (btnTab) btnTab.textContent = "H. Audit Terroir ⏳";

    try {
        const response = await fetch('/api/terroir_analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentCoords)
        });

        const data = await response.json();
        if (data.success) {
            if (btnTab) btnTab.textContent = "H. Audit Terroir ✨";

            // 1. Update Match Card
            const best = data.matches ? data.matches[0] : null;
            if (best) {
                matchEl.innerHTML = `
                    <div class="match-score">Similarity: <strong>${best.similarity_score}%</strong></div>
                    <div class="match-name">Reference: <strong>${best.name}</strong></div>
                    <div class="match-bar-bg"><div class="match-bar-fill" style="width: ${best.similarity_score}%"></div></div>
                `;
            } else {
                matchEl.innerHTML = "Aucun match trouvé.";
            }

            // 2. Update Audit Report
            reportEl.innerHTML = data.audit_report.replace(/\n/g, '<br>');

            // 3. Update Gaps
            if (data.gaps && data.gaps.length > 0) {
                gapsEl.innerHTML = data.gaps.map(g => `
                    <div class="gap-item">
                        <span class="gap-param">⚠️ ${g.parameter}</span>: ${g.impact} 
                        <div class="gap-rec">Fix: ${g.recommendation}</div>
                    </div>
                `).join('');
            } else {
                gapsEl.innerHTML = "L'empreinte du terroir est en parfaite adéquation avec la référence.";
            }
        }
    } catch (error) {
        console.error('Terroir Analysis Error:', error);
        if (reportEl) reportEl.textContent = "Erreur lors de l'audit IA. Vérifiez que le backend et Ollama sont actifs.";
        if (btnTab) btnTab.textContent = "H. Audit Terroir ❌";
    }
}
