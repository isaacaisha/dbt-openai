// Show Popup Function
function showPopup() {
    $('#popupContainer').show(); // Show the popup container
}

// Hide Popup Function
function hidePopup() {
    $('#popupContainer').hide(); // Hide the popup container
}

// Event Listener for Show/Hide Popup Button
$('#showPopupButton').click(function () {
    // Check if the popup container is currently visible
    if ($('#popupContainer').is(':visible')) {
        hidePopup(); // If visible, hide the popup container
    } else {
        showPopup(); // If hidden, show the popup container
    }
});

// Event Listener for Close Popup Button
$('#closePopupButton').click(function () {
    hidePopup(); // Call the hidePopup function when the close button is clicked
});