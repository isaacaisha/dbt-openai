// DRAWING-GENERATOR.JS


document.addEventListener('DOMContentLoaded', function () {
    // Element references
    const generationTypeElement = document.getElementById('generationType');
    const uploadContainer = document.getElementById('upload-container');
    const fileInput = document.getElementById('imageUpload');
    const analyzeFileInput = document.getElementById('analyzeImageUpload');
    const generateButton = document.getElementById('generateDrawingButton');
    const userImageDisplay = document.getElementById('user-image-display');
    const generatedImageDisplay = document.getElementById('generated-image-display');
    const saveButton = document.getElementById('saveImage');
    const analyzeButton = document.getElementById('analyzeButton');
    const imageDisplayContainer = document.getElementById('uploaded-image-display');

    // Event Listeners
    setupEventListeners();

    function setupEventListeners() {
        setupGenerationTypeChange();
        setupGenerateButtonClick();
        setupAnalyzeButtonClick();  // This now directly triggers file input
    }

    function setupGenerationTypeChange() {
        generationTypeElement.addEventListener('change', (event) => {
            const requiresUpload = ['edits', 'face-to-sticker'].includes(event.target.value);
            uploadContainer.style.display = requiresUpload ? 'block' : 'none';
        });
    }

    function setupGenerateButtonClick() {
        generateButton.addEventListener("click", async (event) => {
          event.preventDefault(); // Prevent default form submission

          const generateDraw = document.getElementById("generateDraw").value;
          const generationType = generationTypeElement.value;

          // Check if image upload is necessary and available
          if (
            ["edits", "face-to-sticker"].includes(generationType) &&
            fileInput.files.length === 0
          ) {
            alert("Please select an image to upload.");
            return;
          }

          let imageDataURL = null;
          if (fileInput.files.length > 0) {
            const fileReader = new FileReader();
            fileReader.readAsDataURL(fileInput.files[0]);
            await new Promise((resolve) => (fileReader.onloadend = resolve));
            imageDataURL = fileReader.result.split(",")[1]; // Extract base64 part
            userImageDisplay.innerHTML = `<img src="${fileReader.result}" alt="Uploaded Image" class="image_display"/>`;
          }

          generateDrawing(generateDraw, generationType, imageDataURL);
        });
    }

    async function generateDrawing(generateDraw, generationType, imageDataURL) {
        document.getElementById('loading-indicator2').style.display = 'block';
        document.getElementById('loading-circle2').style.display = 'block';
        document.getElementById('error-message').style.display = 'none';

        try {
            const response = await fetch('/drawing-generator', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ generate_draw: generateDraw, type: generationType, image_data: imageDataURL })
            });
            const data = await response.json();
            document.getElementById('loading-indicator2').style.display = 'none';
            document.getElementById('loading-circle2').style.display = 'none';

            if (response.ok) {
                generatedImageDisplay.innerHTML = `<img src="${data.drawing_url}" alt="Generated Image" class="image_display mb-1" style="max-width: 100%; height: auto;"/>`;
                saveButton.innerHTML = `<a href="${data.drawing_url}" download="GeneratedImage.png">Save Image</a>`;
                saveButton.style.display = 'block';
            } else {
                throw new Error(data.error || 'An error occurred.');
            }
        } catch (error) {
            handleError(error);
        }
    }

    function setupAnalyzeButtonClick() {
        analyzeButton.addEventListener("click", (event) => {
          event.preventDefault(); // Prevent default form submission
          analyzeFileInput.click(); // Directly trigger file input
        });

        analyzeFileInput.addEventListener('change', async () => {
            if (analyzeFileInput.files.length > 0) {
                const formData = new FormData();
                formData.append('analyze_image_upload', analyzeFileInput.files[0]);

                const reader = new FileReader();
                reader.readAsDataURL(analyzeFileInput.files[0]);

                reader.onload = () => {
                    imageDisplayContainer.innerHTML = `<div class="mt-3"><img src="${reader.result}" alt="Uploaded Image"/></div>`;
                };

                await new Promise(resolve => reader.onloadend = resolve);
                analyzeImage(formData);
            }
        });
    }

    async function analyzeImage(formData) {
        document.getElementById('loading-indicator1').style.display = 'block';
        document.getElementById('loading-circle1').style.display = 'block';
        document.getElementById('error-message').style.display = 'none';

        try {
            const response = await fetch('/drawing-analyze', { method: 'POST', body: formData });
            const data = await response.json();

            document.getElementById('loading-indicator1').style.display = 'none';
            document.getElementById('loading-circle1').style.display = 'none';

            if (response.ok) {
                const analysisResult = data.description.choices[0].message.content || data;
                const analysisContainer = document.getElementById('analysis-result');
                analysisContainer.innerHTML = `<hr class="crimson mb-3"><textarea class="textarea-memory">Analysis Result: ${analysisResult}</textarea>`;

                if (data.audio_url) {
                    const audioPlayerContainer = document.getElementById('audio-player-container');
                    const audioPlayer = document.getElementById('audio-player');
                    audioPlayer.src = data.audio_url;
                    audioPlayerContainer.style.display = 'block';

                    // Auto-play the audio
                    audioPlayer.play().catch(error => {
                        console.error('Auto-play failed:', error);
                    });
                }
            } else {
                throw new Error(data.error || 'An error occurred.');
            }
        } catch (error) {
            handleError(error);
        }
    }

    function handleError(error) {
        console.error('Error:', error);
        document.getElementById('loading-indicator1').style.display = 'none';
        document.getElementById('loading-indicator2').style.display = 'none';
        document.getElementById('loading-circle1').style.display = 'none';
        document.getElementById('loading-circle2').style.display = 'none';
        document.getElementById('error-message').textContent = error.message;
        document.getElementById('error-message').style.display = 'block';
    }
});
