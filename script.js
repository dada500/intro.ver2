// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Simple fade-in animation for sections
    const sections = document.querySelectorAll('section');
    
    function checkVisibility() {
        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            const isVisible = (rect.top <= window.innerHeight * 0.8);
            
            if (isVisible) {
                section.classList.add('visible');
            }
        });
    }
    
    // Initial check
    window.addEventListener('load', checkVisibility);
    window.addEventListener('scroll', checkVisibility);
    
    // Update copyright year automatically
    const currentYear = new Date().getFullYear();
    const footerYear = document.querySelector('footer p');
    if (footerYear) {
        footerYear.innerHTML = footerYear.innerHTML.replace('2023', currentYear);
    }
});

// Add CSS animation classes programmatically
window.onload = function() {
    // Add animations to skills section
    const skills = document.querySelectorAll('.skill');
    skills.forEach((skill, index) => {
        skill.style.animationDelay = `${index * 0.2}s`;
        skill.classList.add('animate-in');
    });
}; 