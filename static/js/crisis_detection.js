/**
 * Crisis Detection Client-Side Script
 * Detects crisis keywords and shows immediate helpline popup
 */

(function() {
    'use strict';
    
    // Crisis keywords patterns (client-side detection)
    const CRISIS_PATTERNS = {
        severe: [
            // Suicide ideation
            /\b(kill myself|end my life|suicide|suicidal|want to die|going to die)\b/i,
            /\b(no reason to live|better off dead|can't go on|ending it all)\b/i,
            /\b(take my life|don't want to live|tired of living|done with life)\b/i,
            /\b(goodbye world|this is my last|final message|leaving forever)\b/i,
            
            // Self-harm
            /\b(cut myself|hurt myself|harm myself|self harm|self-harm|cutting)\b/i,
            /\b(slash my wrists|slit my wrists|hurt my body)\b/i,
            
            // Methods
            /\b(overdose|pills to end|jump off|hang myself|hanging myself)\b/i,
            /\b(knife to|gun to|poison myself|drown myself)\b/i,
            
            // Final goodbyes
            /\b(goodbye forever|this is goodbye|final goodbye|suicide note|last words)\b/i,
            /\b(saying goodbye|won't see you again|this is the end)\b/i,
            
            // Direct expressions
            /\b(kill me|death wish|ready to die|planning suicide)\b/i,
            /\b(end it all|finish it|can't live|won't survive)\b/i,
            
            // Hindi/Hinglish terms
            /\b(marna chahta|mar jaana chahta|zinda nahi rehna|khud ko khatam)\b/i,
            /\b(suicide kar lunga|maar dalunga khud ko)\b/i
        ],
        moderate: [
            // Hopelessness
            /\b(hopeless|no hope|nothing matters|pointless|worthless|useless)\b/i,
            /\b(life is meaningless|no purpose|empty inside|hollow)\b/i,
            
            // Despair
            /\b(give up|giving up|can't take it|too much pain|unbearable)\b/i,
            /\b(can't cope|breaking down|falling apart|lost all hope)\b/i,
            
            // Isolation
            /\b(everyone hates me|nobody cares|all alone|so alone|completely alone)\b/i,
            /\b(no one understands|nobody loves me|isolated|lonely|abandoned)\b/i,
            
            // Self-deprecation
            /\b(want to disappear|wish I was dead|wish I wasn't born)\b/i,
            /\b(burden to everyone|better without me|shouldn't exist)\b/i,
            /\b(hate myself|disgusted with myself|failure|worthless person)\b/i,
            
            // Desperation
            /\b(can't go on|can't continue|can't handle|too difficult)\b/i,
            /\b(want it to stop|make it stop|end the pain|escape this)\b/i,
            
            // Academic/social pressure
            /\b(failed everything|ruined my life|destroyed everything|no future)\b/i,
            /\b(disappointed everyone|let everyone down|can't face anyone)\b/i,
            
            // Hindi/Hinglish terms
            /\b(koi umeed nahi|sab khatam|jeena mushkil|bardaasht nahi)\b/i,
            /\b(koi parwaah nahi|akela hun|koi nahi samajhta)\b/i
        ],
        low: [
            // Distress
            /\b(depressed|very sad|extremely sad|feeling down|really low)\b/i,
            /\b(anxious|stressed out|overwhelmed|can't sleep|sleepless)\b/i,
            /\b(panic attack|anxiety attack|breaking point|edge)\b/i,
            
            // Emotional pain
            /\b(hurting so much|in pain|suffering|aching|broken)\b/i,
            /\b(crying all day|can't stop crying|tears won't stop)\b/i,
            
            // Warning signs
            /\b(losing interest|don't care anymore|numb|empty|void)\b/i,
            /\b(tired of trying|exhausted|drained|burnt out)\b/i
        ]
    };
    
    // India-centric helpline numbers
    const HELPLINES = {
        icall: { 
            number: '9152987821', 
            label: 'iCall Psychosocial Helpline', 
            description: 'Mon-Sat, 8 AM - 10 PM (English, Hindi, Marathi)'
        },
        kiran: { 
            number: '1800-599-0019', 
            label: 'KIRAN Mental Health Helpline', 
            description: '24/7, Toll-free (Multiple Indian languages)'
        },
        vandrevala: { 
            number: '9999666555', 
            label: 'Vandrevala Foundation Helpline', 
            description: '24/7 (English, Hindi)'
        },
        aasra: { 
            number: '9820466726', 
            label: 'AASRA (Mumbai)', 
            description: '24/7 Crisis helpline'
        },
        sneha: { 
            number: '044-24640050', 
            label: 'SNEHA (Chennai)', 
            description: '24/7 Suicide prevention'
        },
        emergency: { 
            number: '112', 
            label: 'Emergency Services (India)', 
            description: 'Police, Ambulance, Fire - All emergencies'
        }
    };
    
    /**
     * Detect crisis keywords in text
     */
    function detectCrisis(text) {
        if (!text || text.trim().length === 0) return null;
        
        console.log('🔍 Checking for crisis keywords in:', text);
        
        // Check severe patterns
        for (let pattern of CRISIS_PATTERNS.severe) {
            if (pattern.test(text)) {
                console.log('🚨 SEVERE crisis detected!');
                return { severity: 'severe', level: 9 };
            }
        }
        
        // Check moderate patterns
        for (let pattern of CRISIS_PATTERNS.moderate) {
            if (pattern.test(text)) {
                console.log('⚠️ MODERATE crisis detected');
                return { severity: 'moderate', level: 6 };
            }
        }
        
        console.log('✅ No crisis detected');
        return null;
    }
    
    /**
     * Show crisis helpline popup
     */
    function showCrisisPopup(severity) {
        console.log('🚨 Showing crisis popup - Severity:', severity);
        
        // Remove existing popup if any
        const existing = document.getElementById('crisis-popup');
        if (existing) {
            console.log('Removing existing popup');
            existing.remove();
        }
        
        // Create popup HTML
        const popup = document.createElement('div');
        popup.id = 'crisis-popup';
        popup.className = `crisis-popup ${severity}`;
        popup.innerHTML = `
            <div class="crisis-popup-overlay"></div>
            <div class="crisis-popup-content">
                <div class="crisis-popup-header ${severity}">
                    <span class="crisis-icon">${severity === 'severe' ? '🚨' : '⚠️'}</span>
                    <h2>We're Concerned About You</h2>
                    <button class="crisis-close" aria-label="Close">&times;</button>
                </div>
                
                <div class="crisis-popup-body">
                    <p class="crisis-message">
                        ${severity === 'severe' 
                            ? 'Your message suggests you may be in crisis. <strong>Your safety is the top priority.</strong> Please reach out for immediate help.'
                            : 'We noticed you might be going through a difficult time. You don\'t have to face this alone - help is available.'
                        }
                    </p>
                    
                    <div class="helpline-section">
                        <h3>🆘 Immediate Help Available:</h3>
                        <div class="helpline-list">
                            ${Object.entries(HELPLINES).map(([key, info]) => `
                                <div class="helpline-item ${key === 'emergency' && severity === 'severe' ? 'urgent' : ''}">
                                    <div class="helpline-info">
                                        <strong class="helpline-label">${info.label}</strong>
                                        <p class="helpline-desc">${info.description}</p>
                                    </div>
                                    <a href="tel:${info.number}" class="helpline-number">
                                        📞 ${info.number}
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    ${severity === 'severe' ? `
                        <div class="urgent-notice">
                            <strong>⚠️ If you're in immediate danger, please call 911 or go to your nearest emergency room.</strong>
                        </div>
                    ` : ''}
                    
                    <div class="crisis-actions">
                        <button class="btn-crisis-primary" onclick="window.open('tel:988')">
                            📞 Call 988 Now
                        </button>
                        <button class="btn-crisis-secondary" id="crisis-continue">
                            I'm Safe - Continue Chat
                        </button>
                    </div>
                    
                    <p class="crisis-footer">
                        <small>
                            This message has been flagged and campus counselors have been notified. 
                            Someone from our team will reach out to you soon.
                        </small>
                    </p>
                </div>
            </div>
        `;
        
        document.body.appendChild(popup);
        
        // Add event listeners
        const closeBtn = popup.querySelector('.crisis-close');
        const continueBtn = popup.querySelector('#crisis-continue');
        const overlay = popup.querySelector('.crisis-popup-overlay');
        
        const closePopup = () => {
            popup.classList.add('closing');
            setTimeout(() => popup.remove(), 300);
        };
        
        closeBtn?.addEventListener('click', closePopup);
        continueBtn?.addEventListener('click', closePopup);
        overlay?.addEventListener('click', closePopup);
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        popup.addEventListener('remove', () => {
            document.body.style.overflow = '';
        });
        
        // Auto-focus on primary button for severe cases
        if (severity === 'severe') {
            setTimeout(() => {
                popup.querySelector('.btn-crisis-primary')?.focus();
            }, 100);
        }
    }
    
    /**
     * Send crisis alert to backend
     */
    async function sendCrisisAlert(message, severity, level) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value 
                           || document.querySelector('meta[name="csrf-token"]')?.content;
            
            const response = await fetch('/chat/api/crisis-alert/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    message: message,
                    severity: severity,
                    crisis_level: level,
                    client_detected: true
                })
            });
            
            if (!response.ok) {
                console.error('Failed to send crisis alert to backend');
            }
        } catch (error) {
            console.error('Error sending crisis alert:', error);
        }
    }
    
    /**
     * Monitor chat input for crisis keywords
     */
    function initCrisisDetection() {
        // Monitor chat input field
        const chatInput = document.getElementById('messageInput') 
                       || document.querySelector('textarea[name="message"]')
                       || document.querySelector('.chat-input');
        
        if (!chatInput) {
            console.warn('Chat input not found for crisis detection');
            return;
        }
        
        let detectionTimeout;
        
        chatInput.addEventListener('input', function(e) {
            clearTimeout(detectionTimeout);
            
            // Debounce detection (check 500ms after user stops typing)
            detectionTimeout = setTimeout(() => {
                const text = e.target.value;
                const detection = detectCrisis(text);
                
                if (detection && detection.severity === 'severe') {
                    // Immediate popup for severe cases
                    showCrisisPopup(detection.severity);
                    sendCrisisAlert(text, detection.severity, detection.level);
                }
            }, 500);
        });
        
        // Also check on form submit
        const chatForm = chatInput.closest('form') || document.querySelector('.chat-form');
        if (chatForm) {
            chatForm.addEventListener('submit', function(e) {
                const text = chatInput.value;
                const detection = detectCrisis(text);
                
                if (detection) {
                    // Show popup for any crisis level on send
                    showCrisisPopup(detection.severity);
                    sendCrisisAlert(text, detection.severity, detection.level);
                    
                    // For severe cases, prevent immediate send and show alert first
                    if (detection.severity === 'severe') {
                        e.preventDefault();
                        setTimeout(() => {
                            // Allow send after user sees the popup
                            chatForm.submit();
                        }, 2000);
                    }
                }
            });
        }
        
        console.log('✅ Crisis detection initialized');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCrisisDetection);
    } else {
        initCrisisDetection();
    }
    
    // Expose for manual testing
    window.ManasCrisisDetection = {
        detect: detectCrisis,
        showPopup: showCrisisPopup,
        sendAlert: sendCrisisAlert
    };
})();
