$(document).ready(function () {
    $("#generateButton").click(function () {
        var userInput = $("#userInput").val();
        $.ajax({
            type: "POST",
            url: "/generate_text",
            data: { writing_text: userInput },
            success: function (data) {
                $("#generatedText").val(data.generated_text);
            },
            error: function (xhr, status, error) {
                console.error("Error:", error);
            }
        });
    });
});


function generateText() {
    // Get user input
    const userInput = document.getElementById("userInput").value;

    // Make a POST request to Flask route
    fetch("/generate_text", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ writing_text: userInput })
    })
    .then(response => {
        if (!response.ok) {
            // Handle error response here
            throw new Error
            ("API request failed \nYou exceeded your current quota,\n please check your plan\nand billing details.");
        }
        return response.json();
    })
    .then(data => {
        // Display generated text
        document.getElementById("generatedText").innerText = data.generated_text.trim();
    })
    .catch(error => {
        console.error("Error:", error);

        // Display the error message to the user
        document.getElementById('error-message').textContent = "Error: " + error.message;
        document.getElementById('error-message').style.display = 'block';
    });
}

function capitalizeSentences(textarea) {
            // Get the current value of the textarea
            let currentValue = textarea.value;

            // Split the text into sentences based on periods followed by a space
            let sentences = currentValue.split('. ');

            // Capitalize the first letter of each sentence and join them back together
            let capitalizedText = sentences.map(sentence => {
                return sentence.charAt(0).toUpperCase() + sentence.slice(1);
            }).join('. ');

            // Set the updated value
            textarea.value = capitalizedText;
        }

let userTextData = ""; // Initialize a variable to store the text data
let typingTimeout; // Initialize a variable to track typing timeout

// Function to handle the "Start" button click
document.getElementById('start-button').addEventListener('click', function () {
    // Show the textarea container
    const textareaContainer = document.getElementById('textarea-container');
    textareaContainer.style.display = 'block';

    // Focus on the textarea
    const textarea = document.getElementById('userInput');
    textarea.focus();

    // Listen for input in the textarea
    textarea.addEventListener('input', function () {
        // Clear any previous typing timeout
        clearTimeout(typingTimeout);

        // Set a new typing timeout
        typingTimeout = setTimeout(function () {
            // If the user hasn't typed for 19 seconds, clear the textarea
            textarea.value = "";
        }, 19000); // 19000 milliseconds (19 seconds)
    });
});

// Add a click event listener to the "Final Result" button
document.getElementById('final_result').addEventListener('click', function () {
    // Check if the textarea is empty
    if (userTextData.trim() === "") {
        // Display an error message
        document.getElementById('error-message').textContent = "Please,\nYou Have To Write\nFirst ";
        document.getElementById('error-message').style.display = 'block';

        // Hide the "Final Result" content since there's no text
        document.getElementById('final-result-content').style.display = 'none';
    } else {
        // Clear any previous error message
        document.getElementById('error-message').textContent = "";
        document.getElementById('error-message').style.display = 'none';

        // Display the content in the "Final Result" section
        document.getElementById('final-result-content').textContent = userTextData;
        document.getElementById('final-result-content').style.display = 'block';
    }
});

// Listen for input in the textarea and store the text
document.getElementById('userInput').addEventListener('input', function () {
    userTextData = document.getElementById('userInput').value;
});

// Initially, hide the "Final Result" content and error message
document.getElementById('final-result-content').style.display = 'none';
document.getElementById('error-message').style.display = 'none';
