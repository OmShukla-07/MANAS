/**
 * MANAS Counselor Admin Panel - Complete JavaScript Integration
 * Connects all frontend functionality with Django backend APIs
 */

// CSRF Token for Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Common API request function
async function makeAPIRequest(url, method = 'GET', data = null) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, config);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Request failed');
        }
        
        return result;
    } catch (error) {
        console.error('API Request failed:', error);
        throw error;
    }
}

// Notification system
function showNotification(message, type = 'info', duration = 3000) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.counselor-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = `counselor-notification counselor-notification-${type}`;
    
    const icons = {
        success: '<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>',
        error: '<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>',
        warning: '<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92z" clip-rule="evenodd"/>',
        info: '<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>'
    };
    
    notification.innerHTML = `
        <div class="counselor-notification-content">
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                ${icons[type] || icons.info}
            </svg>
            <span>${message}</span>
        </div>
    `;
    
    // Add styles if not already present
    if (!document.getElementById('counselor-notification-styles')) {
        const style = document.createElement('style');
        style.id = 'counselor-notification-styles';
        style.textContent = `
            .counselor-notification {
                position: fixed;
                top: 1rem;
                right: 1rem;
                padding: 1rem 1.5rem;
                border-radius: 0.75rem;
                color: white;
                z-index: 1001;
                animation: slideInRight 0.3s ease;
                min-width: 300px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            }
            .counselor-notification-success {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            }
            .counselor-notification-error {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            }
            .counselor-notification-warning {
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            }
            .counselor-notification-info {
                background: linear-gradient(135deg, #787bda 0%, #8ee0fe 100%);
            }
            .counselor-notification-content {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            @keyframes slideInRight {
                from {
                    opacity: 0;
                    transform: translateX(100%);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Crisis Management Functions
async function respondToCrisis(alertId) {
    try {
        const result = await makeAPIRequest('/api/counselor/crisis/action/', 'POST', {
            alert_id: alertId,
            action: 'respond',
            notes: 'Crisis response initiated by counselor'
        });
        
        showNotification(result.message, 'success');
        
        // Update the UI
        const alertCard = document.querySelector(`[data-alert-id="${alertId}"]`);
        if (alertCard) {
            alertCard.querySelector('.crisis-alert-severity').textContent = 'IN PROGRESS';
            alertCard.style.opacity = '0.7';
        }
        
        // Refresh the page after a short delay
        setTimeout(() => location.reload(), 1500);
        
    } catch (error) {
        showNotification(`Error responding to crisis: ${error.message}`, 'error');
    }
}

async function escalateCrisis(alertId) {
    const confirmed = confirm('Are you sure you want to escalate this crisis alert? This will mark it as critical priority.');
    
    if (!confirmed) return;
    
    try {
        const result = await makeAPIRequest('/api/counselor/crisis/action/', 'POST', {
            alert_id: alertId,
            action: 'escalate',
            notes: 'Crisis escalated for immediate attention'
        });
        
        showNotification(result.message, 'warning');
        
        // Update the UI
        const alertCard = document.querySelector(`[data-alert-id="${alertId}"]`);
        if (alertCard) {
            alertCard.classList.add('critical');
            alertCard.querySelector('.crisis-alert-severity').textContent = 'CRITICAL Priority';
        }
        
        setTimeout(() => location.reload(), 1500);
        
    } catch (error) {
        showNotification(`Error escalating crisis: ${error.message}`, 'error');
    }
}

async function resolveCrisis(alertId) {
    const notes = prompt('Please provide resolution notes:');
    
    if (!notes) {
        showNotification('Resolution notes are required', 'warning');
        return;
    }
    
    try {
        const result = await makeAPIRequest('/api/counselor/crisis/action/', 'POST', {
            alert_id: alertId,
            action: 'resolve',
            notes: notes
        });
        
        showNotification(result.message, 'success');
        
        // Remove the alert card or mark as resolved
        const alertCard = document.querySelector(`[data-alert-id="${alertId}"]`);
        if (alertCard) {
            alertCard.style.opacity = '0.5';
            alertCard.innerHTML += '<div class="resolved-overlay">RESOLVED</div>';
        }
        
        setTimeout(() => location.reload(), 1500);
        
    } catch (error) {
        showNotification(`Error resolving crisis: ${error.message}`, 'error');
    }
}

// Session Management Functions
async function scheduleSession(studentId, date, time, duration = 60, sessionType = 'Individual') {
    try {
        const result = await makeAPIRequest('/api/counselor/sessions/schedule/', 'POST', {
            student_id: studentId,
            date: date,
            time: time,
            duration: duration,
            session_type: sessionType,
            notes: 'Scheduled through counselor panel'
        });
        
        showNotification(result.message, 'success');
        return result;
        
    } catch (error) {
        showNotification(`Error scheduling session: ${error.message}`, 'error');
        throw error;
    }
}

async function updateSessionStatus(appointmentId, status, notes = '', rating = null) {
    try {
        const result = await makeAPIRequest(`/api/counselor/sessions/${appointmentId}/update/`, 'POST', {
            status: status,
            notes: notes,
            rating: rating
        });
        
        showNotification(result.message, 'success');
        
        // Update the session card UI
        const sessionCard = document.querySelector(`[data-appointment-id="${appointmentId}"]`);
        if (sessionCard) {
            const statusBadge = sessionCard.querySelector('.session-status');
            if (statusBadge) {
                statusBadge.textContent = status.toUpperCase();
                statusBadge.className = `session-status status-${status}`;
            }
        }
        
        return result;
        
    } catch (error) {
        showNotification(`Error updating session: ${error.message}`, 'error');
        throw error;
    }
}

// Student Management Functions
async function getStudentDetails(studentId) {
    try {
        const result = await makeAPIRequest(`/api/counselor/students/${studentId}/details/`);
        return result;
    } catch (error) {
        showNotification(`Error fetching student details: ${error.message}`, 'error');
        throw error;
    }
}

function showStudentDetails(studentId) {
    getStudentDetails(studentId).then(data => {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'student-details-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="closeStudentModal()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${data.student.name}</h3>
                    <button onclick="closeStudentModal()" class="modal-close">×</button>
                </div>
                <div class="modal-body">
                    <div class="student-info">
                        <p><strong>Email:</strong> ${data.student.email}</p>
                        <p><strong>Phone:</strong> ${data.student.phone || 'Not provided'}</p>
                        <p><strong>Risk Level:</strong> 
                            <span class="risk-badge risk-${data.stats.risk_level.toLowerCase()}">${data.stats.risk_level}</span>
                        </p>
                    </div>
                    
                    <div class="student-stats">
                        <div class="stat-item">
                            <span class="stat-value">${data.stats.total_sessions}</span>
                            <span class="stat-label">Total Sessions</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${data.stats.completed_sessions}</span>
                            <span class="stat-label">Completed</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${data.stats.progress_percentage}%</span>
                            <span class="stat-label">Progress</span>
                        </div>
                    </div>
                    
                    <div class="recent-sessions">
                        <h4>Recent Sessions</h4>
                        ${data.sessions.slice(0, 5).map(session => `
                            <div class="session-item">
                                <span class="session-date">${session.date}</span>
                                <span class="session-status status-${session.status}">${session.status}</span>
                                ${session.rating ? `<span class="session-rating">${session.rating}★</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="modal-actions">
                    <button onclick="scheduleNewSession(${studentId})" class="btn btn-primary">Schedule Session</button>
                    <button onclick="viewFullHistory(${studentId})" class="btn btn-secondary">View Full History</button>
                </div>
            </div>
        `;
        
        // Add modal styles
        if (!document.getElementById('modal-styles')) {
            const style = document.createElement('style');
            style.id = 'modal-styles';
            style.textContent = `
                .student-details-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 1000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .modal-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.75);
                }
                
                .modal-content {
                    background: white;
                    border-radius: 1rem;
                    padding: 0;
                    max-width: 600px;
                    width: 90%;
                    max-height: 80%;
                    overflow: auto;
                    position: relative;
                    z-index: 1001;
                    animation: modalSlideIn 0.3s ease;
                }
                
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1.5rem;
                    border-bottom: 1px solid #e2e8f0;
                }
                
                .modal-close {
                    background: none;
                    border: none;
                    font-size: 1.5rem;
                    cursor: pointer;
                    color: #6b7280;
                }
                
                .modal-body {
                    padding: 1.5rem;
                }
                
                .student-stats {
                    display: flex;
                    gap: 1rem;
                    margin: 1rem 0;
                }
                
                .stat-item {
                    text-align: center;
                    padding: 1rem;
                    background: #f8fafc;
                    border-radius: 0.5rem;
                    flex: 1;
                }
                
                .stat-value {
                    display: block;
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #1e40af;
                }
                
                .stat-label {
                    font-size: 0.875rem;
                    color: #6b7280;
                }
                
                .risk-badge {
                    padding: 0.25rem 0.5rem;
                    border-radius: 0.25rem;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }
                
                .risk-low { background: #d1fae5; color: #065f46; }
                .risk-medium { background: #fef3c7; color: #92400e; }
                .risk-high { background: #fee2e2; color: #991b1b; }
                
                .session-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.5rem 0;
                    border-bottom: 1px solid #e2e8f0;
                }
                
                .session-status {
                    padding: 0.25rem 0.5rem;
                    border-radius: 0.25rem;
                    font-size: 0.75rem;
                    text-transform: uppercase;
                }
                
                .status-completed { background: #d1fae5; color: #065f46; }
                .status-confirmed { background: #dbeafe; color: #1e40af; }
                .status-cancelled { background: #fee2e2; color: #991b1b; }
                
                .modal-actions {
                    padding: 1.5rem;
                    border-top: 1px solid #e2e8f0;
                    display: flex;
                    gap: 1rem;
                }
                
                .btn {
                    padding: 0.5rem 1rem;
                    border-radius: 0.5rem;
                    border: none;
                    cursor: pointer;
                    font-weight: 600;
                }
                
                .btn-primary {
                    background: #3b82f6;
                    color: white;
                }
                
                .btn-secondary {
                    background: #e2e8f0;
                    color: #374151;
                }
                
                @keyframes modalSlideIn {
                    from {
                        opacity: 0;
                        transform: scale(0.9) translateY(-50px);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1) translateY(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(modal);
    });
}

function closeStudentModal() {
    const modal = document.querySelector('.student-details-modal');
    if (modal) {
        modal.remove();
    }
}

// Profile Management Functions
async function updateCounselorProfile(profileData) {
    try {
        const result = await makeAPIRequest('/api/counselor/profile/update/', 'POST', profileData);
        showNotification(result.message, 'success');
        return result;
    } catch (error) {
        showNotification(`Error updating profile: ${error.message}`, 'error');
        throw error;
    }
}

async function changePassword(passwordData) {
    try {
        const result = await makeAPIRequest('/api/counselor/profile/password/', 'POST', passwordData);
        showNotification(result.message, 'success');
        
        // Clear password fields
        document.getElementById('current_password').value = '';
        document.getElementById('new_password').value = '';
        document.getElementById('confirm_password').value = '';
        
        return result;
    } catch (error) {
        showNotification(`Error changing password: ${error.message}`, 'error');
        throw error;
    }
}

// Analytics Functions
async function loadSessionAnalytics(days = 30) {
    try {
        const result = await makeAPIRequest(`/api/counselor/analytics/sessions/?days=${days}`);
        
        // Update charts with real data
        if (window.updateChartsWithData && typeof window.updateChartsWithData === 'function') {
            window.updateChartsWithData(result);
        }
        
        return result;
    } catch (error) {
        showNotification(`Error loading analytics: ${error.message}`, 'error');
        throw error;
    }
}

// Calendar Functions
async function loadCalendarEvents(start, end) {
    try {
        const result = await makeAPIRequest(`/api/counselor/calendar/events/?start=${start}&end=${end}`);
        return result;
    } catch (error) {
        console.error('Error loading calendar events:', error);
        return [];
    }
}

// Export Functions
async function exportData(type) {
    try {
        const url = `/api/counselor/export/${type}/`;
        const response = await fetch(url, {
            headers: {
                'X-CSRFToken': csrftoken
            }
        });
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = downloadUrl;
        a.download = `${type}_export_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
        
        showNotification(`${type.charAt(0).toUpperCase() + type.slice(1)} data exported successfully`, 'success');
        
    } catch (error) {
        showNotification(`Error exporting ${type}: ${error.message}`, 'error');
    }
}

// Search and Filter Functions
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.counselor-search-input');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = e.target.value.trim();
                
                if (query.length >= 2 || query.length === 0) {
                    // Update URL with search parameter
                    const url = new URL(window.location);
                    if (query) {
                        url.searchParams.set('search', query);
                    } else {
                        url.searchParams.delete('search');
                    }
                    
                    // Reload page with new search parameter
                    window.location.href = url.toString();
                }
            }, 500);
        });
    });
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initializeSearch();
    
    // Initialize tooltips and popovers
    initializeTooltips();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
    
    // Load analytics if on analytics page
    if (window.location.pathname.includes('/analytics/')) {
        loadSessionAnalytics();
    }
    
    console.log('MANAS Counselor Admin Panel initialized');
});

// Tooltip initialization
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const text = event.target.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'counselor-tooltip';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.counselor-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Real-time updates (WebSocket or polling)
function initializeRealTimeUpdates() {
    // Poll for crisis alerts every 30 seconds
    setInterval(async () => {
        try {
            // Check for new crisis alerts
            const response = await makeAPIRequest('/api/counselor/crisis/alerts/');
            if (response.new_alerts > 0) {
                showNotification(`${response.new_alerts} new crisis alert(s) received`, 'warning', 5000);
                
                // Update crisis alerts count in navbar
                const alertsBadge = document.querySelector('.crisis-alerts-badge');
                if (alertsBadge) {
                    alertsBadge.textContent = response.total_active;
                    alertsBadge.classList.add('pulse');
                }
            }
        } catch (error) {
            // Silently handle errors in background updates
            console.log('Background update failed:', error);
        }
    }, 30000);
}

// Emergency functions
function callEmergency(number) {
    const confirmed = confirm(`Call ${number}?\n\nThis will attempt to initiate a phone call to the emergency number.`);
    
    if (confirmed) {
        // In a real application, this would integrate with device calling capabilities
        window.open(`tel:${number}`, '_self');
        showNotification(`Calling ${number}...`, 'info');
    }
}

function showEmergencyAlert() {
    const alertModal = document.createElement('div');
    alertModal.className = 'counselor-emergency-modal';
    alertModal.innerHTML = `
        <div class="counselor-emergency-modal-content">
            <div class="counselor-emergency-modal-header">
                <h3>🚨 Emergency Alert Activated</h3>
                <button onclick="closeEmergencyAlert()" class="counselor-modal-close">×</button>
            </div>
            <div class="counselor-emergency-modal-body">
                <p><strong>IMMEDIATE ACTION REQUIRED:</strong></p>
                <ul>
                    <li>If student is in immediate danger: Call 100 (Police) or 102 (Medical)</li>
                    <li>For mental health crisis: Call KIRAN 1800-599-0019</li>
                    <li>Document all actions taken</li>
                    <li>Notify institution administration</li>
                </ul>
                <div class="counselor-emergency-quick-actions">
                    <button class="counselor-btn counselor-btn-danger" onclick="callEmergency('100')">Call 100 (Police)</button>
                    <button class="counselor-btn counselor-btn-warning" onclick="callEmergency('18005990019')">Call KIRAN</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(alertModal);
    
    // Auto-close after 30 seconds
    setTimeout(() => {
        if (document.body.contains(alertModal)) {
            alertModal.remove();
        }
    }, 30000);
}

function closeEmergencyAlert() {
    const modal = document.querySelector('.counselor-emergency-modal');
    if (modal) modal.remove();
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function formatTime(timeString) {
    const time = new Date(`2000-01-01T${timeString}`);
    return time.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit' 
    });
}

function calculateProgress(completed, total) {
    if (total === 0) return 0;
    return Math.round((completed / total) * 100);
}

// Export global functions for use in templates
window.CounselorAdmin = {
    // Crisis management
    respondToCrisis,
    escalateCrisis,
    resolveCrisis,
    
    // Session management
    scheduleSession,
    updateSessionStatus,
    
    // Student management
    getStudentDetails,
    showStudentDetails,
    closeStudentModal,
    
    // Profile management
    updateCounselorProfile,
    changePassword,
    
    // Analytics
    loadSessionAnalytics,
    
    // Export and utilities
    exportData,
    showNotification,
    
    // Emergency functions
    callEmergency,
    showEmergencyAlert,
    closeEmergencyAlert,
    
    // API helper
    makeAPIRequest
};

console.log('MANAS Counselor Admin Panel - JavaScript loaded successfully');