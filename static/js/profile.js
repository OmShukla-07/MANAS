/* MANAS Profile Page JavaScript */

// Global variables
let currentUserData = null;
let currentAction = null;

// Initialize profile page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Profile page loaded');
    console.log('Auth token:', localStorage.getItem('authToken'));
    
    // Check authentication
    if (!isAuthenticated()) {
        console.log('Not authenticated, redirecting...');
        showNotification('Please login first', 'error');
        setTimeout(() => {
            window.location.href = '../auth/login.html';
        }, 2000);
        return;
    }
    
    console.log('User is authenticated, initializing profile...');
    
    // Initialize profile
    initializeProfile();
    
    // Set up event listeners
    setupEventListeners();
});

// Initialize profile data
async function initializeProfile() {
    showLoadingOverlay(true);
    
    try {
        await loadUserProfile();
        hideLoadingOverlay();
    } catch (error) {
        console.error('Failed to load profile:', error);
        showNotification('Failed to load profile data', 'error');
        hideLoadingOverlay();
    }
}

// Load user profile from API
async function loadUserProfile() {
    try {
        const response = await apiRequest('/auth/user/');
        
        if (response && response.success && response.data) {
            currentUserData = response.data;
            populateProfileData(currentUserData);
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Profile load error:', error);
        
        // Fallback: try to get user data from localStorage
        const userData = localStorage.getItem('user');
        if (userData) {
            try {
                currentUserData = JSON.parse(userData);
                populateProfileData(currentUserData);
                showNotification('Profile loaded from cache', 'success');
            } catch (e) {
                throw new Error('Failed to load profile data');
            }
        } else {
            throw error;
        }
    }
}

// Populate profile data in the UI
function populateProfileData(userData) {
    // Basic user info
    const fullName = userData.full_name || `${userData.first_name || ''} ${userData.last_name || ''}`.trim() || userData.username || 'User';
    
    // Update avatar and basic info
    document.getElementById('userName').textContent = fullName;
    document.getElementById('userType').textContent = (userData.user_type || 'student').charAt(0).toUpperCase() + (userData.user_type || 'student').slice(1);
    document.getElementById('userBio').textContent = userData.bio || 'Not provided';
    
    // Update avatar initial
    const initial = fullName.charAt(0).toUpperCase();
    document.getElementById('avatarInitial').textContent = initial;
    
    // Update profile details
    document.getElementById('username').textContent = userData.username || 'Not provided';
    document.getElementById('email').textContent = userData.email || 'Not provided';
    document.getElementById('phoneNumber').textContent = userData.phone_number || 'Not provided';
    
    // Format date of birth
    if (userData.date_of_birth) {
        const date = new Date(userData.date_of_birth);
        document.getElementById('dateOfBirth').textContent = date.toLocaleDateString();
    } else {
        document.getElementById('dateOfBirth').textContent = 'Not provided';
    }
    
    // Format member since date
    if (userData.created_at) {
        const date = new Date(userData.created_at);
        document.getElementById('memberSince').textContent = date.toLocaleDateString();
        document.getElementById('memberSince').classList.remove('loading');
    } else {
        document.getElementById('memberSince').textContent = 'Not available';
        document.getElementById('memberSince').classList.remove('loading');
    }
    
    // Update wellness data
    const profile = userData.profile || {};
    document.getElementById('stressLevel').textContent = profile.stress_level || '5';
    document.getElementById('sleepHours').textContent = profile.sleep_hours || '8';
    document.getElementById('exerciseFrequency').textContent = profile.exercise_frequency || 'Sometimes';
    document.getElementById('preferredLanguage').textContent = profile.preferred_language || 'English';
}

// Set up event listeners
function setupEventListeners() {
    // Stress level range input
    const stressLevelInput = document.getElementById('editStressLevel');
    if (stressLevelInput) {
        stressLevelInput.addEventListener('input', function() {
            document.getElementById('stressLevelDisplay').textContent = this.value;
        });
    }
    
    // Close modals when clicking outside
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal-overlay')) {
            closeModals();
        }
    });
    
    // Handle escape key to close modals
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeModals();
        }
    });
}

// Enable edit mode
function enableEditMode() {
    if (!currentUserData) {
        showNotification('Profile data not loaded', 'error');
        return;
    }
    
    // Populate edit form with current data
    document.getElementById('editFirstName').value = currentUserData.first_name || '';
    document.getElementById('editLastName').value = currentUserData.last_name || '';
    document.getElementById('editEmail').value = currentUserData.email || '';
    document.getElementById('editPhone').value = currentUserData.phone_number || '';
    document.getElementById('editBio').value = currentUserData.bio || '';
    
    // Populate wellness data
    const profile = currentUserData.profile || {};
    document.getElementById('editStressLevel').value = profile.stress_level || 5;
    document.getElementById('stressLevelDisplay').textContent = profile.stress_level || 5;
    document.getElementById('editSleepHours').value = profile.sleep_hours || 8;
    document.getElementById('editExerciseFrequency').value = profile.exercise_frequency || 'Sometimes';
    document.getElementById('editPreferredLanguage').value = profile.preferred_language || 'English';
    
    // Show edit modal
    showModal('editModal');
}

// Save profile changes
async function saveProfile() {
    showLoadingOverlay(true);
    
    try {
        const formData = new FormData(document.getElementById('editProfileForm'));
        const updateData = {};
        
        // Collect form data
        for (let [key, value] of formData.entries()) {
            updateData[key] = value;
        }
        
        // Send update request
        const response = await apiRequest('/auth/profile/', {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
        
        if (response && response.success) {
            // Update current user data
            currentUserData = response.data;
            
            // Update localStorage
            localStorage.setItem('user', JSON.stringify(currentUserData));
            
            // Refresh profile display
            populateProfileData(currentUserData);
            
            // Close modal and show success
            closeEditModal();
            showNotification('Profile updated successfully!', 'success');
        } else {
            throw new Error(response.message || 'Failed to update profile');
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showNotification('Failed to update profile: ' + error.message, 'error');
    } finally {
        hideLoadingOverlay();
    }
}

// Delete user data
function deleteData() {
    currentAction = 'deleteData';
    showConfirmModal(
        'Delete All Data',
        'Are you sure you want to delete all your data? This action cannot be undone and will remove all your assessments, appointments, and wellness data.',
        'Delete Data'
    );
}

// Delete user account
function deleteAccount() {
    currentAction = 'deleteAccount';
    showConfirmModal(
        'Delete Account',
        'Are you sure you want to permanently delete your account? This will remove all your data and you will not be able to recover it.',
        'Delete Account'
    );
}

// Logout function
function logout() {
    currentAction = 'logout';
    showConfirmModal(
        'Logout',
        'Are you sure you want to logout?',
        'Logout'
    );
}

// Confirm action handler
async function confirmAction() {
    closeConfirmModal();
    
    switch (currentAction) {
        case 'deleteData':
            await handleDeleteData();
            break;
        case 'deleteAccount':
            await handleDeleteAccount();
            break;
        case 'logout':
            handleLogout();
            break;
    }
    
    currentAction = null;
}

// Handle delete data
async function handleDeleteData() {
    showLoadingOverlay(true);
    
    try {
        // Call API to delete user data (keeping account)
        const response = await apiRequest('/auth/delete-data/', {
            method: 'DELETE'
        });
        
        if (response && response.success) {
            showNotification('All your data has been deleted successfully', 'success');
            
            // Refresh profile to show cleared data
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            throw new Error(response.message || 'Failed to delete data');
        }
    } catch (error) {
        console.error('Delete data error:', error);
        showNotification('Failed to delete data: ' + error.message, 'error');
    } finally {
        hideLoadingOverlay();
    }
}

// Handle delete account
async function handleDeleteAccount() {
    showLoadingOverlay(true);
    
    try {
        // Call API to delete entire account
        const response = await apiRequest('/auth/delete-account/', {
            method: 'DELETE'
        });
        
        if (response && response.success) {
            showNotification('Account deleted successfully', 'success');
            
            // Clear all local storage and redirect
            localStorage.clear();
            setTimeout(() => {
                window.location.href = '../auth/login.html';
            }, 2000);
        } else {
            throw new Error(response.message || 'Failed to delete account');
        }
    } catch (error) {
        console.error('Delete account error:', error);
        showNotification('Failed to delete account: ' + error.message, 'error');
    } finally {
        hideLoadingOverlay();
    }
}

// Handle logout
function handleLogout() {
    try {
        // Clear all authentication data
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        localStorage.removeItem('assessmentProgress');
        
        showNotification('Logged out successfully', 'success');
        
        // Redirect to login page
        setTimeout(() => {
            window.location.href = '../auth/login.html';
        }, 1000);
    } catch (error) {
        console.error('Logout error:', error);
        // Force redirect even if there's an error
        window.location.href = '../auth/login.html';
    }
}

// Modal helper functions
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

function closeModals() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.classList.remove('active');
    });
    document.body.style.overflow = 'auto';
}

function closeEditModal() {
    hideModal('editModal');
}

function showConfirmModal(title, message, buttonText) {
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    document.getElementById('confirmButton').textContent = buttonText;
    showModal('confirmModal');
}

function closeConfirmModal() {
    hideModal('confirmModal');
}

// Loading overlay functions
function showLoadingOverlay(show = true) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        if (show) {
            overlay.classList.remove('hidden');
            console.log('Showing loading overlay');
        } else {
            overlay.classList.add('hidden');
            console.log('Hiding loading overlay');
        }
    } else {
        console.error('Loading overlay element not found');
    }
}

function hideLoadingOverlay() {
    showLoadingOverlay(false);
}

// Notification functions
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const messageElement = document.getElementById('notificationMessage');
    
    if (notification && messageElement) {
        messageElement.textContent = message;
        notification.className = `notification ${type} show`;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            closeNotification();
        }, 5000);
    }
}

function closeNotification() {
    const notification = document.getElementById('notification');
    if (notification) {
        notification.classList.remove('show');
    }
}

// Utility function to check if user is authenticated
function isAuthenticated() {
    return !!localStorage.getItem('authToken');
}
