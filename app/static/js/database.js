
// Function to toggle users container
function toggleUsers() {
    var container = document.getElementById('usersContainer');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}
// Function to toggle histories container
function toggleHistories() {
    var container = document.getElementById('historiesContainer');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}

// Function to toggle histories JSON container
function toggleHistoriesJson() {
    var container = document.getElementById('historiesContainerJson');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}

// Function to toggle themes container
function toggleThemes() {
    var container = document.getElementById('themesContainer');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}

// Function to toggle messages container
function toggleMessages() {
    var container = document.getElementById('messagesContainer');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}

// Function to toggle test histories container
function toggleTestHistories() {
    var container = document.getElementById('historiesTestContainer');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}

// Function to toggle blog posts container
function toggleBlogsPosts() {
    var container = document.getElementById('BlogPostsContainer');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}

// Function to toggle Portfolio reviews container
function togglePortfolioReviews() {
    var container = document.getElementById('PortfolioReviewsContainer');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}

// Function to toggle Portfolio reviews container
function toggleDrawingImages() {
    var container = document.getElementById('DrawingImagesContainer');
    container.style.display = (container.style.display === 'none') ? 'block' : 'none';
}


// JavaScript for scrolling down
function scrollDown() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}
