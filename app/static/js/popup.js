// Show Popup Function
function showPopup() {
    $('#popupContainer').show(); // Show the popup container
}

// Hide Popup Function
function hidePopup() {
    $('#popupContainer').hide(); // Hide the popup container
}

// Event Listener for Show Popup Button
$('#showPopupButton').click(function () {
    showPopup(); // Call the showPopup function when the button is clicked
});

// Event Listener for Close Popup Button
$('#closePopupButton').click(function () {
    hidePopup(); // Call the hidePopup function when the close button is clicked
});