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

//JavaScript for scrolling down 
function scrollDown() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}

// Function to set the form action based on the button clicked
function setFormAction(action) {
    document.getElementById('formAction').value = action;
}
