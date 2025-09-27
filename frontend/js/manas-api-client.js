/*
Enhanced MANAS Frontend - Comprehensive JavaScript API Client
Integrates with the complete backend API system for seamless user experience
*/

class ManasAPIClient {
    constructor() {
        this.baseURL = '/api';
        this.token = this.getAuthToken();
        this.user = null;
        this.notifications = [];
        this.websocket = null;
        this.eventListeners = new Map();
        
        // Initialize on construction
        this.init();
    }

    // ===== INITIALIZATION ===== //
    async init() {
        await this.loadUserData();
        this.setupWebSocket();
        this.setupNotificationPolling();
    }

    // ===== AUTHENTICATION ===== //
    getAuthToken() {
        return localStorage.getItem('manas_auth_token') || 
               document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    setAuthToken(token) {
        localStorage.setItem('manas_auth_token', token);
        this.token = token;
    }

    async loadUserData() {
        try {
            const response = await this.request('/accounts/profile/');
            this.user = response;
            this.emit('userLoaded', this.user);
        } catch (error) {
            console.warn('Could not load user data:', error);
        }
    }

    // ===== HTTP CLIENT ===== //
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.token,
                ...(options.headers || {})
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    // ===== ASSESSMENTS API ===== //
    async getAssessmentCategories() {
        return this.request('/assessments/categories/');
    }

    async getUserAssessments(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/assessments/user-assessments/${params ? '?' + params : ''}`);
    }

    async getAssessmentById(id) {
        return this.request(`/assessments/user-assessments/${id}/`);
    }

    async takeAssessment(assessmentId) {
        return this.request(`/assessments/user-assessments/${assessmentId}/take/`, {
            method: 'POST'
        });
    }

    async submitAssessmentAnswers(assessmentId, answers) {
        return this.request(`/assessments/user-assessments/${assessmentId}/submit/`, {
            method: 'POST',
            body: { answers }
        });
    }

    async getAssessmentDashboard() {
        return this.request('/assessments/dashboard/');
    }

    async getAssessmentStats() {
        return this.request('/assessments/stats/');
    }

    // ===== WELLNESS API ===== //
    async getMoodEntries(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/wellness/mood-entries/${params ? '?' + params : ''}`);
    }

    async createMoodEntry(moodData) {
        return this.request('/wellness/mood-entries/', {
            method: 'POST',
            body: moodData
        });
    }

    async getWellnessGoals() {
        return this.request('/wellness/goals/');
    }

    async createWellnessGoal(goalData) {
        return this.request('/wellness/goals/', {
            method: 'POST',
            body: goalData
        });
    }

    async updateWellnessGoal(goalId, goalData) {
        return this.request(`/wellness/goals/${goalId}/`, {
            method: 'PATCH',
            body: goalData
        });
    }

    async getWellnessActivities() {
        return this.request('/wellness/activities/');
    }

    async completeActivity(activityId, completionData) {
        return this.request(`/wellness/activities/${activityId}/complete/`, {
            method: 'POST',
            body: completionData
        });
    }

    async getWellnessChallenges() {
        return this.request('/wellness/challenges/');
    }

    async joinChallenge(challengeId) {
        return this.request(`/wellness/challenges/${challengeId}/join/`, {
            method: 'POST'
        });
    }

    async getWellnessDashboard() {
        return this.request('/wellness/dashboard/');
    }

    async getWellnessInsights() {
        return this.request('/wellness/insights/');
    }

    // ===== CRISIS API ===== //
    async getCrisisTypes() {
        return this.request('/crisis/types/');
    }

    async getCrisisAlerts(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/crisis/alerts/${params ? '?' + params : ''}`);
    }

    async createCrisisAlert(alertData) {
        return this.request('/crisis/alerts/create/', {
            method: 'POST',
            body: alertData
        });
    }

    async getSafetyPlans() {
        return this.request('/crisis/safety-plans/');
    }

    async createSafetyPlan(planData) {
        return this.request('/crisis/safety-plans/', {
            method: 'POST',
            body: planData
        });
    }

    async activateSafetyPlan(planId) {
        return this.request(`/crisis/safety-plans/${planId}/activate/`, {
            method: 'POST'
        });
    }

    async getCrisisResources(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/crisis/resources/${params ? '?' + params : ''}`);
    }

    async getEmergencyResources() {
        return this.request('/crisis/resources/emergency/');
    }

    async getCrisisDashboard() {
        return this.request('/crisis/dashboard/');
    }

    // ===== COMMUNITY API ===== //
    async getCommunities(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/community/communities/${params ? '?' + params : ''}`);
    }

    async getCommunityById(id) {
        return this.request(`/community/communities/${id}/`);
    }

    async joinCommunity(communityId) {
        return this.request(`/community/communities/${communityId}/join/`, {
            method: 'POST'
        });
    }

    async leaveCommunity(communityId) {
        return this.request(`/community/communities/${communityId}/leave/`, {
            method: 'POST'
        });
    }

    async getPosts(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/community/posts/${params ? '?' + params : ''}`);
    }

    async createPost(postData) {
        return this.request('/community/posts/', {
            method: 'POST',
            body: postData
        });
    }

    async likePost(postId) {
        return this.request(`/community/posts/${postId}/like/`, {
            method: 'POST'
        });
    }

    async savePost(postId) {
        return this.request(`/community/posts/${postId}/save/`, {
            method: 'POST'
        });
    }

    async getComments(postId) {
        return this.request(`/community/comments/?post=${postId}`);
    }

    async createComment(commentData) {
        return this.request('/community/comments/', {
            method: 'POST',
            body: commentData
        });
    }

    async getSupportGroups(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/community/support-groups/${params ? '?' + params : ''}`);
    }

    async joinSupportGroup(groupId) {
        return this.request(`/community/support-groups/${groupId}/join/`, {
            method: 'POST'
        });
    }

    async getCommunityDashboard() {
        return this.request('/community/dashboard/');
    }

    // ===== CORE/SYSTEM API ===== //
    async getNotifications(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/core/notifications/${params ? '?' + params : ''}`);
    }

    async markNotificationsRead(notificationIds = []) {
        return this.request('/core/notifications/mark-read/', {
            method: 'POST',
            body: { notification_ids: notificationIds }
        });
    }

    async getFAQs(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/core/faqs/${params ? '?' + params : ''}`);
    }

    async rateFAQ(faqId, isHelpful) {
        return this.request(`/core/faqs/${faqId}/rate/`, {
            method: 'POST',
            body: { is_helpful: isHelpful }
        });
    }

    async sendContactMessage(messageData) {
        return this.request('/core/contact/', {
            method: 'POST',
            body: messageData
        });
    }

    async getSystemAlerts() {
        return this.request('/core/alerts/');
    }

    async getUserPreferences() {
        return this.request('/core/preferences/');
    }

    async updateUserPreferences(preferences) {
        return this.request('/core/preferences/', {
            method: 'PATCH',
            body: preferences
        });
    }

    async getDashboard() {
        return this.request('/core/dashboard/');
    }

    async getNotificationStats() {
        return this.request('/core/notifications/stats/');
    }

    // ===== APPOINTMENTS API (existing) ===== //
    async getAppointments(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/appointments/${params ? '?' + params : ''}`);
    }

    async createAppointment(appointmentData) {
        return this.request('/appointments/', {
            method: 'POST',
            body: appointmentData
        });
    }

    async updateAppointment(appointmentId, appointmentData) {
        return this.request(`/appointments/${appointmentId}/`, {
            method: 'PATCH',
            body: appointmentData
        });
    }

    async cancelAppointment(appointmentId) {
        return this.request(`/appointments/${appointmentId}/cancel/`, {
            method: 'POST'
        });
    }

    // ===== CHAT API (existing) ===== //
    async getChatHistory(sessionId) {
        return this.request(`/chat/sessions/${sessionId}/messages/`);
    }

    async sendChatMessage(sessionId, message) {
        return this.request(`/chat/sessions/${sessionId}/messages/`, {
            method: 'POST',
            body: { content: message }
        });
    }

    // ===== REAL-TIME FEATURES ===== //
    setupWebSocket() {
        if (this.websocket) {
            this.websocket.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/updates/`;

        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.emit('websocketConnected');
        };

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.emit('websocketDisconnected');
            
            // Reconnect after 5 seconds
            setTimeout(() => this.setupWebSocket(), 5000);
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'notification':
                this.notifications.unshift(data.notification);
                this.emit('newNotification', data.notification);
                break;
            case 'crisis_alert':
                this.emit('crisisAlert', data.alert);
                break;
            case 'appointment_update':
                this.emit('appointmentUpdate', data.appointment);
                break;
            case 'community_update':
                this.emit('communityUpdate', data.update);
                break;
            default:
                this.emit('websocketMessage', data);
        }
    }

    setupNotificationPolling() {
        // Poll for notifications every 30 seconds as backup
        setInterval(async () => {
            try {
                const notifications = await this.getNotifications({ is_read: false });
                const newNotifications = notifications.results || notifications;
                
                if (newNotifications.length > this.notifications.length) {
                    const latest = newNotifications.slice(0, newNotifications.length - this.notifications.length);
                    latest.forEach(notification => {
                        this.emit('newNotification', notification);
                    });
                }
                
                this.notifications = newNotifications;
            } catch (error) {
                console.warn('Notification polling failed:', error);
            }
        }, 30000);
    }

    // ===== EVENT SYSTEM ===== //
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    // ===== UTILITY METHODS ===== //
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    formatDateTime(dateString) {
        return new Date(dateString).toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    timeAgo(dateString) {
        const now = new Date();
        const date = new Date(dateString);
        const diffInMinutes = Math.floor((now - date) / (1000 * 60));

        if (diffInMinutes < 1) return 'Just now';
        if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
        
        const diffInHours = Math.floor(diffInMinutes / 60);
        if (diffInHours < 24) return `${diffInHours} hours ago`;
        
        const diffInDays = Math.floor(diffInHours / 24);
        if (diffInDays < 7) return `${diffInDays} days ago`;
        
        return this.formatDate(dateString);
    }

    // ===== ERROR HANDLING ===== //
    showError(message, duration = 5000) {
        this.emit('error', { message, duration });
    }

    showSuccess(message, duration = 3000) {
        this.emit('success', { message, duration });
    }

    showInfo(message, duration = 4000) {
        this.emit('info', { message, duration });
    }
}

// ===== NOTIFICATION MANAGER ===== //
class NotificationManager {
    constructor(apiClient) {
        this.api = apiClient;
        this.container = null;
        this.setupUI();
        this.setupEventListeners();
    }

    setupUI() {
        // Create notification container
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        this.container.innerHTML = `
            <style>
                .notification-container {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                    max-width: 400px;
                }
                .notification {
                    background: white;
                    border-radius: 8px;
                    padding: 16px;
                    margin-bottom: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    border-left: 4px solid #6366f1;
                    animation: slideIn 0.3s ease-out;
                }
                .notification.success { border-left-color: #10b981; }
                .notification.error { border-left-color: #ef4444; }
                .notification.warning { border-left-color: #f59e0b; }
                .notification.info { border-left-color: #3b82f6; }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            </style>
        `;
        document.body.appendChild(this.container);
    }

    setupEventListeners() {
        this.api.on('newNotification', (notification) => {
            this.showNotification(notification.title, notification.message, 'info');
        });

        this.api.on('error', ({ message, duration }) => {
            this.showNotification('Error', message, 'error', duration);
        });

        this.api.on('success', ({ message, duration }) => {
            this.showNotification('Success', message, 'success', duration);
        });

        this.api.on('info', ({ message, duration }) => {
            this.showNotification('Info', message, 'info', duration);
        });

        this.api.on('crisisAlert', (alert) => {
            this.showNotification(
                'Crisis Alert', 
                'Emergency support resources have been activated. Help is available.',
                'warning',
                10000
            );
        });
    }

    showNotification(title, message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h4 style="margin: 0 0 8px 0; font-weight: 600;">${title}</h4>
                    <p style="margin: 0; color: #6b7280; font-size: 14px;">${message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; font-size: 18px; cursor: pointer; color: #9ca3af;">
                    ×
                </button>
            </div>
        `;

        this.container.appendChild(notification);

        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }
}

// ===== GLOBAL INITIALIZATION ===== //
let manasAPI = null;
let notificationManager = null;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize API client
    manasAPI = new ManasAPIClient();
    
    // Initialize notification manager
    notificationManager = new NotificationManager(manasAPI);
    
    // Make API client globally available
    window.manasAPI = manasAPI;
    window.notificationManager = notificationManager;
    
    console.log('MANAS API Client initialized');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ManasAPIClient, NotificationManager };
}