// Debug script to test button functionality
console.log('=== BUTTON DEBUG SCRIPT LOADED ===');

// Wait for page to load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking buttons...');
    
    // Log Django context
    console.log('Django context:', window.DJANGO_CONTEXT);
    
    // Find all buttons and links
    const buttons = document.querySelectorAll('button, a');
    console.log(`Found ${buttons.length} buttons/links on page`);
    
    // Add click listeners to debug
    buttons.forEach((button, index) => {
        button.addEventListener('click', function(e) {
            console.log(`Button ${index} clicked:`, {
                tag: button.tagName,
                text: button.textContent.trim().substring(0, 50),
                onClick: button.getAttribute('onclick'),
                href: button.getAttribute('href'),
                className: button.className
            });
            
            // Log the actual action being taken
            if (button.getAttribute('onclick')) {
                console.log('Has onclick attribute:', button.getAttribute('onclick'));
            }
        });
    });
    
    // Test function to manually navigate
    window.testNavigation = function() {
        console.log('Testing manual navigation...');
        console.log('Django context URLs:', {
            loginUrl: window.DJANGO_CONTEXT?.loginUrl,
            signupUrl: window.DJANGO_CONTEXT?.signupUrl,
            homeUrl: window.DJANGO_CONTEXT?.homeUrl
        });
        
        // Test direct navigation
        if (window.DJANGO_CONTEXT?.loginUrl) {
            console.log('Attempting navigation to:', window.DJANGO_CONTEXT.loginUrl);
            window.location.href = window.DJANGO_CONTEXT.loginUrl;
        }
    };
    
    console.log('Debug script ready. Call testNavigation() in console to test.');
});