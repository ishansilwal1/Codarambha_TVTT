// Lifeline Dashboard JavaScript

// API Base URL
const API_BASE = 'http://localhost:8000';

// Global state
let isOverrideEnabled = false;
let websocket = null;
let updateInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    initializeWebSocket();
    setupEventListeners();
    startPeriodicUpdates();
});

// WebSocket connection for real-time updates
function initializeWebSocket() {
    websocket = new WebSocket(`ws://localhost:8000/ws/updates`);
    
    websocket.onopen = function() {
        console.log('WebSocket connected');
        addEvent('System', 'Connected to server');
        updateSystemStatus('running', true);
    };
    
    websocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        updateDashboard(data);
    };
    
    websocket.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateSystemStatus('error', false);
        addEvent('Error', 'Connection lost');
    };
    
    websocket.onclose = function() {
        console.log('WebSocket disconnected');
        updateSystemStatus('disconnected', false);
        // Attempt to reconnect after 5 seconds
        setTimeout(initializeWebSocket, 5000);
    };
}

// Setup event listeners
function setupEventListeners() {
    // Start/Stop buttons
    document.getElementById('startBtn').addEventListener('click', startSystem);
    document.getElementById('stopBtn').addEventListener('click', stopSystem);
    document.getElementById('emergencyStopBtn').addEventListener('click', emergencyStop);
    
    // Override button
    document.getElementById('overrideBtn').addEventListener('click', toggleOverride);
    
    // Video controls
    document.getElementById('pauseBtn').addEventListener('click', pauseVideo);
    document.getElementById('recordBtn').addEventListener('click', startRecording);
}

// Periodic updates (fallback if WebSocket fails)
function startPeriodicUpdates() {
    updateInterval = setInterval(async () => {
        if (!websocket || websocket.readyState !== WebSocket.OPEN) {
            await fetchStatus();
        }
    }, 2000);
}

// Fetch system status
async function fetchStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();
        updateDashboard(data);
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

// Update dashboard with new data
function updateDashboard(data) {
    // Update signal states
    if (data.states) {
        updateSignals(data.states);
    }
    
    // Update priority mode
    if (data.priority_mode !== undefined) {
        updatePriorityIndicator(data.priority_mode, data.priority_lane);
    }
    
    // Update statistics
    if (data.statistics) {
        updateStatistics(data.statistics);
    }
    
    // Update detection count
    if (data.detections_count !== undefined) {
        document.getElementById('detectionCount').textContent = data.detections_count;
    }
}

// Update traffic signals
function updateSignals(states) {
    for (const [direction, state] of Object.entries(states)) {
        const signalElement = document.getElementById(`signal${capitalize(direction)}`);
        if (signalElement) {
            const lights = signalElement.querySelectorAll('.light');
            lights.forEach(light => light.classList.remove('active'));
            
            const activeLight = signalElement.querySelector(`.light.${state}`);
            if (activeLight) {
                activeLight.classList.add('active');
            }
        }
    }
}

// Update priority indicator
function updatePriorityIndicator(priorityMode, priorityLane) {
    const indicator = document.getElementById('priorityIndicator');
    const text = indicator.querySelector('.priority-text');
    
    if (priorityMode) {
        indicator.classList.add('active');
        text.textContent = `🚨 PRIORITY: ${priorityLane ? priorityLane.toUpperCase() : 'ACTIVE'}`;
        addEvent('Priority', `Emergency mode activated for ${priorityLane || 'unknown'} lane`);
    } else {
        indicator.classList.remove('active');
        text.textContent = 'NORMAL MODE';
    }
}

// Update statistics
function updateStatistics(stats) {
    if (stats.total_detections !== undefined) {
        document.getElementById('totalDetections').textContent = stats.total_detections;
    }
    if (stats.priority_activations !== undefined) {
        document.getElementById('priorityActivations').textContent = stats.priority_activations;
    }
    if (stats.avg_response_time !== undefined) {
        document.getElementById('avgResponseTime').textContent = Math.round(stats.avg_response_time);
    }
    if (stats.uptime !== undefined) {
        document.getElementById('uptime').textContent = formatUptime(stats.uptime);
    }
}

// Update system status indicator
function updateSystemStatus(status, isConnected) {
    const statusElement = document.getElementById('systemStatus');
    const dot = statusElement.querySelector('.status-dot');
    const text = statusElement.querySelector('.status-text');
    
    dot.style.background = isConnected ? 'var(--success-color)' : 'var(--danger-color)';
    text.textContent = capitalize(status);
}

// Add event to log
function addEvent(type, message) {
    const eventsLog = document.getElementById('eventsLog');
    const eventItem = document.createElement('div');
    eventItem.className = 'event-item';
    
    const time = new Date().toLocaleTimeString();
    eventItem.innerHTML = `
        <span class="event-time">${time}</span>
        <span class="event-message">[${type}] ${message}</span>
    `;
    
    eventsLog.insertBefore(eventItem, eventsLog.firstChild);
    
    // Keep only last 20 events
    while (eventsLog.children.length > 20) {
        eventsLog.removeChild(eventsLog.lastChild);
    }
}

// Control functions
async function startSystem() {
    try {
        const response = await fetch(`${API_BASE}/api/system/start`, { method: 'POST' });
        const data = await response.json();
        addEvent('System', 'System started');
        showNotification('System Started', 'success');
    } catch (error) {
        console.error('Error starting system:', error);
        showNotification('Failed to start system', 'error');
    }
}

async function stopSystem() {
    try {
        const response = await fetch(`${API_BASE}/api/system/stop`, { method: 'POST' });
        const data = await response.json();
        addEvent('System', 'System stopped');
        showNotification('System Stopped', 'warning');
    } catch (error) {
        console.error('Error stopping system:', error);
        showNotification('Failed to stop system', 'error');
    }
}

function emergencyStop() {
    if (confirm('Are you sure you want to perform an emergency stop? All signals will turn red.')) {
        stopSystem();
        addEvent('Emergency', 'Emergency stop activated');
        showNotification('EMERGENCY STOP', 'error');
    }
}

async function toggleOverride() {
    isOverrideEnabled = !isOverrideEnabled;
    const btn = document.getElementById('overrideBtn');
    const panel = document.getElementById('manualControlPanel');
    
    try {
        const endpoint = isOverrideEnabled ? 'enable' : 'disable';
        const response = await fetch(`${API_BASE}/api/override/${endpoint}`, { method: 'POST' });
        
        if (response.ok) {
            btn.textContent = isOverrideEnabled ? '✓ Override Active' : 'Manual Override';
            btn.style.background = isOverrideEnabled ? 'var(--warning-color)' : 'var(--primary-color)';
            panel.style.display = isOverrideEnabled ? 'block' : 'none';
            addEvent('Control', `Manual override ${isOverrideEnabled ? 'enabled' : 'disabled'}`);
        }
    } catch (error) {
        console.error('Error toggling override:', error);
        showNotification('Failed to toggle override', 'error');
    }
}

async function setSignal(direction, state) {
    try {
        const response = await fetch(`${API_BASE}/api/signals/control`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction, state })
        });
        
        if (response.ok) {
            addEvent('Manual', `${direction} set to ${state}`);
        }
    } catch (error) {
        console.error('Error setting signal:', error);
        showNotification('Failed to set signal', 'error');
    }
}

function pauseVideo() {
    const btn = document.getElementById('pauseBtn');
    // Toggle pause state
    btn.textContent = btn.textContent === 'Pause' ? 'Resume' : 'Pause';
    addEvent('Video', 'Video feed paused');
}

function startRecording() {
    const btn = document.getElementById('recordBtn');
    btn.textContent = btn.textContent === 'Record' ? 'Stop Recording' : 'Record';
    btn.style.background = btn.textContent === 'Stop Recording' ? 'var(--danger-color)' : 'var(--primary-color)';
    addEvent('Video', btn.textContent === 'Stop Recording' ? 'Recording started' : 'Recording stopped');
}

// Utility functions
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${pad(hours)}:${pad(minutes)}:${pad(secs)}`;
}

function pad(num) {
    return num.toString().padStart(2, '0');
}

function showNotification(message, type) {
    // Simple notification (you can enhance this with a toast library)
    const color = type === 'success' ? 'var(--success-color)' : 
                  type === 'warning' ? 'var(--warning-color)' : 
                  'var(--danger-color)';
    
    console.log(`[${type.toUpperCase()}] ${message}`);
    addEvent('Notification', message);
}

// Modal functions
function showModal(title, message) {
    const modal = document.getElementById('alertModal');
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalMessage').textContent = message;
    modal.style.display = 'flex';
}

function closeModal() {
    document.getElementById('alertModal').style.display = 'none';
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+E for emergency stop
    if (e.ctrlKey && e.key === 'e') {
        e.preventDefault();
        emergencyStop();
    }
    
    // Ctrl+M for manual override
    if (e.ctrlKey && e.key === 'm') {
        e.preventDefault();
        toggleOverride();
    }
});

// Update FPS counter periodically
setInterval(async () => {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();
        if (data.video_stats && data.video_stats.fps) {
            document.getElementById('fpsCounter').textContent = `FPS: ${data.video_stats.fps}`;
        }
    } catch (error) {
        // Silently fail
    }
}, 1000);
