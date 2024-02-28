// Function to update active state of navigation links
function updateActiveState() {
    // Get all navigation links
    var navLinks = document.querySelectorAll('.nav-link');

    // Get the current URL
    var currentUrl = window.location.pathname;

    // Loop through each navigation link and add or remove the active class
    navLinks.forEach(function (link) {
        if (link.getAttribute('href') === currentUrl) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Update active state when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    updateActiveState();
});

// Update active state when navigating between pages using history API (e.g., back/forward buttons)
window.addEventListener('popstate', function () {
    updateActiveState();
});
