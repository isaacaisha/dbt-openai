// Function to retrieve the CSRF token from the hidden span
function getCSRFToken() {
    return document.getElementById('csrf-token').textContent;
}

// Function to handle AJAX requests with CSRF token inclusion
function makeAjaxRequest(method, url, data, successCallback, errorCallback) {
    // Create a new XMLHttpRequest object
    const xhr = new XMLHttpRequest();

    // Define the type of request, the URL, and whether the request should be asynchronous
    xhr.open(method, url, true);

    // Set the request header to include the CSRF token
    xhr.setRequestHeader('X-CSRFToken', getCSRFToken());

    // Define the callback functions to handle the response
    xhr.onload = function () {
        if (xhr.status === 200) {
            successCallback(xhr.responseText);
        } else {
            errorCallback(xhr.status, xhr.statusText);
        }
    };

    xhr.onerror = function () {
        errorCallback(xhr.status, xhr.statusText);
    };

    // Convert the data object to a URL-encoded string
    const formData = new URLSearchParams();
    for (const key in data) {
        formData.append(key, data[key]);
    }

    // Send the request with the form data
    xhr.send(formData);
}

// Function to handle form submission with AJAX
function handleFormSubmission(event) {
    // Prevent the default form submission behavior
    event.preventDefault();

    // Get the form associated with the submit button
    const form = event.target.closest('form');

    if (form) {
        // Extract form data
        const formData = new FormData(form);

        // Call the generic AJAX request function
        makeAjaxRequest('POST', form.action, formData,
            function (response) {
                // Handle success response here
                console.log(response);
            },
            function (status, statusText) {
                // Handle error here
                console.error('Error:', status, statusText);
            }
        );
    }
}

// Attach the handleFormSubmission function to all submit buttons in forms
document.querySelectorAll('form button[type="submit"]').forEach(function (button) {
    button.addEventListener('click', handleFormSubmission);
});
