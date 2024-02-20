document.addEventListener('DOMContentLoaded', function () {
    var navLinks = document.querySelectorAll('.nav-link');
    var currentUrl = '{{ current_url }}';  // Use Flask to pass the current URL from the server

    navLinks.forEach(function (link) {
        if (link.getAttribute('href') === currentUrl) {
            link.classList.add('active');
        }
    });

    // Update active state when user navigates using history API
    window.addEventListener('popstate', function () {
        var currentUrl = window.location.pathname;

        navLinks.forEach(function (link) {
            link.classList.toggle('active', link.getAttribute('href') === currentUrl);
        });
    });
});
