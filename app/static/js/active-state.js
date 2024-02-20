// Get all navigation links except for the class -> remove-active-state 
var navLinks = document.querySelectorAll('.nav-link');

// Get the current URL
var currentUrl = window.location.pathname;

// Loop through each navigation link and add the active class if the URL matches
navLinks.forEach(function (link) {
    if (link.getAttribute('href') === currentUrl) {
        link.classList.add('active');
    }
});
