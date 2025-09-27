/* MANAS Frontend-Backend Integration */
// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8001/api';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// Initialize user data
function loadCurrentUser() {
    const userData = localStorage.getItem('user');
    if (userData) {
        currentUser = JSON.parse(userData);
    }
    return currentUser;
}

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    const config = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            ...(authToken && { 'Authorization': `Token ${authToken}` }),
            ...options.headers
        },
        ...options
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        if (response.status === 401) {
            // Only logout for non-login endpoints (token expired or invalid)
            if (!endpoint.includes('/auth/login/')) {
                logout();
                return;
            }
        }
        
        const data = await response.json();
        
        // For 400 responses, return the data so the calling function can handle validation errors
        if (response.status === 400) {
            return data;
        }
        
        // For 401 on login endpoint, return the data to handle the error properly
        if (response.status === 401 && endpoint.includes('/auth/login/')) {
            return data;
        }
        
        if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        // Don't show notification for validation errors - let the calling function handle it
        if (!error.message.includes('validation') && !error.message.includes('already exists')) {
            showNotification('Error: ' + error.message, 'error');
        }
        throw error;
    }
}

// CSRF Token Helper
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return null;
}

// Authentication Functions
async function login(email, password) {
    try {
        const response = await apiRequest('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ 
                email: email,
                password: password 
            })
        });
        
        if (response && response.success && response.user) {
            // Store authentication data
            authToken = response.token || 'authenticated';
            currentUser = response.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('user', JSON.stringify(currentUser));
            
            showNotification('Login successful!', 'success');
            return response;
        } else {
            // Handle login failure
            const errorMessage = response?.error || response?.message || 'Invalid credentials';
            throw new Error(errorMessage);
        }
    } catch (error) {
        console.error('Login error:', error);
        // Don't show notification here - let the calling function handle it
        throw error;
    }
}

async function register(userData) {
    try {
        const response = await apiRequest('/auth/register/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        
        if (response.success) {
            showNotification('Registration successful! Please login.', 'success');
            return response;
        } else {
            // Handle validation errors properly
            if (response.errors) {
                const errorMessages = [];
                for (const field in response.errors) {
                    const fieldErrors = response.errors[field];
                    fieldErrors.forEach(error => {
                        errorMessages.push(`${field}: ${error}`);
                    });
                }
                throw new Error(errorMessages.join(', '));
            } else {
                throw new Error(response.message || 'Registration failed');
            }
        }
    } catch (error) {
        console.error('Registration API error:', error);
        throw error;
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    localStorage.removeItem('assessmentProgress');
    
    // Redirect to login page - determine path based on current location
    const pathSegments = window.location.pathname.split('/');
    let loginPath = '../auth/login.html';
    
    // If already in auth folder
    if (pathSegments.includes('auth')) {
        loginPath = 'login.html';
    }
    // If in root or main level  
    else if (pathSegments.length <= 3) {
        loginPath = 'pages/auth/login.html';
    }
    
    window.location.href = loginPath;
}

function isAuthenticated() {
    return !!localStorage.getItem('authToken');
}

// Alias for compatibility with existing pages
function checkAuthentication() {
    return isAuthenticated();
}

// Assessment Functions
async function getAssessments() {
    try {
        return await apiRequest('/assessments/');
    } catch (error) {
        return { data: [] }; // Fallback to empty array
    }
}

async function getAssessmentCategories() {
    try {
        return await apiRequest('/assessments/categories/');
    } catch (error) {
        return { data: [] };
    }
}

async function startAssessment(assessmentId) {
    try {
        return await apiRequest(`/assessments/${assessmentId}/start/`, {
            method: 'POST'
        });
    } catch (error) {
        console.error('Failed to start assessment:', error);
        return null;
    }
}

async function submitAssessmentAnswers(assessmentId, answers) {
    try {
        return await apiRequest(`/assessments/${assessmentId}/submit/`, {
            method: 'POST',
            body: JSON.stringify({ answers })
        });
    } catch (error) {
        console.error('Failed to submit assessment:', error);
        return null;
    }
}

// Appointment Functions
async function getCounselors() {
    try {
        return await apiRequest('/appointments/counselors/');
    } catch (error) {
        return { data: [] };
    }
}

async function bookAppointment(appointmentData) {
    try {
        return await apiRequest('/appointments/', {
            method: 'POST',
            body: JSON.stringify(appointmentData)
        });
    } catch (error) {
        showNotification('Failed to book appointment', 'error');
        return null;
    }
}

async function getUserAppointments() {
    try {
        return await apiRequest('/appointments/');
    } catch (error) {
        return { data: [] };
    }
}

// Chat Functions - Compatible with Student UI
async function createChatSession() {
    try {
        return await apiRequest('/chat-conversations/', {
            method: 'POST',
            body: JSON.stringify({
                title: 'Chat Session',
                session_type: 'ai_chat'
            })
        });
    } catch (error) {
        console.error('Failed to create chat session:', error);
        return null;
    }
}

async function sendChatMessage(conversationId, message, messageType = 'user') {
    try {
        return await apiRequest('/chat-messages/', {
            method: 'POST',
            body: JSON.stringify({
                conversation: conversationId,
                content: message,
                message_type: messageType
            })
        });
    } catch (error) {
        console.error('Failed to send message:', error);
        return null;
    }
}

async function getChatMessages(conversationId) {
    try {
        return await apiRequest(`/chat-messages/?conversation=${conversationId}`);
    } catch (error) {
        return { data: [] };
    }
}

// AI Chat Integration
async function getAIResponse(sessionId, message, mode = 'hybrid') {
    try {
        const response = await apiRequest('/ai-chat/', {
            method: 'POST',
            body: JSON.stringify({
                sessionId: sessionId,
                message: message,
                mode: mode
            })
        });
        
        if (response.crisis) {
            // Handle crisis response
            return {
                isCrisis: true,
                message: response.message,
                helpline: response.helpline
            };
        }
        
        return {
            isSuccess: response.success,
            response: response.response,
            error: response.error
        };
    } catch (error) {
        console.error('Failed to get AI response:', error);
        return {
            isSuccess: false,
            error: 'Failed to connect to AI service',
            response: 'I apologize, but I\'m having trouble responding right now. Please try again in a moment.'
        };
    }
}

// Wellness Functions
async function getWellnessActivities() {
    try {
        return await apiRequest('/wellness/activities/');
    } catch (error) {
        return { data: [] };
    }
}

async function getWellnessGames() {
    try {
        return await apiRequest('/wellness/games/');
    } catch (error) {
        return { data: [] };
    }
}

async function startWellnessActivity(activityId) {
    try {
        return await apiRequest(`/wellness/activities/${activityId}/start/`, {
            method: 'POST'
        });
    } catch (error) {
        console.error('Failed to start activity:', error);
        return null;
    }
}

async function completeWellnessActivity(activityId, data) {
    try {
        return await apiRequest(`/wellness/activities/${activityId}/complete/`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    } catch (error) {
        console.error('Failed to complete activity:', error);
        return null;
    }
}

// Resources Functions
async function getResources() {
    try {
        return await apiRequest('/resources/');
    } catch (error) {
        return { data: [] };
    }
}

async function getResourceCategories() {
    try {
        return await apiRequest('/resources/categories/');
    } catch (error) {
        return { data: [] };
    }
}

async function bookmarkResource(resourceId) {
    try {
        return await apiRequest(`/resources/${resourceId}/bookmark/`, {
            method: 'POST'
        });
    } catch (error) {
        console.error('Failed to bookmark resource:', error);
        return null;
    }
}

// Community Functions
async function getForumPosts() {
    try {
        return await apiRequest('/community/posts/');
    } catch (error) {
        return { data: [] };
    }
}

async function createForumPost(postData) {
    try {
        return await apiRequest('/community/posts/', {
            method: 'POST',
            body: JSON.stringify(postData)
        });
    } catch (error) {
        showNotification('Failed to create post', 'error');
        return null;
    }
}

// UI Helper Functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
    
    // Click to close
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });
}

function showLoader(show = true) {
    let loader = document.getElementById('globalLoader');
    if (!loader && show) {
        loader = document.createElement('div');
        loader.id = 'globalLoader';
        loader.className = 'global-loader';
        loader.innerHTML = '<div class="loader-spinner"></div>';
        document.body.appendChild(loader);
    }
    
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
}

// Initialize app
function initializeApp() {
    loadCurrentUser();
    
    // Add global styles for notifications and loader
    if (!document.getElementById('manas-global-styles')) {
        const styles = document.createElement('style');
        styles.id = 'manas-global-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
                padding: 15px;
                border-radius: 8px;
                color: white;
                animation: slideIn 0.3s ease-out;
            }
            .notification.success { background-color: #4CAF50; }
            .notification.error { background-color: #f44336; }
            .notification.info { background-color: #2196F3; }
            .notification-close { 
                background: none; 
                border: none; 
                color: white; 
                font-size: 18px; 
                cursor: pointer; 
                float: right; 
            }
            .global-loader {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            }
            .loader-spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #7BA098;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(styles);
    }
}

// Notification Helper
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? '#ff4444' : type === 'success' ? '#44ff44' : '#4444ff'};
        color: white;
        border-radius: 5px;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Loader Helper
function showLoader(show) {
    console.log(`Loader: ${show ? 'shown' : 'hidden'}`);
}

// Authentication Guard for Protected Pages
function requireAuth() {
    if (!isAuthenticated()) {
        showNotification('Please login to access this page', 'error');
        
        // Determine correct path to login page
        const pathSegments = window.location.pathname.split('/');
        let loginPath = '../auth/login.html';
        
        if (pathSegments.includes('auth')) {
            loginPath = 'login.html';
        } else if (pathSegments.length <= 3) {
            loginPath = 'pages/auth/login.html';
        }
        
        window.location.href = loginPath;
        return false;
    }
    return true;
}

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', initializeApp);

// Export for use in other files
window.MANAS_API = {
    login,
    register,
    logout,
    isAuthenticated,
    checkAuthentication,
    requireAuth,
    getAssessments,
    getAssessmentCategories,
    startAssessment,
    submitAssessmentAnswers,
    getCounselors,
    bookAppointment,
    getUserAppointments,
    createChatSession,
    sendChatMessage,
    getChatMessages,
    getAIResponse,
    getWellnessActivities,
    getWellnessGames,
    startWellnessActivity,
    completeWellnessActivity,
    getResources,
    getResourceCategories,
    bookmarkResource,
    getForumPosts,
    createForumPost,
    showNotification,
    showLoader,
    currentUser: () => currentUser,
    apiRequest
};
