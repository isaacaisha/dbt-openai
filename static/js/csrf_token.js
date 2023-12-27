// Function to handle AJAX requests with CSRF token inclusion using fetch
async function makeAjaxRequest(method, url, data) {
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: new URLSearchParams(data),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const responseData = await response.text();
        return responseData;
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Function to handle form submission with AJAX using fetch
function handleFormSubmission(event) {
    event.preventDefault();

    const form = event.target.closest('form');

    if (form) {
        const formData = new FormData(form);

        makeAjaxRequest('POST', form.action, formData)
            .then((response) => {
                // Handle success response here
                console.log(response);
            })
            .catch((error) => {
                // Handle error here
                console.error('Error:', error);
            });
    }
}

// Attach the handleFormSubmission function to all submit buttons in forms
document.querySelectorAll('form button[type="submit"]').forEach(function (button) {
    button.addEventListener('click', handleFormSubmission);
});
