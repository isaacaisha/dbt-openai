//HOME-SPEECH-REQUEST.JS

// Function to get the CSRF token from cookies
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Function to send a POST request to the server
function sendRequest(prompt) {
  const csrfToken = getCookie("csrf_token");
  showLoading();

  // Disable buttons
  disableButtons();

  xhr = new XMLHttpRequest(); // Use the global xhr variable
  xhr.open("POST", "/home/answer", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  xhr.setRequestHeader("X-CSRFToken", csrfToken);
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4) {
      hideLoading();
      enableButtons();

      if (xhr.status === 200) {
        processResponse(xhr.responseText);
      } else {
        handleRequestFailure();
      }
    }
  };
  xhr.send("prompt=" + encodeURIComponent(prompt));
}

// Function to show the loading indicator
function showLoading() {
  var loadingIndicator = document.getElementById("loading-indicator");
  var loadingCircle = document.getElementById("loading-circle");
  loadingIndicator.style.display = "block";
  loadingCircle.style.display = "block";
}

// Function to hide the loading indicator
function hideLoading() {
  var loadingIndicator = document.getElementById("loading-indicator");
  var loadingCircle = document.getElementById("loading-circle");
  loadingIndicator.style.display = "none";
  loadingCircle.style.display = "none";
}

// Function to disable buttons
function disableButtons() {
  document.getElementById("speechRecognitionButton").disabled = true;
  document.getElementById("generateButton").disabled = true;
  document.getElementById("playbackButton").disabled = true;
}

// Function to enable buttons
function enableButtons() {
  document.getElementById("speechRecognitionButton").disabled = false;
  document.getElementById("generateButton").disabled = false;
  document.getElementById("playbackButton").disabled = false;
}

// Function to handle request failure
function handleRequestFailure() {
  document.getElementById("interruptButton").style.display = "none";
}

// Function to process the server response
function processResponse(responseText) {
  var response = JSON.parse(responseText);

  // Check if there's a flash message and display it
  if (response.flash_message) {
    document.getElementById("flash-message").textContent =
      response.flash_message;
  }

  // Display the text response in the textarea
  var textarea = document.getElementById("generatedText");
  textarea.value = response.answer_text;

  // Store the detected language as a data attribute
  textarea.dataset.detectedLang = response.detected_lang || "es-ES";

  if (response.answer_text) {
    textarea.style.display = "block";
    smoothScrollToBottomWhileTyping(response.answer_text);
    speakText(response.answer_text, response.detected_lang);
  } else {
    textarea.style.display = "none";
  }

  handleAudioResponse(response.answer_audio_path);
}

// Function to handle the audio response
function handleAudioResponse(audioPath) {
  var audio = document.getElementById("response-audio");
  audio.src = audioPath;
  audio.style.display = "block";
  document.getElementById("playbackButton").classList.remove("hidden");
  document.getElementById("hrCrimson1").style.display = "block";
  document.getElementById("hrCrimson2").style.display = "block";
}

// Function to speak the text using SpeechSynthesis
function speakText(text, lang) {
  var speech = new SpeechSynthesisUtterance(text);
  speech.lang = lang || "es-ES";

  speech.onend = function () {
    document.getElementById("interruptButton").style.display = "none";
  };

  speech.onboundary = function (event) {
    if (event.name === "word") {
      smoothScrollToBottom();
    }
  };

  window.speechSynthesis.speak(speech);
}

// Function to smoothly scroll the textarea to the bottom
function smoothScrollToBottom() {
  var textarea = document.getElementById("generatedText");
  var start = textarea.scrollTop;
  var end = textarea.scrollHeight;
  var change = end - start;
  var duration = 1000; // Duration for scrolling
  var startTime = performance.now();

  function scroll(timestamp) {
    var elapsed = timestamp - startTime;
    var progress = Math.min(elapsed / duration, 1);
    textarea.scrollTop = start + change * progress;
    if (progress < 1) {
      requestAnimationFrame(scroll);
    }
  }

  requestAnimationFrame(scroll);
}

// Function to scroll gradually while text is being typed
function smoothScrollToBottomWhileTyping(text) {
  var textarea = document.getElementById("generatedText");
  textarea.value = ""; // Clear the textarea before typing starts

  var index = 0;
  var typingSpeed = 57; // Adjust this value to control typing speed
  var typingInProgress = true; // Set the typing flag to true

  function typeText() {
    if (!typingInProgress) return; // Exit if typing is interrupted
    if (index < text.length) {
      textarea.value += text[index++];
      textarea.scrollTop = textarea.scrollHeight; // Scroll to bottom as text is typed
      setTimeout(typeText, typingSpeed);
    } else {
      smoothScrollToBottom(); // Ensure final scroll to bottom
    }
  }

  typeText();
}

// Add an event listener to the form for submitting
document.addEventListener("DOMContentLoaded", function () {
  // Reference the audio element globally
  const audio = document.getElementById("response-audio");

  // Add an event listener to the form for submitting
  document
    .getElementById("prompt-form")
    .addEventListener("submit", function (e) {
      e.preventDefault();
      var prompt = document.getElementById("userInput").value; // Get text from the textarea
      sendRequest(prompt);
    });

  // Add an event listener to the playback button
  document
    .getElementById("playbackButton")
    .addEventListener("click", function () {
      const playbackButton = document.getElementById("playbackButton");

      // Ensure the correct audio reference is used
      if (audio.paused) {
        audio.play();
        playbackButton.textContent = "-¡!¡- Pause Audio -¡!¡-";
      } else {
        audio.pause();
        playbackButton.textContent = "-¡!¡- PlayBack Audio -¡!¡-";
      }
    });

  // Add an event listener to the audio element for playback
  audio.addEventListener("click", function () {
    audio.play();
  });
});
